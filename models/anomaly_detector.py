# anomaly_detector.py
import numpy as np
import pandas as pd
import joblib
import os
from tensorflow.keras.models import load_model

# 1. 모델 & 스케일러 로드
SEQ_LENGTH = 10
sensor_cols = [
    'indoor_temp', 'outdoor_temp', 'indoor_hum', 'outdoor_hum',
    'wind_speed', 'window_open', 'fan_speed', 'CO2', 'CO', 'HCHO', 'TVOC'
]

BASE_DIR = os.path.dirname(__file__)  
scaler = joblib.load(os.path.join(BASE_DIR, "anomaly_scaler.pkl"))
model = load_model(os.path.join(BASE_DIR, "anomaly_lstm_ae.h5"), compile=False)

THRESHOLD = 0.2178


# 2. 시퀀스 생성 함수
def create_sequences(data, seq_length=SEQ_LENGTH):
    sequences = []
    for i in range(len(data) - seq_length + 1):
        sequences.append(data[i:i+seq_length])
    return np.array(sequences)


# 3. 이상 탐지 함수
def detect_anomaly(processed: pd.DataFrame):
    """
    processed: preprocess_sensor_data() 결과 DataFrame
    return: dict {timestamp: {loss, anomaly_flag}}
    """
    if processed.empty:
        return {}

    # 센서 값 추출
    data = processed[sensor_cols].values

    # 스케일링
    data_scaled = scaler.transform(data)

    # 시퀀스 변환
    X = create_sequences(data_scaled, SEQ_LENGTH)
    if len(X) == 0:
        return {}

    # Reconstruction 예측
    X_pred = model.predict(X)

    # Reconstruction loss (MAE)
    losses = np.mean(np.abs(X_pred - X), axis=(1, 2))

    # 결과 변환
    results = {}
    timestamps = processed["timestamp"].iloc[SEQ_LENGTH-1:].reset_index(drop=True)

    for i, ts in enumerate(timestamps):
        loss = losses[i]
        if np.isnan(loss) or np.isinf(loss):
            loss = None  # JSON에 안전하게 내려주기
        results[str(ts)] = {
            "loss_mae": loss,
            "threshold": THRESHOLD,
            "anomaly": bool(loss is not None and loss > THRESHOLD)
        }

    return results
