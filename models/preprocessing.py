# anomaly_detector 입력용
# 최근 10분 데이터 평균

import pandas as pd

def preprocess_sensor_data(df: pd.DataFrame, window: str = "10T") -> pd.DataFrame:
    """
    센서 raw 데이터를 받아서 10분 평균으로 집계
    anomaly_detector 입력용으로 전처리
    
    Args:
        df (pd.DataFrame): timestamp + 센서 필드가 포함된 데이터프레임
        window (str): 리샘플링 기준 (기본 10분 = "10T")
    
    Returns:
        pd.DataFrame: 10분 단위 평균으로 전처리된 데이터
    """

    if df.empty:
        return df

    # timestamp를 datetime으로 보장
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp")

    # 리샘플링 (10분 평균)
    df_resampled = df.resample(window).mean()

    # 결측치 처리 (앞 값으로 채우기 → ffill, 필요시 bfill)
    df_resampled = df_resampled.fillna(method="ffill").fillna(method="bfill")

    # index를 다시 컬럼으로 복원
    df_resampled = df_resampled.reset_index()

    return df_resampled
