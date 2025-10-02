import pandas as pd
from influxdb_client import InfluxDBClient, Point, WritePrecision
import pytz

# ------------------------
# 1. CSV 불러오기
# ------------------------
csv_path = "C:/Users/khk02/meit-server/real_data.csv"
df = pd.read_csv(csv_path, parse_dates=["timestamp"])

# ------------------------
# 2. InfluxDB 설정
# ------------------------
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "eoHq8OwyRkcNPgQXCi4N2zKZEXhRLfebFENNe9XmOn4NQ1N6SU8J54IcRCShpwURxUWhJ0JgR832s_MAsM4n-Q=="
INFLUX_ORG = "meit"
INFLUX_BUCKET = "meit"

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client.write_api()

# ------------------------
# 3. CSV → InfluxDB
# ------------------------
columns = [
    "indoor_temp", "outdoor_temp",
    "indoor_hum", "outdoor_hum",
    "wind_speed", "window_open", "fan_speed",
    "CO2", "CO", "HCHO", "TVOC"
]

points = []
for idx, row in df.iterrows():
    try:
        # timestamp를 tz-aware로
        ts = row["timestamp"]
        if ts.tzinfo is None:
            ts = ts.tz_localize('Asia/Seoul')

        point = Point("control").time(ts, WritePrecision.NS)

        # field 추가
        for f in columns:
            val = row[f]
            if pd.notnull(val):
                point = point.field(f, float(val))

        points.append(point)

        # batch로 일정 개수마다 쓰기 (예: 500개씩)
        if len(points) >= 500:
            write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)
            points = []

    except Exception as e:
        print(f"Error writing row {idx}: {e}")

# 남은 포인트 쓰기
if points:
    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points)

client.close()
print("CSV → InfluxDB 업로드 완료!")