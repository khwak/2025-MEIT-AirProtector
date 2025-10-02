from influxdb_client import InfluxDBClient

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "eoHq8OwyRkcNPgQXCi4N2zKZEXhRLfebFENNe9XmOn4NQ1N6SU8J54IcRCShpwURxUWhJ0JgR832s_MAsM4n-Q=="
INFLUX_ORG = "meit"
INFLUX_BUCKET = "meit"

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)

# measurement="control" 데이터 전체 삭제
client.delete_api().delete(
    start="1970-01-01T00:00:00Z",
    stop="2100-01-01T00:00:00Z",
    predicate='_measurement="control"',
    bucket=INFLUX_BUCKET,
    org=INFLUX_ORG
)

print("Control measurement 데이터 삭제 완료")
client.close()
