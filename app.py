#Flask 앱 기본 설정.
from flask import Flask, request, jsonify, render_template
from utils.fetch_data import fetch_data
from models.preprocessing import preprocess_sensor_data
from models.ventilation_predictor import predict_remaining_minutes
from models.anomaly_detector import detect_anomaly
from utils.ventilation_controller import get_current_status

# InfluxDB 클라이언트 관련 임포트 추가
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
import time

# ---- InfluxDB 설정 ----
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "eoHq8OwyRkcNPgQXCi4N2zKZEXhRLfebFENNe9XmOn4NQ1N6SU8J54IcRCShpwURxUWhJ0JgR832s_MAsM4n-Q=="
INFLUX_ORG = "meit"
INFLUX_BUCKET = "meit"

#Flask : Python 웹 프레임워크. 웹 API를 쉽게 만들 수 있음.
#request : 클라이언트에서 들어오는 요청 파라미터를 읽는 기능.
#jsonify : Python dict → JSON 응답으로 변환.
#render_template : html파일을 불러오는 함수.
#InfluxDBClient : 시계열 데이터베이스인 InfluxDB에 연결하기 위한 라이브러리.
#preprocess_sensor_data : 데이터 전처리 함수 (스케일링, 보정 등).
#ThresholdChecker : 센서 데이터의 정상/경고/심각 여부를 판단하는 클래스.

app = Flask(__name__) #Flask 앱 객체를 생성.

# InfluxDB 클라이언트 초기화
try:
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    query_api = client.query_api()
    print("InfluxDB 클라이언트 초기화 완료.")
except Exception as e:
    print(f"InfluxDB 클라이언트 초기화 오류: {e}")
    client = None
    query_api = None

# 창문/환기팬 상태 (자동/수동)
@app.route("/api/ventilation/status", methods=["GET"])
def ventilation_controll():
    """
    {
        "window": int,       # 창문 열림 정도 
        "fan_speed": int     # 환기팬 속도 
    }
    """
    # TODO: 여기에서 실제 센서/DB에서 현재 상태를 가져오는 로직을 사용해야 합니다.
    status = get_current_status() 
    
    return jsonify(status)

# 창문/환기팬 상태 (수동)
# mqtt로 센서한테 window 또는 fan_speed 전달
@app.route("/api/ventilation/manual", methods=["POST"])
def ventilation_manual_controll():
    data = request.get_json()
    control_type = data.get("control_type")  # "window" 또는 "fan"
    level = data.get("level")                # 0, 1, 2 (0%, 50%, 100%)
    
    if control_type not in ["window", "fan"] or level not in [0, 1, 2]:
        return jsonify({"error": "Invalid control type or level"}), 400

    # TODO: 여기에 실제 MQTT/장치 제어 로직을 구현
    print(f"Manual control request: {control_type} set to level {level}")
    
    return jsonify({"success": True, "control_type": control_type, "level": level})



# 환기 시간 예측
@app.route("/api/ventilation/predict", methods=["GET"])
def ventilation_predict():
    """
    {
        0: {"vent_flag": int, "remaining_minutes": int},
        1: {"vent_flag": int, "remaining_minutes": int},
        ...
    }
    - vent_flag: 환기 필요 여부 (0: 불필요, 1: 필요)
    - remaining_minutes: 환기 완료까지 예상 남은 시간 (분 단위)
    """
    raw_data = fetch_data()
    if raw_data.empty:
        return jsonify({"error": "No data available"}), 400
    latest_row = raw_data.sort_values("timestamp").iloc[-1:] 
    predictions = predict_remaining_minutes(latest_row)

    return jsonify(predictions)


# 센서 이상/고장 감지
@app.route("/api/anomaly/results", methods=["GET"])
def anomaly_results():
    """
    {
        "2025-09-29 12:00:00": {"loss_mae": 0.32, "threshold": 0.275, "anomaly": true},
        "2025-09-29 12:01:00": {"loss_mae": 0.12, "threshold": 0.275, "anomaly": false},
        ...
    }
    - loss_mae: 재구성 오차(MAE)
    - threshold: 이상 판단 기준
    - anomaly: True -> 이상 발생, False -> 정상
    """
    raw_data = fetch_data()
    if raw_data.empty:
        return jsonify({"error": "No data available"}), 400
    processed = preprocess_sensor_data(raw_data)
    anomalies = detect_anomaly(processed)

    return jsonify(anomalies)


# 경고 상태 확인 (신규 엔드포인트)
@app.route('/api/alert/status', methods=['GET'])
def get_alert_status():
    """
    Grafana Alert Rule에 사용된 Flux 쿼리를 실행하여 현재 경고 레벨을 반환합니다.
    Alert Condition: WHEN Last OF QUERY IS ABOVE 1
    """
    if not query_api:
        return jsonify({"level_code": 0, "message": "API 서버 오류: InfluxDB 연결 실패"}), 500
    
    # Grafana Alert Rule 쿼리 (최근 5분 데이터의 Max level_code)
    flux_query = f'''
    from(bucket: "{INFLUX_BUCKET}")
        |> range(start: -5m) 
        |> filter(fn: (r) => r._measurement == "alert_status")
        |> filter(fn: (r) => r._field == "level_code")
        |> aggregateWindow(every: 5m, fn: max, createEmpty: false)
        |> max()
        |> yield(name: "MaxLevel")
    '''

    try:
        tables = query_api.query(query=flux_query, org=INFLUX_ORG)
        
        max_level_code = 0
        if tables and tables[0].records:
            # 결과 테이블에서 MaxLevel 값을 추출
            record = tables[0].records[0]
            max_level_code = int(record['_value'])
        
        # level_code에 따른 메시지 결정
        # Alert Rule 조건이 'IS ABOVE 1'이므로, level_code > 1 일 때 심각으로 처리합니다.
        if max_level_code > 1:
            message = f"Critical Alert: 심각 단계 경고 발생 (Level {max_level_code})."
            level_code = 2 # 심각
        elif max_level_code == 1:
            message = f"Warning Alert: 실내 환경 기준 초과 경고 (Level {max_level_code})."
            level_code = 1 # 경고
        else:
            message = "Normal: 실내 환경 정상입니다."
            level_code = 0 # 정상
            
        return jsonify({"level_code": level_code, "message": message})
        
    except Exception as e:
        print(f"InfluxDB 쿼리 실행 오류: {e}")
        # 쿼리 오류 발생 시 임시로 정상 상태(0) 반환
        return jsonify({"level_code": 0, "message": "쿼리 실행 중 오류 발생"}), 500



# UI 페이지
@app.route("/")
def user_page():
    return render_template("user.html")

@app.route("/admin")
def admin_page():
    return render_template("admin.html")

if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)