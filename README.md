# 2025-MEIT-AirProtector

# 스마트 환기 제어 시스템

본 프로젝트는 실내 공기질 센서 데이터를 활용하여 **환기 필요 여부 및 소요 시간 예측**, **센서 이상 감지**, **환기 시설 제어**를 수행하는 Flask 기반 서버 애플리케이션입니다.  

---

## 프로젝트 구조

```text
project/
│
├─ app.py # Flask 서버 메인
│
├─ models/ # 분석 모듈
│ ├─ anomaly_detector.py # 고장 감지
│ ├─ ventilation_predictor.py # 환기 시간 예측
│ ├─ threshold.py # 이상 상황 판단
│ ├─ preprocessing.py # 데이터 전처리, 스케일링
│ ├─ anomaly_lstm_ae.h5 # 센서 이상/고장 감지 모델
│ ├─ anomaly_scaler.pkl # 센서 이상/고장 감지 스케일러
│ ├─ ventilation_classifier_lgbm.pkl # 환기 필요 여부 예측 모델
│ ├─ ventilation_regressor_lgbm.pkl # 환기 소요 시간 예측 모델
│ └─ ventilation_scaler.pkl # 환기 모델 스케일러
│
├─ utils/ # 유틸 함수
│ ├─ cycle_timer.py # cycle_elapsed_time 계산
│ ├─ fetch_data.py # 실시간 데이터 fetch
│ ├─ mqtt_publish.py # 센서로 값 전송
│ ├─ mqtt_subsribe.py # ESP32에서 수신한 값을 DB에 저장
│ └─ ventilation_controller.py # 환기 시설 조절 실행
│
└─ templates/
├─ admin.html # 관리자 화면
└─ user.html # 사용자 화면


---

## 시스템 아키텍처

![System Architecture](https://raw.githubusercontent.com/khwak/for-image/main/meit_architec.png)

---

## 적용 기술

| 구분 | 목적 | 사용 데이터 | 출력/조치 |
| --- | --- | --- | --- |
| **통계적 기준 (Threshold)** | 환경치 이상 여부 탐지 | CO₂, CO, HCHO, TVOC | - 경고/심각 단계 판단 <br> → 창문/환기팬 제어 |
| **LSTM-Autoencoder** | - 센서 이상 감지 | 모든 센서 데이터 | - 센서 고장/데이터 드리프트 탐지 <br> - 안정 수치 도달까지 남은 시간 회귀 예측 <br> → 창문 종료 시점 안내 |
| **LightGBM** | - 환기에 걸리는 시간 예측 | 모든 센서 데이터 및 cycle_elapsed_time, remaining_minutes | - Classifier: 환기 필요 여부 예측 <br> - Regressor: 환기 소요 시간 예측 |

