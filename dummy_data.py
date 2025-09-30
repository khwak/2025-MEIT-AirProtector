from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import datetime
import random

# ---- InfluxDB 설정 ----
INFLUX_URL = "http://localhost:8086"
# INFLUX_TOKEN = "eoHq8OwyRkcNPgQXCi4N2zKZEXhRLfebFENNe9XmOn4NQ1N6SU8J54IcRCShpwURxUWhJ0JgR832s_MAsM4n-Q=="
INFLUX_TOKEN = "1mjcn8eY-FHd6MIQB2CnxiItKPL2IOzirhwxwxZRTiC8ZlaRglHJ-okXUav072S6j6IfGZ3YIE1BvSeapYnkvg=="
INFLUX_ORG = "meit"
INFLUX_BUCKET = "meit"

try:
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    # SYNCHRONOUS: 데이터가 즉시 기록되도록 보장하는 옵션입니다.
    write_api = client.write_api(write_options=SYNCHRONOUS)

    # ---- 최근 30분, 1분 간격 데이터 생성 ----
    now = datetime.datetime.utcnow()
    data_points = []
    
    # 30분치 데이터를 생성하도록 range(30)으로 수정
    for i in range(30):
        # 30분 전부터 현재까지 1분 간격의 타임스탬프를 생성합니다.
        timestamp = now - datetime.timedelta(minutes=29 - i)
        
        # Point 객체를 한 번에 정의하여 필드 값을 모두 추가합니다.
        point = (
            Point("environment")
            .field("indoor_temp", 24 + random.uniform(-0.5, 0.5))
            .field("outdoor_temp", 20 + random.uniform(-1, 1))
            .field("indoor_hum", 50 + random.uniform(-2, 2))
            .field("outdoor_hum", 55 + random.uniform(-2, 2))
            .field("wind_speed", 1 + random.uniform(0, 0.5))
            .field("window_open", random.choice([0, 0, 1]))
            .field("fan_speed", random.choice([0, 1]))
            .field("CO2", 900 + random.uniform(50, 150))
            .field("CO", 4 + random.uniform(0, 1))
            .field("HCHO", 0.05 + random.uniform(0, 0.05))
            .field("TVOC", 700 + random.uniform(50, 150))
            .time(timestamp, WritePrecision.NS)
        )
        data_points.append(point)

    write_api.write(bucket=INFLUX_BUCKET, record=data_points)
    print(f"최근 30분치({len(data_points)}개) 더미 데이터가 InfluxDB에 입력되었습니다.")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # 스크립트가 끝나면 항상 클라이언트 연결을 닫아줍니다.
    if 'client' in locals():
        client.close()
        print("InfluxDB client closed.")