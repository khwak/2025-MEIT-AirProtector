from flask import Flask, request, jsonify
from influxdb_client import InfluxDBClient
from models.preprocessing import preprocess_sensor_data
from models.threshold import ThresholdChecker

app = Flask(__name__)

# ---- InfluxDB 연결 설정 ----
INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "eoHq8OwyRkcNPgQXCi4N2zKZEXhRLfebFENNe9XmOn4NQ1N6SU8J54IcRCShpwURxUWhJ0JgR832s_MAsM4n-Q=="
INFLUX_ORG = "meit"
INFLUX_BUCKET = "meit"

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
query_api = client.query_api()

# ---- 최근 센서 데이터 조회 + 전처리 + 이상 판단 ----
@app.route("/api/sensor/latest", methods=["GET"])
def get_latest_sensor():
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
