'''
flask 웹 서버 코드. 
프로젝트의 서버 쪽에서 센서 데이터랑 환기 제어 기능을 
웹 API 형태로 제공하는 구조임.
'''

#Flask 앱 기본 설정. import를 한다. 
from flask import Flask, request, jsonify, render_template
from utils.fetch_data import fetch_data
from models.preprocessing import preprocess_sensor_data
from models.ventilation_predictor import predict_remaining_minutes 
# 환기 완료까지 남은 시간을 예측하는 함수
from utils.ventilation_controller import get_current_status
#현재 창문,환기팬 상태를 읽어오는 함수. 
'''
'''

app = Flask(__name__) 
#Flask 웹 서버의 인스턴스를 하나 만들었다. 그 서버 이름은 app
#__name__: 지금 파일의 모듈이름을 넘겨주는 것 -> 디버그메세지에 모듈 기준 경로를 잘 보여준다. 

# 창문/환기팬 상태 조회 (자동)
'''
decorator. 
:함수를 감싸서 동작을 바꾸거나 등록하는 파이썬 문법
(아래에 오는 함수 하나를 특정url과 매핑해준다.)
ex)'http://127.0.0.1:5000/api/ventilation/controll'로 들어오면
    flask가 ventilatio_controll함수를 실행하고 json응답을 돌려준다. 
'''
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
if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)

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