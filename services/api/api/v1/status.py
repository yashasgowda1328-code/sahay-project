from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from database import get_db
from models.models import WearableReading, ExtractedFeature, CaseStatus, PersonalBaseline, DeviationRecord, AnalysisHistory
from schemas.schemas import WearableReadingBatch, FeatureOut, BaselineOut, DeviationOut, CaseStatusOut, AnalysisHistoryOut, CaseStatusResponse, CaseSummary
from ml.pipeline import extract_features_for_case, compute_baseline, detect_changes, compute_priority, run_analysis
import json


router = APIRouter()


@router.get("/cases", response_model=list[CaseSummary])
async def list_cases(
    db: AsyncSession = Depends(get_db),
    priority: str | None = None,
    district: str | None = None,
    case_type: str | None = None,
    counsellor: str | None = None,
    monitoring: str | None = None,
):
    query = select(CaseStatus).order_by(desc(CaseStatus.computed_at))
    if priority:
        query = query.where(CaseStatus.priority == priority)
    if district:
        query = query.where(CaseStatus.district == district)
    if case_type:
        query = query.where(CaseStatus.case_type == case_type)
    if counsellor:
        query = query.where(CaseStatus.assigned_counsellor_id == counsellor)
    if monitoring:
        query = query.where(CaseStatus.monitoring_status == monitoring)

    result = await db.execute(query)
    rows = result.scalars().all()
    return [
        CaseSummary(
            case_id=r.case_id,
            person_name=r.person_name or r.case_id,
            case_type=r.case_type or "Other Atrocity",
            age=r.age,
            district=r.district,
            state=r.state,
            assigned_counsellor=r.assigned_counsellor_id,
            priority=r.priority,
            monitoring_status=r.monitoring_status or "active",
            consent_status=r.consent_status or "pending",
            case_opened=r.case_opened_date,
            last_counselling=r.last_counselling_date,
            next_follow_up=r.next_follow_up_date,
            last_reading=None,
        )
        for r in rows
    ]


async def run_analysis(case_id: str, db: AsyncSession):
    result = await db.execute(
        select(WearableReading).where(WearableReading.case_id == case_id).order_by(WearableReading.timestamp)
    )
    readings = result.scalars().all()
    if not readings:
        return

    features = await extract_features_for_case(db, case_id, readings)
    baseline = await compute_baseline(db, case_id)
    if baseline:
        await detect_changes(db, case_id, features, baseline)
    status = await compute_priority(db, case_id)
    await db.commit()


@router.post("/readings/ingest")
async def ingest_readings(batch: WearableReadingBatch, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    readings = [
        WearableReading(
            case_id=batch.case_id,
            timestamp=r.timestamp,
            heart_rate=r.heart_rate,
            steps_increment=r.steps_increment,
            activity_level=r.activity_level,
            is_inactive=r.is_inactive,
        )
        for r in batch.readings
    ]
    db.add_all(readings)
    await db.flush()

    background_tasks.add_task(run_analysis, batch.case_id, db)

    return {"ingested": len(readings), "status": "analysis_queued"}


@router.get("/readings/{case_id}", response_model=list[dict])
async def get_readings(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WearableReading).where(WearableReading.case_id == case_id).order_by(WearableReading.timestamp.desc()).limit(100)
    )
    readings = result.scalars().all()
    return [
        {
            "id": r.id,
            "case_id": r.case_id,
            "timestamp": r.timestamp.isoformat(),
            "heart_rate": r.heart_rate,
            "steps_increment": r.steps_increment,
            "activity_level": r.activity_level,
            "is_inactive": r.is_inactive,
        }
        for r in readings
    ]


