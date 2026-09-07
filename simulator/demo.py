import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Optional
from services.api.database import AsyncSessionLocal
from services.api.models.models import WearableReading, ExtractedFeature, PersonalBaseline, DeviationRecord, CaseStatus, AnalysisHistory, Alert, DemoState
from ml.pipeline import run_analysis
from sqlalchemy import select


DEMO_CASE_ID = "demo-case-001"
random.seed(42)


def _generate_readings_deterministic(case_id: str, start: datetime, end: datetime,
                                      hr_base: float = 70, hr_noise: float = 5,
                                      active_chance: float = 0.35) -> List[WearableReading]:
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
                activity = random.choice(["light", "moderate", "vigorous"])
            else:
                activity = "sedentary"
            inactive = activity == "sedentary"
            steps_inc = random.randint(0, 20) if activity != "sedentary" else 0
        else:
            hr = hr_base + random.uniform(0, hr_noise * 2)
            if random.random() < active_chance:
                activity = random.choice(["light", "moderate", "vigorous"])
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
        current += timedelta(minutes=5)
    return readings


async def _clear_case(case_id: str):
    async with AsyncSessionLocal() as db:
        tables = [
            WearableReading, ExtractedFeature, PersonalBaseline,
            DeviationRecord, CaseStatus, AnalysisHistory, Alert
        ]
        for table in tables:
            await db.execute(table.__table__.delete().where(table.__table__.c.case_id == case_id))
        await db.commit()


async def _clear_analysis(case_id: str):
    async with AsyncSessionLocal() as db:
        tables = [
            WearableReading, ExtractedFeature,
            DeviationRecord, CaseStatus, AnalysisHistory, Alert
        ]
        for table in tables:
            await db.execute(table.__table__.delete().where(table.__table__.c.case_id == case_id))
        await db.commit()


async def _run_phase(case_id: str, start: datetime, end: datetime,
                     hr_base: float = 70, hr_noise: float = 5,
                     active_chance: float = 0.35) -> dict:
    readings = _generate_readings_deterministic(case_id, start, end, hr_base, hr_noise, active_chance)
    async with AsyncSessionLocal() as db:
        db.add_all(readings)
        await db.commit()
        status = await run_analysis(case_id, db)
        await db.commit()

        result = await db.execute(
            select(CaseStatus).where(CaseStatus.case_id == case_id)
        )
        case_status = result.scalar_one_or_none()

        alerts_result = await db.execute(
            select(Alert).where(Alert.case_id == case_id).order_by(Alert.created_at.desc())
        )
        alerts = alerts_result.scalars().all()

        return {
            "priority": case_status.priority if case_status else "NORMAL",
            "details": case_status.details if case_status else "{}",
            "alert_count": len(alerts),
            "readings_added": len(readings),
        }


async def start_demo() -> dict:
    global random
    random.seed(42)
    await _clear_case(DEMO_CASE_ID)
    await _save_phase(0)
    return {
        "case_id": DEMO_CASE_ID,
        "phase": 0,
        "status": "started",
        "message": "Demo started. Baseline collection phase.",
    }


