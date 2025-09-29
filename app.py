#Flask 앱 기본 설정.
from flask import Flask, request, jsonify, render_template
from utils.mqtt_subscriber import fetch_data
from models.preprocessing import preprocess_sensor_data
from models.ventilation_predictor import predict_remaining_minutes
from models.anomaly_detector import detect_anomaly
from utils.ventilation_controller import get_current_status

#Flask : Python 웹 프레임워크. 웹 API를 쉽게 만들 수 있음.
#request : 클라이언트에서 들어오는 요청 파라미터를 읽는 기능.
#jsonify : Python dict → JSON 응답으로 변환.
#render_template : html파일을 불러오는 함수.
#InfluxDBClient : 시계열 데이터베이스인 InfluxDB에 연결하기 위한 라이브러리.
#preprocess_sensor_data : 데이터 전처리 함수 (스케일링, 보정 등).
#ThresholdChecker : 센서 데이터의 정상/경고/심각 여부를 판단하는 클래스.

app = Flask(__name__) #Flask 앱 객체를 생성.

# 창문/환기팬 상태 (자동)
@app.route("/api/ventilation/controll", methods=["GET"])
def ventilation_controll():
    """
    {
        "window": int,       # 창문 열림 정도 
        "fan_speed": int     # 환기팬 속도 
    }
    """
    status = get_current_status() 

    return jsonify(status)

# 창문/환기팬 상태 (수동)
# mqtt로 센서한테 window 또는 fan_speed 전달


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


# UI 페이지
@app.route("/")
def user_page():
    return render_template("user.html")

@app.route("/admin")
def admin_page():
    return render_template("admin.html")

if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)