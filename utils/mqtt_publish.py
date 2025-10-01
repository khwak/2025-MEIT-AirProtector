import json
import paho.mqtt.client as mqtt

class MqttPublisher:
    def __init__(self, broker="172.20.96.32", port=1883, topic="fan/control"):
        self.broker = broker
        self.port = port
        self.topic = topic
        self.client = mqtt.Client()
        self.client.connect(self.broker, self.port, 60)

    def publish_results(self, data: dict):
        """
        data: ThresholdChecker.check() 결과
        """
        # 최악의 상태 기준으로 종합 판단
        priority = {"normal": 0, "warning": 1, "serious": 2}
        overall_level = "normal"
        for v in data.values():
            if priority[v["level"]] > priority[overall_level]:
                overall_level = v["level"]

        # 창문/팬 신호 매핑
        level_map = {
            "normal": {"window_open": 0, "fan_speed": 0},
            "warning": {"window_open": 1, "fan_speed": 1},
            "serious": {"window_open": 2, "fan_speed": 2},
        }

        payload = {
            "status": overall_level,
            "window_open": level_map[overall_level]["window_open"],
            "fan_speed": level_map[overall_level]["fan_speed"],
            "details": data  # 항목별 상세 결과 포함
        }

        self.client.publish(self.topic, json.dumps(payload))
        print(f"[MQTT PUBLISH] Sent to {self.topic}: {payload}")
