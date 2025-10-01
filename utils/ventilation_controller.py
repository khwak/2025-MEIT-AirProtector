import time
from .mqtt_publish import MqttPublisher
from .fetch_data import fetch_data  # 데이터 조회 함수 임포트
from models.threshold import ThresholdChecker

# --- InfluxDB 쓰기 설정 ---
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import os

INFLUX_URL = "http://localhost:8086" 
INFLUX_TOKEN = "eoHq8OwyRkcNPgQXCi4N2zKZEXhRLfebFENNe9XmOn4NQ1N6SU8J54IcRCShpwURxUWhJ0JgR832s_MAsM4n-Q=="
INFLUX_ORG = "meit" 
INFLUX_BUCKET = "meit" 

# InfluxDB 쓰기 클라이언트 초기화
try:
    write_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = write_client.write_api(write_options=SYNCHRONOUS)
    print("InfluxDB Write Client initialized successfully.")
except Exception as e:
    print(f"Error initializing InfluxDB client: {e}. Writing will be skipped.")
    write_api = None


# ---- 설정 ----
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "actuators/control"
PROCESS_INTERVAL_SECONDS = 300  # 5분

# ---- 초기화 ----
checker = ThresholdChecker()
publisher = MqttPublisher(broker=MQTT_BROKER, port=MQTT_PORT, topic=MQTT_TOPIC)

_current_status = {
    "window": 0,  # 창문 열림 정도
    "fan_speed": 0    # 환기팬 속도 
}

def fetch_latest_data(required_fields):
    """
    InfluxDB에서 최근 30분 데이터를 가져와서
    ThresholdChecker에 필요한 필드만 추출 (최근 값 기준)
    """
    df = fetch_data()  # fetch_data.py의 fetch_data() 호출
    if df.empty:
        return None

    # 가장 최신 row 가져오기
    latest_row = df.sort_values("timestamp").iloc[-1]
    
    # 필요한 필드만 추출
    # Benzene 데이터는 required_fields에 없지만, ThresholdChecker가 사용한다면 추가 필요
    all_fields = required_fields + ["Benzene"] 
    processed_data = {field: latest_row[field] for field in all_fields if field in latest_row}
    return processed_data

def get_current_status():
    """
    현재 창문/팬 상태를 반환
    Flask에서 /api/ventilation/controll 호출 시 사용
    여기서는 예시로 고정값을 반환.
    """
    global _current_status
    return _current_status


def main():
    """메인 실행 루프"""
    print("실내 환경 데이터 모니터링 및 자동 제어를 시작합니다.")

    global _current_status  # 상태 업데이트 가능하게 설정
    level_map = {"normal": 0, "warning": 1, "serious": 2}
    required_fields = ["CO2", "CO", "HCHO", "TVOC"] 

    while True:
        try:
            # 1. 데이터 조회 모듈을 통해 최신 데이터 가져오기
            print("\n--- 최신 데이터 조회 시작 ---")
            processed_data = fetch_latest_data(required_fields)
            
            if processed_data:
                print(f"조회된 데이터: {processed_data}")

                # 2. 임계값 검사
                results = checker.check(processed_data)
                print(f"임계값 분석 결과: {results}")

                # 3. Grafana Alert용 데이터 InfluxDB에 저장
                if write_api and results:
                    points_to_write = []
                    # 모든 센서의 경고 레벨을 저장
                    for field, data in results.items():
                        if field in ["CO2", "CO", "HCHO", "TVOC"]: # 검사 대상 필드만
                            level_code = level_map.get(data['level'], 0)
                            
                            point = (
                                Point("alert_status") # 경고 상태를 저장할 새로운 measurement
                                .tag("sensor", field) # CO2, CO 등을 태그로 지정
                                .field("level_code", level_code) # 경고 레벨을 숫자로 저장 (0, 1, 2)
                                .field("sensor_value", data['value']) # 실제 센서 값을 필드로 저장
                            )
                            points_to_write.append(point)

                    if points_to_write:
                        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=points_to_write)
                        print(f"--> 임계값 분석 결과 ({len(points_to_write)}개)를 InfluxDB 'alert_status'에 저장 완료.")

                
        except Exception as e:
            print(f"오류가 발생했습니다: {e}")
            
        finally:
            print(f"--- {PROCESS_INTERVAL_SECONDS}초 후 다음 작업을 시작합니다. ---")
            time.sleep(PROCESS_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()