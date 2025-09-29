import pandas as pd
from models.threshold import ThresholdChecker

checker = ThresholdChecker()

def add_cycle_elapsed_time(df: pd.DataFrame):
    """
    df: raw sensor DataFrame
    return: df with 'cycle_elapsed_time' column added
    """
    cycle_active = False
    cycle_elapsed_time = 0
    remaining_minutes = 0
    cycle_elapsed_list = []

    consec_non_normal = 0
    consec_normal = 0
    start_threshold = 3
    end_threshold = 5

    for i, row in df.iterrows():
        processed_data = {
            "CO2": row.get("CO2", 0), 
            "CO": row.get("CO", 0),
            "HCHO": row.get("HCHO", 0), 
            "Benzene": row.get("Benzene", 0), 
            "TVOC": row.get("TVOC", 0)
        }
        result = checker.check(processed_data)
        all_normal = all(v["level"] == "normal" for v in result.values())

        if all_normal:
            consec_normal += 1
            consec_non_normal = 0
        else:
            consec_non_normal += 1
            consec_normal = 0

        # 시작 조건
        if not cycle_active and consec_non_normal >= start_threshold:
            cycle_active = True
            cycle_elapsed_time = 0
            consec_normal = 0

        # 종료 조건
        if cycle_active and consec_normal >= end_threshold:
            cycle_active = False
            cycle_elapsed_time = 0
            consec_normal = 0
            consec_non_normal = 0

        # 진행 중이면 +1
        if cycle_active:
            cycle_elapsed_time += 1

        cycle_elapsed_list.append(cycle_elapsed_time)

    df["cycle_elapsed_time"] = cycle_elapsed_list
    return df
