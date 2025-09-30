import paho.mqtt.client as mqtt
import json
import pandas as pd
from influxdb_client import InfluxDBClient, Point, WritePrecision
from .cycle_timer import add_cycle_elapsed_time

# ---- MQTT 설정 ----
MQTT_BROKER = "192.168.137.1"
MQTT_PORT = 1883
MQTT_TOPIC = "actuarators/control"

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
        # timestamp가 없으면 현재 시각 추가
        ts = pd.to_datetime(payload.get("timestamp", pd.Timestamp.now()))
        payload["timestamp"] = ts

        # DataFrame에 추가
        row = {col: payload.get(col, None) for col in columns}
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df = add_cycle_elapsed_time(df)

        # InfluxDB Point 생성
        point = Point("control").time(ts, WritePrecision.NS)
        for f in columns[1:]:  # timestamp는 _time으로 들어가므로 제외
            if row[f] is not None:
                point.field(f, float(row[f]))

        # InfluxDB에 저장
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

        print(f"Saved to InfluxDB: {row}")
    except Exception as e:
        print(f"Error processing message: {e}")

def start_subscriber():
    client_mqtt = mqtt.Client()
    client_mqtt.on_connect = on_connect
    client_mqtt.on_message = on_message

    client_mqtt.connect(MQTT_BROKER, MQTT_PORT, 60)
    client_mqtt.loop_forever()

if __name__ == "__main__":
    start_subscriber()
