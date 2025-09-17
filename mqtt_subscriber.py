import json
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# ---- InfluxDB 설정 ----
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "eoHq8OwyRkcNPgQXCi4N2zKZEXhRLfebFENNe9XmOn4NQ1N6SU8J54IcRCShpwURxUWhJ0JgR832s_MAsM4n-Q=="
INFLUX_ORG = "meit"
INFLUX_BUCKET = "meit"

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

# ---- MQTT 콜백 ----
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # 관심 있는 센서 토픽 구독
    client.subscribe("sensors/#")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        sensor_id = payload.get("sensor_id")
        
        # 각 항목별로 InfluxDB 저장
        for field in ["CO2", "CO", "HCHO", "Benzene", "TVOC"]:
            if field in payload:
                point = (
                    Point("environment")
                    .tag("device", sensor_id)
                    .tag("sensor_type", field)
                    .field("value", payload[field])
                )
                write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
                print(f"Saved {field} from {sensor_id}: {payload[field]}")
    except Exception as e:
        print("Error processing message:", e)

# ---- MQTT 클라이언트 초기화 ----
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# 브로커 접속
mqtt_client.connect("localhost", 1883, 60)

# MQTT 루프 시작 (블로킹)
mqtt_client.loop_forever()
