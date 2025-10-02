from influxdb_client import InfluxDBClient
import pandas as pd
from .cycle_timer import add_cycle_elapsed_time

# ---- InfluxDB 설정 ----
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "eoHq8OwyRkcNPgQXCi4N2zKZEXhRLfebFENNe9XmOn4NQ1N6SU8J54IcRCShpwURxUWhJ0JgR832s_MAsM4n-Q=="
INFLUX_ORG = "meit"
INFLUX_BUCKET = "meit"

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
query_api = client.query_api()

# 필요한 필드들 
fields = [
    "indoor_temp", "outdoor_temp",
    "indoor_hum", "outdoor_hum",
    "wind_speed", "window_open", "fan_speed",
    "CO2", "CO", "HCHO", "TVOC",
]

def fetch_data():
    # Flux 쿼리 만들기 
    field_filter = " or ".join([f'r["_field"] == "{f}"' for f in fields])
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
    |> range(start: -1h)  // 최근 1시간(-1h)
    |> filter(fn: (r) => r["_measurement"] == "control")
    |> filter(fn: (r) => {field_filter})
    |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value")
    |> keep(columns: ["_time", {",".join([f'"{f}"' for f in fields])}])
    '''

    # 쿼리 실행 
    df = query_api.query_data_frame(query)
    if isinstance(df, list):  # 여러 table 반환된 경우
        df = pd.concat(df)

    if not df.empty:
        # _time → timestamp rename
        df = df.rename(columns={"_time": "timestamp"})

        # 메타 정보 제거 (_time은 이미 timestamp로 rename 했으므로 안전)
        drop_cols = [c for c in df.columns if c.startswith("_") or c in ["result", "table"]]
        df = df.drop(columns=drop_cols, errors="ignore")

        # 누락 데이터 처리
        missing_fields = [f for f in fields if f not in df.columns]
        for f in missing_fields:
            # 누락된 열을 0.0으로 채워 추가
            df[f] = 0.0 

        # 정렬
        df = df.sort_values("timestamp").reset_index(drop=True)

        # 숫자형 변환
        for f in fields:
            df[f] = pd.to_numeric(df[f], errors="coerce")
    
    # cycle_elapsed_time 추가
    df = add_cycle_elapsed_time(df)

    return df

# 테스트
if __name__ == "__main__":
    df = fetch_data()
    print(df.head())