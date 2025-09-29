import time
from mqtt_publish import MqttPublisher
from mqtt_subscriber import fetch_data  # 데이터 조회 함수 임포트
from models.threshold import ThresholdChecker

# ---- 설정 ----
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "actuators/control"
PROCESS_INTERVAL_SECONDS = 300  # 5분

# ---- 초기화 ----
checker = ThresholdChecker()
publisher = MqttPublisher(broker=MQTT_BROKER, port=MQTT_PORT, topic=MQTT_TOPIC)

_current_status = {
    "window": 0,   # 창문 열림 정도
    "fan_speed": 0    # 환기팬 속도 
}

def fetch_latest_data(required_fields):
    """
    InfluxDB에서 최근 30분 데이터를 가져와서
    ThresholdChecker에 필요한 필드만 추출 (최근 값 기준)
    """
    df = fetch_data()  # mqtt_subscriber.py의 fetch_data() 호출
    if df.empty:
        return None

    # 가장 최신 row 가져오기
    latest_row = df.sort_values("timestamp").iloc[-1]
    
    # 필요한 필드만 추출
    processed_data = {field: latest_row[field] for field in required_fields if field in latest_row}
    return processed_data

def get_current_status():
    """
    현재 창문/팬 상태를 반환
    Flask에서 /api/ventilation/controll 호출 시 사용
    """
    return _current_status

def main():
    """메인 실행 루프"""
    print("실내 환경 데이터 모니터링 및 자동 제어를 시작합니다.")

    global _current_status  # 상태 업데이트 가능하게 설정
    while True:
        try:
            # 1. 데이터 조회 모듈을 통해 최신 데이터 가져오기
            print("\n--- 최신 데이터 조회 시작 ---")
            # ThresholdChecker에 필요한 필드 목록
            required_fields = ["CO2", "CO", "HCHO", "TVOC"] 
            processed_data = fetch_latest_data(required_fields)
            
            if processed_data:
                print(f"조회된 데이터: {processed_data}")

                # 2. 임계값 검사
                results = checker.check(processed_data)
                print(f"임계값 분석 결과: {results}")

                if results:
                    # 전체 상태
                    _current_status["window"] = int(results.get("window_open", 0))
                    _current_status["fan_speed"] = int(results.get("fan_speed", 0))

                # 3. MQTT로 제어 결과 발행
                publisher.publish_results(data=results)

        except Exception as e:
            print(f"오류가 발생했습니다: {e}")
            
        finally:
            print(f"--- {PROCESS_INTERVAL_SECONDS}초 후 다음 작업을 시작합니다. ---")
            time.sleep(PROCESS_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()