# preprocessing.py
import pandas as pd
from utils.fetch_data import fetch_data

def preprocess_sensor_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    anomaly_detector 입력용 전처리
    - 최근 10행 raw 센서 데이터를 그대로 사용
    - 범주형/이산형 값 처리 필요 없음
    
    Args:
        df (pd.DataFrame): timestamp + 센서 필드가 포함된 데이터프레임
    
    Returns:
        pd.DataFrame: 최근 10행 데이터
    """

    if df.empty:
        return df

    # timestamp를 datetime으로 변환
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # 최근 10행 선택
    recent_df = df.sort_values("timestamp").iloc[-10:].copy()

    return recent_df.reset_index(drop=True)


# 테스트
if __name__ == "__main__":
    raw_data = fetch_data()
    df = preprocess_sensor_data(raw_data)
    print(df)
    print(f"DataFrame shape: {df.shape}")  # -> (10, 센서컬럼수 + timestamp)
