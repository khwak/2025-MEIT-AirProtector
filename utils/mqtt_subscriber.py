import paho.mqtt.client as mqtt
import json
import pandas as pd
from .cycle_timer import add_cycle_elapsed_time

MQTT_BROKER = "localhost"  # HW에서 publish하는 MQTT 브로커 주소
MQTT_PORT = 1883
MQTT_TOPIC = "environment/data"  # HW에서 publish하는 topic

# 수신된 데이터를 임시 저장할 DataFrame
columns = [
    "timestamp", "indoor_temp", "outdoor_temp",
    "indoor_hum", "outdoor_hum",
    "wind_speed", "window_open", "fan_speed",
    "CO2", "CO", "HCHO", "TVOC"
]
df = pd.DataFrame(columns=columns)

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    global df
    try:
        payload = json.loads(msg.payload.decode())
        # timestamp가 없으면 현재 시각 추가
        if "timestamp" not in payload:
            payload["timestamp"] = pd.Timestamp.now()
        row = {col: payload.get(col, None) for col in columns}
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

        # 숫자형 변환
        for f in columns[1:]:
            df[f] = pd.to_numeric(df[f], errors="coerce")
        
        # cycle_elapsed_time 계산
        df = add_cycle_elapsed_time(df)
        print(f"Received data: {row}")
    except Exception as e:
        print(f"Error processing message: {e}")

def start_subscriber():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()  # blocking loop

# 테스트
if __name__ == "__main__":
    start_subscriber()
