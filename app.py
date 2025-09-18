#Flask 앱 기본 설정.
from flask import Flask, request, jsonify, render_template
from influxdb_client import InfluxDBClient
from models.preprocessing import preprocess_sensor_data
from models.threshold import ThresholdChecker

#Flask : Python 웹 프레임워크. 웹 API를 쉽게 만들 수 있음.
#request : 클라이언트에서 들어오는 요청 파라미터를 읽는 기능.
#jsonify : Python dict → JSON 응답으로 변환.
#render_template : html파일을 불러오는 함수.
#InfluxDBClient : 시계열 데이터베이스인 InfluxDB에 연결하기 위한 라이브러리.
#preprocess_sensor_data : 데이터 전처리 함수 (스케일링, 보정 등).
#ThresholdChecker : 센서 데이터의 정상/경고/심각 여부를 판단하는 클래스.

app = Flask(__name__) #Flask 앱 객체를 생성.

# ---- InfluxDB 연결 설정 ---- (influxDB는 url, 인증토큰, 조직면, 버킷 정보가 필요함.)
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "eoHq8OwyRkcNPgQXCi4N2zKZEXhRLfebFENNe9XmOn4NQ1N6SU8J54IcRCShpwURxUWhJ0JgR832s_MAsM4n-Q=="
INFLUX_ORG = "meit"
INFLUX_BUCKET = "meit"

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
query_api = client.query_api() #flux 쿼리를 실행하는 인터페이스.

# ---- 최근 센서 데이터 조회 + 전처리 + 이상 판단 ----
@app.route("/api/sensor/latest", methods=["GET"])

def get_latest_sensor(): #/api/sensor/latest 경로에 get요청을 보내면 이 함수 실행됨.
    """
    Query Parameters:
        - sensor_id (optional): 특정 센서만 조회
    """
    sensor_id = request.args.get("sensor_id")
    filter_tag = f'|> filter(fn: (r) => r.device == "{sensor_id}")' if sensor_id else ""
    
    # InfluxDB Flux 쿼리
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -1h)
      |> filter(fn: (r) => r._measurement == "environment")
      {filter_tag}
      |> last()
    '''
    tables = query_api.query(query, org=INFLUX_ORG)

    # raw 데이터 구성: device -> sensor_type -> {value, time}
    raw_results = {}
    for table in tables:
        for record in table.records:
            device = record.values.get("device")
            field = record.values.get("sensor_type")
            if device not in raw_results:
                raw_results[device] = {}
            raw_results[device][field] = {
                "value": record.get_value(),
                "time": str(record.get_time())
            }

    # ---- 전처리 + Threshold 판단 ----
    response = {}
    checker = ThresholdChecker()

    for device, data in raw_results.items():
        processed = preprocess_sensor_data(data)  # 스케일링/정규화 등 전처리
        analysis = checker.check(processed)       # 표 기반 경고/심각 판단
        response[device] = {
            "raw": data,
            "processed": processed,
            "analysis": analysis
        }

    return jsonify(response)


if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)







@app.route("/")
def user_page():
    return render_template("user.html")

@app.route("/admin")
def admin_page():
    return render_template("admin.html")

if __name__ == "__main__":
    app.run(debug=True)