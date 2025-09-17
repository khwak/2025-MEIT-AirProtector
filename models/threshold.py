# models/threshold.py

class ThresholdChecker:
    def __init__(self):
        # 각 항목별 정상/경고/심각 기준과 메시지 정의
        self.rules = {
            "CO2": {
                "normal": lambda x: x < 800,
                "warning": lambda x: 800 <= x <= 1000,
                "serious": lambda x: x > 1000,
                "action": {
                    "warning": "-경고 : 창문 50%, 환기팬 50%",
                    "serious": "-심각 : 창문 100%, 환기팬 100%"
                },
                "alert": {
                    "warning": "공기청정기 50% 가동 권고, 냉난방기 절약 모드에서 환기 보조 권고",
                    "serious": "공기청정기 100% 가동 권고, 냉난방기 표준 모드 유지, 장시간 환기 필요 권고"
                }
            },
            "CO": {
                "normal": lambda x: x < 10,
                "warning": lambda x: 10 <= x <= 35,
                "serious": lambda x: x > 35,
                "action": {
                    "warning": "-경고 : 창문 50%, 환기팬 50%",
                    "serious": "-심각 : 창문 100%, 환기팬 100%"
                },
                "alert": {
                    "warning": "공기청정기 50% 가동 권고 (필터 모드), 냉난방기 절약 모드 환기 보조",
                    "serious": "공기청정기 100% 가동 권고, 냉난방기 표준 모드, 즉시 환기 강화 및 원인 제거 권고"
                }
            },
            "HCHO": {
                "normal": lambda x: x <= 80,
                "warning": lambda x: 80 < x <= 200,
                "serious": lambda x: x > 200,
                "action": {
                    "warning": "-경고 : 창문 50%, 환기팬 50%",
                    "serious": "-심각 : 창문 100%, 환기팬 100%"
                },
                "alert": {
                    "warning": "공기청정기 50% 가동 권고 (활성탄/케미컬 필터 모드), 냉난방기 절약 모드 환기 보조",
                    "serious": "공기청정기 100% 가동 권고, 냉난방기 표준 모드, 즉시 환기 및 원인 차단 권고"
                }
            },
            "Benzene": {
                "normal": lambda x: x <= 30,
                "warning": lambda x: 30 < x <= 100,
                "serious": lambda x: x > 100,
                "action": {
                    "warning": "-경고 : 창문 50%, 환기팬 50%",
                    "serious": "-심각 : 창문 100%, 환기팬 100%"
                },
                "alert": {
                    "warning": "공기청정기 50% 가동 권고 (활성탄 필터 강화), 냉난방기 절약 모드 환기 보조",
                    "serious": "공기청정기 100% 가동 권고, 냉난방기 표준 모드, 즉시 환기 및 대피 고려"
                }
            },
            "TVOC": {
                "normal": lambda x: x <= 400,
                "warning": lambda x: 400 < x <= 1000,
                "serious": lambda x: x > 1000,
                "action": {
                    "warning": "-경고: 창문 50%, 환기팬 50%",
                    "serious": "-심각: 창문 100%, 팬 100%, 원인 확인 필요 문구(가스·자재)"
                },
                "alert": {
                    "warning": "공기청정기 50% 가동 권고 (VOC 제거 모드), 냉난방기 절약 모드 환기 보조 권고",
                    "serious": "공기청정기 100% 가동 권고, 냉난방기 표준 모드, 지속 환기 필요"
                }
            }
        }

    def check(self, processed_data: dict) -> dict:
        """
        processed_data: { "CO2": 750, "CO": 5, "HCHO": 50, ... }
        return: {
            "CO2": {"value": 750, "level": "normal/warning/serious", "action": "...", "alert": "..."},
            ...
        }
        """
        results = {}
        for key, value in processed_data.items():
            if value is None:
                continue

            rule = self.rules.get(key, None)
            if not rule:
                continue

            if rule["normal"](value):
                level = "normal"
                action = "정상: 조치 불필요"
                alert = None
            elif rule["warning"](value):
                level = "warning"
                action = rule["action"]["warning"]
                alert = rule["alert"]["warning"]
            elif rule["serious"](value):
                level = "serious"
                action = rule["action"]["serious"]
                alert = rule["alert"]["serious"]
            else:
                level = "unknown"
                action = "판단 불가"
                alert = None

            results[key] = {
                "value": value,
                "level": level,
                "action": action,
                "alert": alert
            }

        return results
