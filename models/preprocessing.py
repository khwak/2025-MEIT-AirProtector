import pandas as pd

def preprocess_sensor_data(raw_data: dict) -> dict:
    """
    raw_data: { "CO2": {"value": 800, "time": "..."} , "CO": {...}, ... }
    return: { "CO2": float, "CO": float, ... }  # 전처리된 값만 반환
    """
    processed = {}

    for key, entry in raw_data.items():
        try:
            value = float(entry.get("value", None))
        except (ValueError, TypeError):
            value = None

        # 단위 변환 예시 (필요시)
        if key == "HCHO" and value is not None:
            # µg/m³ -> ppm 변환 가정 (실제 변환식 필요)
            # 여기서는 단순히 값 그대로 사용
            processed[key] = value
        else:
            processed[key] = value

    return processed
