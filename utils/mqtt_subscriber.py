from influxdb_client import InfluxDBClient
import pandas as pd

# ---- InfluxDB 설정 ----
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "eoHq8OwyRkcNPgQXCi4N2zKZEXhRLfebFENNe9XmOn4NQ1N6SU8J54IcRCShpwURxUWhJ0JgR832s_MAsM4n-Q=="
INFLUX_ORG = "meit"
INFLUX_BUCKET = "meit"

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
query_api = client.query_api()

# ---- 필요한 필드들 ----
fields = [
    "indoor_temp", "outdoor_temp",
    "indoor_hum", "outdoor_hum",
    "wind_speed", "window_open", "fan_speed",
    "CO2", "CO", "HCHO", "TVOC",
]

def fetch_data():
    # ---- Flux 쿼리 만들기 ----
    field_filter = " or ".join([f'r["_field"] == "{f}"' for f in fields])
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
    |> range(start: -30m)  // 최근 30분
    |> filter(fn: (r) => r["_measurement"] == "environment")
    |> filter(fn: (r) => {field_filter})
    |> pivot(rowKey:["_time"], columnKey:["_field"], valueColumn:"_value")
    |> keep(columns: ["_time", {",".join([f'"{f}"' for f in fields])}])
    '''

    # ---- 쿼리 실행 ----
    df = query_api.query_data_frame(query)
    df = df.rename(columns={"_time": "timestamp"})  # timestamp 컬럼 이름 맞춤

    return df

# ---- 테스트 ----
if __name__ == "__main__":
    df = fetch_data()
    print(df.head())