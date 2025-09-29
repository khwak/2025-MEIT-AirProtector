# ventilation_predict.py
import numpy as np
import pandas as pd
import os
import joblib
from utils.mqtt_subscriber import fetch_data  # 센서 데이터 가져오기


# 1. 모델 로드
BASE_DIR = os.path.dirname(__file__)  
scaler = joblib.load(os.path.join(BASE_DIR, "ventilation_scaler.pkl"))
clf = joblib.load(os.path.join(BASE_DIR, "ventilation_classifier_lgbm.pkl"))
reg = joblib.load(os.path.join(BASE_DIR, "ventilation_regressor_lgbm.pkl"))


# 2. Features 정의
features = [
    "CO2","CO","HCHO","TVOC",
    "indoor_temp","outdoor_temp","indoor_hum","outdoor_hum",
    "wind_speed","window_open","fan_speed","cycle_elapsed_time"
]

def predict_remaining_minutes(raw_data: pd.DataFrame):
    """
    raw_data: pandas DataFrame, mqtt_subscriber에서 가져온 데이터
    return: dict, device별 예측 결과
    """
    if raw_data.empty:
        return {}

    # 스케일링
    df_scaled = raw_data.copy()
    df_scaled[features] = scaler.transform(df_scaled[features])

    # Classifier 예측
    vent_flag_pred = clf.predict(df_scaled[features])

    # Regressor 예측 (환기 필요 시)
    remaining_pred = np.zeros(len(df_scaled))
    if np.any(vent_flag_pred == 1):
        X_reg = df_scaled[vent_flag_pred == 1][features]
        remaining_pred[vent_flag_pred == 1] = reg.predict(X_reg)

    # JSON 형태로 변환
    results = {}
    for idx, row in df_scaled.iterrows():
        results[idx] = {
            "vent_flag": int(vent_flag_pred[idx]),
            "remaining_minutes": int(remaining_pred[idx])
        }

    return results


# 3. 테스트용
if __name__ == "__main__":
    df = fetch_data()
    preds = predict_remaining_minutes(df)
    print(preds)
