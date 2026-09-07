import random
import math
from datetime import datetime, timedelta
from typing import List
from services.api.models.models import WearableReading


ACTIVITY_LEVELS = ["sedentary", "light", "moderate", "vigorous"]


def generate_readings(case_id: str, start: datetime, end: datetime, interval_minutes: int = 5) -> List[WearableReading]:
    readings = []
    current = start
    base_hr = 70 + random.uniform(-5, 5)
    cumulative_steps = 0

    while current <= end:
        hour = current.hour
        is_sleep_hours = hour >= 22 or hour < 6
        is_work_hours = 9 <= hour < 17

        if is_sleep_hours:
            hr = base_hr + random.uniform(-3, 3)
            activity = "sedentary"
            inactive = True
            steps_inc = 0
        elif is_work_hours:
            hr = base_hr + random.uniform(-5, 10)
            activity = random.choices(ACTIVITY_LEVELS, weights=[70, 20, 8, 2])[0]
            inactive = activity == "sedentary"
            steps_inc = random.randint(0, 15) if activity != "sedentary" else 0
        else:
            hr = base_hr + random.uniform(0, 20)
            activity = random.choices(ACTIVITY_LEVELS, weights=[40, 35, 20, 5])[0]
            inactive = activity == "sedentary"
            steps_inc = random.randint(0, 40) if activity != "sedentary" else 0

        cumulative_steps += steps_inc
        readings.append(
            WearableReading(
                case_id=case_id,
                timestamp=current,
                heart_rate=round(hr, 1),
                steps_increment=steps_inc,
                activity_level=activity,
                is_inactive=inactive,
            )
        )
        current += timedelta(minutes=interval_minutes)

    return readings
