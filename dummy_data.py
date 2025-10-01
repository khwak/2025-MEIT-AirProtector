import paho.mqtt.client as mqtt
import json
from datetime import datetime
import time
import random

broker = "localhost"
port = 1883
topic = "actuators/control"

client = mqtt.Client()
client.connect(broker, port, 60)

try:
    while True:
        # 1초마다 전송
        payload = {
            "timestamp": datetime.now().isoformat(),
            "window_open": random.choice([0, 1, 2]),  # ESP처럼 랜덤 테스트
            "fan_speed": random.choice([0, 1, 2]),    # 랜덤 테스트
            "indoor_temp": round(random.uniform(20, 26), 1),
            "outdoor_temp": round(random.uniform(15, 22), 1),
            "indoor_hum": round(random.uniform(40, 60), 1),
            "outdoor_hum": round(random.uniform(30, 55), 1),
            "wind_speed": round(random.uniform(0, 5), 1),
            "CO2": random.randint(400, 800),
            "CO": random.randint(0, 10),
            "HCHO": round(random.uniform(0, 0.1), 3),
            "TVOC": round(random.uniform(0, 1), 2)
        }

        client.publish(topic, json.dumps(payload))
        print(f"[MQTT] Message sent: {payload}")
        time.sleep(1)

except KeyboardInterrupt:
    print("Stopped by user")
    client.disconnect()
