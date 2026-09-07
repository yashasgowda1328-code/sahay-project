import asyncio
import random
from datetime import datetime, timedelta
from typing import List
from services.api.database import AsyncSessionLocal
from services.api.models.models import WearableReading, ExtractedFeature, PersonalBaseline, DeviationRecord, CaseStatus, AnalysisHistory
from ml.pipeline import run_analysis


ACTIVITY_LEVELS = ["sedentary", "light", "moderate", "vigorous"]


def generate_readings(case_id: str, start: datetime, end: datetime, interval_minutes: int = 5,
                      hr_base: float = 70, hr_noise: float = 5, active_chance: float = 0.3) -> List[WearableReading]:
    readings = []
    current = start
    while current <= end:
        hour = current.hour
        is_sleep_hours = hour >= 22 or hour < 6
        is_work_hours = 9 <= hour < 17

        if is_sleep_hours:
            hr = hr_base + random.uniform(-3, 3)
            activity = "sedentary"
            inactive = True
            steps_inc = 0
        elif is_work_hours:
            hr = hr_base + random.uniform(-hr_noise, hr_noise * 2)
            if random.random() < active_chance:
                activity = random.choices(ACTIVITY_LEVELS[1:], weights=[70, 25, 5])[0]
            else:
                activity = "sedentary"
            inactive = activity == "sedentary"
            steps_inc = random.randint(0, 20) if activity != "sedentary" else 0
        else:
            hr = hr_base + random.uniform(0, hr_noise * 2)
            if random.random() < active_chance:
                activity = random.choices(ACTIVITY_LEVELS[1:], weights=[50, 35, 15])[0]
            else:
                activity = "sedentary"
            inactive = activity == "sedentary"
            steps_inc = random.randint(0, 50) if activity != "sedentary" else 0

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


async def clear_case(case_id: str):
    async with AsyncSessionLocal() as db:
        tables = [
            WearableReading, ExtractedFeature, PersonalBaseline,
            DeviationRecord, CaseStatus, AnalysisHistory
        ]
        for table in tables:
            await db.execute(table.__table__.delete().where(table.__table__.c.case_id == case_id))
        await db.commit()


async def run_phased_scenario(name: str, case_id: str):
    await clear_case(case_id)
    phases = []

    if name == "normal":
        phases = [
            (datetime.utcnow() - timedelta(days=8), datetime.utcnow(), 72, 5, 0.35, "NORMAL"),
        ]
    elif name == "persistent_change":
        phases = [
            (datetime.utcnow() - timedelta(days=8), datetime.utcnow() - timedelta(days=1), 72, 5, 0.35, "NORMAL"),
            (datetime.utcnow() - timedelta(days=1), datetime.utcnow(), 95, 8, 0.1, "HIGH_PRIORITY"),
        ]
    elif name == "recovery":
        phases = [
            (datetime.utcnow() - timedelta(days=10), datetime.utcnow() - timedelta(days=4), 72, 5, 0.35, "NORMAL"),
            (datetime.utcnow() - timedelta(days=4), datetime.utcnow() - timedelta(days=1), 95, 8, 0.1, "HIGH_PRIORITY"),
            (datetime.utcnow() - timedelta(days=1), datetime.utcnow(), 72, 5, 0.35, "NORMAL"),
        ]
    else:
        raise ValueError(f"Unknown scenario: {name}")

    results = []
    for start, end, hr_base, hr_noise, active_chance, expected in phases:
        async with AsyncSessionLocal() as db:
            readings = generate_readings(case_id, start, end, hr_base=hr_base, hr_noise=hr_noise, active_chance=active_chance)
            db.add_all(readings)
            await db.commit()

            status = await run_analysis(case_id, db)
            await db.commit()
            results.append((expected, status.priority))
            print(f"  Phase {start.strftime('%m-%d')} to {end.strftime('%m-%d')}: expected={expected}, got={status.priority}")

    return results


async def main():
    scenarios = ["normal", "persistent_change", "recovery"]
    for scenario in scenarios:
        case_id = f"scenario-{scenario}"
        print(f"Scenario {scenario}:")
        results = await run_phased_scenario(scenario, case_id)
        for expected, actual in results:
            match = "OK" if expected == actual else "MISMATCH"
            print(f"    {expected} -> {actual} ({match})")
        print()


if __name__ == "__main__":
    asyncio.run(main())
