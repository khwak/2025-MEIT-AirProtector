import paho.mqtt.client as mqtt
import json
import pandas as pd
from influxdb_client import InfluxDBClient, Point, WritePrecision
from .cycle_timer import add_cycle_elapsed_time
import pytz
import sys

# ---- MQTT 설정 ----
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "actuators/control"

# ---- InfluxDB 설정 ----
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "eoHq8OwyRkcNPgQXCi4N2zKZEXhRLfebFENNe9XmOn4NQ1N6SU8J54IcRCShpwURxUWhJ0JgR832s_MAsM4n-Q=="
INFLUX_ORG = "meit"
INFLUX_BUCKET = "meit"


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

def on_message_with_db(client_mqtt, userdata, msg, write_api, bucket, org):
    print(f"[MQTT] Message received: {msg.payload.decode()}")
    global df
    try:
        payload = json.loads(msg.payload.decode())
        ts = pd.Timestamp.now(tz=pytz.timezone("Asia/Seoul"))
        payload["timestamp"] = ts

        row = {col: payload.get(col, None) for col in columns}
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df = add_cycle_elapsed_time(df)

        point = Point("control").time(ts, WritePrecision.NS)

        is_valid_point = False
        for f in columns[1:]:
            val = row[f]
            if val is not None:
                try: 
                    # 문자열 데이터를 float으로 변환하여 필드에 추가
                    point = point.field(f, float(val))
                    is_valid_point = True
                except: 
                    print(f"Warning: Field {f} could not be converted to float.")

        # InfluxDB에 쓰기
        if write_api and is_valid_point:
            write_api.write(bucket=bucket, org=org, record=point)
            print(f"InfluxDB 쓰기 성공: {ts}")
        elif not write_api:
            print("Write API가 초기화되지 않았습니다. DB에 데이터를 쓸 수 없습니다.")
        
    except Exception as e:
        print(f"Error processing message or writing to DB: {e}", file=sys.stderr)

def start_subscriber(write_api=None, bucket=None, org=None):
    """
    MQTT 클라이언트 연결을 시작합니다. 
    write_api가 None일 경우, 단독 실행 모드로 간주하고 InfluxDB를 초기화합니다.
    """
    if write_api is None:
        print("단독 실행 모드: InfluxDB 클라이언트를 자체 초기화합니다.")
        try:
            client_db = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
            # 단독 실행 시에는 Write API를 SYNCHRONOUS로 설정하여 데이터 손실을 방지합니다.
            write_api = client_db.write_api()
            bucket = INFLUX_BUCKET
            org = INFLUX_ORG
        except Exception as e:
            print(f"단독 실행 모드 InfluxDB 클라이언트 초기화 오류: {e}")
            return
            
    client_mqtt = mqtt.Client(client_id="", protocol=mqtt.MQTTv311, transport="tcp")
    client_mqtt.on_connect = on_connect
    
    # write_api, bucket, org를 인수로 on_message_with_db에 전달
    client_mqtt.on_message = lambda c, u, m: on_message_with_db(c, u, m, write_api, bucket, org)
    
    print(f"write_api initialized: {write_api is not None}")

    try:
        client_mqtt.connect(MQTT_BROKER, MQTT_PORT, 60)
        client_mqtt.loop_forever()
    except Exception as e:
        print(f"MQTT connection error: {e}")
    finally:
        print("MQTT subscriber stopped.")

if __name__ == "__main__":
    start_subscriber()
