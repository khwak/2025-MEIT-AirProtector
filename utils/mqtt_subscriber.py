import paho.mqtt.client as mqtt
import json
import pandas as pd
from influxdb_client import InfluxDBClient, Point, WritePrecision
from .cycle_timer import add_cycle_elapsed_time

# ---- MQTT 설정 ----
MQTT_BROKER = "192.168.137.1"
MQTT_PORT = 1883
MQTT_TOPIC = "actuators/control"

# ---- InfluxDB 설정 ----
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "eoHq8OwyRkcNPgQXCi4N2zKZEXhRLfebFENNe9XmOn4NQ1N6SU8J54IcRCShpwURxUWhJ0JgR832s_MAsM4n-Q=="
INFLUX_ORG = "meit"
INFLUX_BUCKET = "meit"

client_db = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client_db.write_api()

# DataFrame 컬럼
columns = [
    "timestamp", "indoor_temp", "outdoor_temp",
    "indoor_hum", "outdoor_hum",
    "wind_speed", "window_open", "fan_speed",
    "CO2", "CO", "HCHO", "TVOC"
]
df = pd.DataFrame(columns=columns)

def on_connect(client_mqtt, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client_mqtt.subscribe(MQTT_TOPIC)

def on_message(client_mqtt, userdata, msg):
    global df
    try:
        payload = json.loads(msg.payload.decode())
        ts_value = payload.get("timestamp")

        if isinstance(ts_value, (int, float)) and ts_value > 1_000_000_000: 
            # 초 단위로 가정하고 변환
            ts = pd.to_datetime(ts_value, unit='s')
        else:
            # 타임스탬프가 없거나 유효하지 않으면 현재 시각 (UTC 권장) 사용
            ts = pd.Timestamp.now(tz='UTC')

        payload["timestamp"] = ts

        # DataFrame에 추가
        row = {col: payload.get(col, None) for col in columns}
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df = add_cycle_elapsed_time(df)

        # InfluxDB Point 생성
        point = Point("control").time(ts, WritePrecision.NS)
        for f in columns[1:]:  # timestamp는 _time으로 들어가므로 제외
            value = row[f]
            if value is not None:
                try:
                    # InfluxDB는 정수/실수를 구분하므로, 정수형 필드는 int()로 변환 시도
                    if isinstance(value, int) or (isinstance(value, float) and value.is_integer()):
                        point.field(f, int(value))
                    else:
                        point.field(f, float(value))
                except (ValueError, TypeError):
                    # 숫자로 변환할 수 없는 경우 문자열로 기록하거나 건너뛰기
                    # 여기서는 건너뛰도록 처리합니다.
                    pass

        # InfluxDB에 저장
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

        print(f"Saved to InfluxDB: {row}")
    except Exception as e:
        print(f"Error processing message: {e}")

def start_subscriber():
    client_mqtt = mqtt.Client()
    client_mqtt.on_connect = on_connect
    client_mqtt.on_message = on_message

    try:
        client_mqtt.connect(MQTT_BROKER, MQTT_PORT, 60)
        print("MQTT connection established. Starting loop...")
        client_mqtt.loop_forever()
    except KeyboardInterrupt:
        print("Subscriber stopped by user.")
    except Exception as e:
        print(f"An error occurred in the MQTT connection: {e}")
    finally:
        # 스크립트 종료 시 InfluxDB 클라이언트 연결 해제
        print("Closing InfluxDB client.")
        client_db.close()

if __name__ == "__main__":
    start_subscriber()
