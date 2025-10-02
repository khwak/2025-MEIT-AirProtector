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
MQTT_BROKER = "192.168.137.1"
MQTT_PORT = 1883
MQTT_TOPIC = "actuators/control"
PROCESS_INTERVAL_SECONDS = 300  # 5분

# ---- 초기화 ----
checker = ThresholdChecker()
publisher = MqttPublisher(broker=MQTT_BROKER, port=MQTT_PORT, topic="fan/control")

_current_status = {
    "window": 0,  # 창문 열림 정도
    "fan_speed": 0    # 환기팬 속도 
}

# _current_status 갱신
def update_current_status_from_db():
    """
    InfluxDB에서 최신 창문/팬 상태를 가져와 _current_status를 갱신
    """
    global _current_status

    try:
        df = fetch_data()  # fetch_data()는 InfluxDB에서 최근 데이터 가져오는 함수
        if df.empty:
            print("DB에 데이터 없음. _current_status 유지")
            return

        latest_row = df.sort_values("timestamp").iloc[-1]

        # DB 컬럼명에 맞춰 상태 가져오기
        _current_status['window'] = int(latest_row.get('window_open', 0))
        _current_status['fan_speed'] = int(latest_row.get('fan_speed', 0))

        print(f"_current_status 갱신: {_current_status}")

    except Exception as e:
        print(f"_current_status 갱신 실패: {e}")



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
    update_current_status_from_db()  # 호출 시마다 최신 상태로 갱신
    return _current_status


# --- 경고 상태를 InfluxDB에 쓰는 핵심 함수 ---
def write_alert_status(max_level_code: int, max_level_sensor: str):
    """
    모든 센서 중 가장 높은 경고 레벨을 'alert_status' 측정값에 기록합니다.
    """
    if not write_api:
        print("ERROR: InfluxDB Write API가 초기화되지 않아 데이터 기록을 건너뜁니다.")
        return

    # Grafana 알림 쿼리가 사용하는 measurement와 field에 맞게 Point를 생성
    point = Point("alert_status") \
        .tag("host", "air_monitor_server") \
        .tag("sensor", max_level_sensor) \
        .field("level_code", max_level_code) \
        .time(time.time_ns(), WritePrecision.NS)

    try:
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        print(f"INFO: 'alert_status' 기록 완료. (Level: {max_level_code}, Source: {max_level_sensor})")
    except Exception as e:
        print(f"ERROR: InfluxDB 쓰기 오류 발생: {e}")
        

def run_once():
    """한 사이클만 실행되는 모니터링/제어 함수"""
    print("실내 환경 데이터 모니터링 및 자동 제어 실행 (1회)")

    global _current_status
    level_map = {"normal": 0, "warning": 1, "serious": 2}
    required_fields = ["CO2", "CO", "HCHO", "TVOC"]

    try:
        # 1. 데이터 조회
        processed_data = fetch_latest_data(required_fields)
        if not processed_data:
            print("WARNING: 조회된 최신 데이터가 없습니다.")
            return

        print(f"조회된 데이터: {processed_data}")

        # 2. 임계값 검사
        results = checker.check(processed_data)
        print(f"임계값 분석 결과: {results}")

        # 3. 최대 경고 레벨 결정
        max_level_code = 0
        max_level_sensor = "Normal"
        for field, data in results.items():
            current_level_code = level_map.get(data['level'], 0)
            if current_level_code > max_level_code:
                max_level_code = current_level_code
                max_level_sensor = field

        # 4. InfluxDB에 경고 상태 기록
        write_alert_status(max_level_code, max_level_sensor)
        print(f"InfluxDB에 기록됨: Level {max_level_code} ({max_level_sensor})")

        # 5. 자동 제어 로직 (생략 가능)

    except Exception as e:
        print(f"1회 실행 중 오류 발생: {e}")