async def tick_demo() -> dict:
    global random
    now = datetime.utcnow()
    phase_info = {}

    if not await _get_demo_exists():
        raise ValueError("Demo not started. Call start_demo first.")

    current_phase = await _get_current_phase()
    if current_phase >= 6:
        return {
            "case_id": DEMO_CASE_ID,
            "phase": current_phase,
            "status": "completed",
            "message": "Demo cycle completed. Call reset_demo to restart.",
        }

    next_phase = current_phase + 1

    if next_phase > 1:
        await _clear_analysis(DEMO_CASE_ID)

    if next_phase == 1:
        start = now - timedelta(days=8)
        end = now - timedelta(days=1)
        phase_info = await _run_phase(DEMO_CASE_ID, start, end, hr_base=72, hr_noise=5, active_chance=0.35)
        phase_info["case_id"] = DEMO_CASE_ID
        phase_info["phase"] = 1
        phase_info["status"] = "baseline_complete"
        phase_info["message"] = "Baseline established. Persistent change phase starting."

    elif next_phase == 2:
        start = now - timedelta(days=1)
        end = now - timedelta(minutes=30)
        phase_info = await _run_phase(DEMO_CASE_ID, start, end, hr_base=95, hr_noise=8, active_chance=0.1)
        phase_info["case_id"] = DEMO_CASE_ID
        phase_info["phase"] = 2
        phase_info["status"] = "watch_possible"
        phase_info["message"] = "Persistent change detected. Monitoring continues."

    elif next_phase == 3:
        start = now - timedelta(minutes=25)
        end = now - timedelta(minutes=5)
        phase_info = await _run_phase(DEMO_CASE_ID, start, end, hr_base=100, hr_noise=10, active_chance=0.05)
        phase_info["case_id"] = DEMO_CASE_ID
        phase_info["phase"] = 3
        phase_info["status"] = "high_priority"
        phase_info["message"] = "HIGH_PRIORITY alert generated. Counsellor review required."

    elif next_phase == 4:
        start = now - timedelta(minutes=4)
        end = now
        phase_info = await _run_phase(DEMO_CASE_ID, start, end, hr_base=100, hr_noise=10, active_chance=0.05)
        phase_info["case_id"] = DEMO_CASE_ID
        phase_info["phase"] = 4
        phase_info["status"] = "intervention_ready"
        phase_info["message"] = "Alert active. Protocol assistance and intervention can be recorded."

    elif next_phase == 5:
        start = now - timedelta(days=3)
        end = now
        phase_info = await _run_phase(DEMO_CASE_ID, start, end, hr_base=75, hr_noise=6, active_chance=0.3)
        phase_info["case_id"] = DEMO_CASE_ID
        phase_info["phase"] = 5
        phase_info["status"] = "recovery"
        phase_info["message"] = "Recovery observed. Continued monitoring."

    elif next_phase == 6:
        start = now - timedelta(days=2)
        end = now
        phase_info = await _run_phase(DEMO_CASE_ID, start, end, hr_base=72, hr_noise=5, active_chance=0.35)
        phase_info["case_id"] = DEMO_CASE_ID
        phase_info["phase"] = 6
        phase_info["status"] = "normal"
        phase_info["message"] = "Returned to normal baseline. Demo cycle complete."

    await _save_phase(next_phase)
    return phase_info


async def reset_demo() -> dict:
    await _clear_case(DEMO_CASE_ID)
    if await _get_demo_exists():
        async with AsyncSessionLocal() as db:
            await db.execute(DemoState.__table__.delete().where(DemoState.id == 1))
            await db.commit()
    return {"case_id": DEMO_CASE_ID, "status": "reset", "message": "Demo reset."}


async def get_demo_state() -> dict:
    exists = await _get_demo_exists()
    if not exists:
        return {"case_id": DEMO_CASE_ID, "phase": 0, "status": "not_started"}

    phase = await _get_current_phase()
    status_map = {
        0: "not_started",
        1: "baseline_complete",
        2: "watch_possible",
        3: "high_priority",
        4: "intervention_ready",
        5: "recovery",
        6: "normal",
    }
    return {
        "case_id": DEMO_CASE_ID,
        "phase": phase,
        "status": status_map.get(phase, "unknown"),
    }


async def _get_demo_exists() -> bool:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(DemoState).where(DemoState.id == 1))
        return result.scalar_one_or_none() is not None


async def _get_current_phase() -> int:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(DemoState).where(DemoState.id == 1))
        state = result.scalar_one_or_none()
        return state.phase if state else 0


async def _save_phase(phase: int):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(DemoState).where(DemoState.id == 1))
        state = result.scalar_one_or_none()
        if state:
            state.phase = phase
            state.updated_at = datetime.utcnow()
        else:
            db.add(DemoState(id=1, phase=phase))
        await db.commit()