@router.get("/cases/{case_id}/status", response_model=CaseStatusResponse)
async def get_case_status(case_id: str, db: AsyncSession = Depends(get_db)):
    status_result = await db.execute(select(CaseStatus).where(CaseStatus.case_id == case_id))
    status = status_result.scalar_one_or_none()
    if not status:
        raise HTTPException(status_code=404, detail="Case not found")

    baseline_result = await db.execute(select(PersonalBaseline).where(PersonalBaseline.case_id == case_id))
    baseline = baseline_result.scalar_one_or_none()

    deviations_result = await db.execute(
        select(DeviationRecord).where(DeviationRecord.case_id == case_id).order_by(desc(DeviationRecord.timestamp)).limit(20)
    )
    deviations = deviations_result.scalars().all()

    current_features = json.loads(status.current_features) if status.current_features else {}
    baseline_dict = {}
    if baseline:
        baseline_dict = {
            "hr_median": baseline.hr_median,
            "hr_mad": baseline.hr_mad,
            "steps_median": baseline.steps_median,
            "active_ratio_median": baseline.active_ratio_median,
            "inactive_minutes_median": baseline.inactive_minutes_median,
            "sample_count": baseline.sample_count,
        }

    return CaseStatusResponse(
        case_id=status.case_id,
        priority=status.priority,
        computed_at=status.computed_at,
        details=status.details,
        current_features=current_features,
        baseline=baseline_dict,
        deviations=[
            DeviationOut(
                id=d.id,
                case_id=d.case_id,
                feature_name=d.feature_name,
                timestamp=d.timestamp,
                raw_value=d.raw_value,
                baseline_value=d.baseline_value,
                absolute_deviation=d.absolute_deviation,
                percentage_deviation=d.percentage_deviation,
                ewma=d.ewma,
                deviation=d.deviation,
                z_score=d.z_score,
                persistence_count=d.persistence_count,
                change_detected=d.change_detected,
            )
            for d in deviations
        ],
    )


@router.get("/cases/{case_id}/analysis", response_model=list[AnalysisHistoryOut])
async def get_analysis_history(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AnalysisHistory).where(AnalysisHistory.case_id == case_id).order_by(desc(AnalysisHistory.computed_at)).limit(50)
    )
    history = result.scalars().all()
    return [
        AnalysisHistoryOut(
            id=h.id,
            case_id=h.case_id,
            priority=h.priority,
            computed_at=h.computed_at,
            details=h.details,
            feature_snapshot=h.feature_snapshot,
            baseline_snapshot=h.baseline_snapshot,
            explanation=h.explanation,
        )
        for h in history
    ]


@router.get("/cases/{case_id}/baseline", response_model=BaselineOut)
async def get_baseline(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PersonalBaseline).where(PersonalBaseline.case_id == case_id))
    baseline = result.scalar_one_or_none()
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")
    return BaselineOut(
        id=baseline.id,
        case_id=baseline.case_id,
        computed_at=baseline.computed_at,
        window=baseline.window,
        hr_mean=baseline.hr_mean,
        hr_median=baseline.hr_median,
        hr_mad=baseline.hr_mad,
        hr_std=baseline.hr_std,
        steps_mean=baseline.steps_mean,
        steps_median=baseline.steps_median,
        active_ratio_mean=baseline.active_ratio_mean,
        active_ratio_median=baseline.active_ratio_median,
        inactive_minutes_mean=baseline.inactive_minutes_mean,
        inactive_minutes_median=baseline.inactive_minutes_median,
        sample_count=baseline.sample_count,
    )


@router.get("/cases/{case_id}/deviations", response_model=list[DeviationOut])
async def get_deviations(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DeviationRecord).where(DeviationRecord.case_id == case_id).order_by(desc(DeviationRecord.timestamp)).limit(50)
    )
    deviations = result.scalars().all()
    return [
        DeviationOut(
            id=d.id,
            case_id=d.case_id,
            feature_name=d.feature_name,
            timestamp=d.timestamp,
            raw_value=d.raw_value,
            baseline_value=d.baseline_value,
            absolute_deviation=d.absolute_deviation,
            percentage_deviation=d.percentage_deviation,
            ewma=d.ewma,
            deviation=d.deviation,
            z_score=d.z_score,
            persistence_count=d.persistence_count,
            change_detected=d.change_detected,
        )
        for d in deviations
    ]
