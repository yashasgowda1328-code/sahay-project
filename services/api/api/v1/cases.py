from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from database import get_db
from models.models import (
    CaseStatus, Alert, Intervention, CounsellingSession, FollowUp,
    District, User, Counsellor, PersonalBaseline, DeviationRecord, AuditLog
)
from schemas.schemas import CaseSummary, CaseDetailResponse, DashboardMetrics, DistrictMetrics, CounsellingSessionOut, FollowUpOut, AlertOut, InterventionOut, AuditLogOut

router = APIRouter()


@router.get("/list", response_model=list[CaseSummary])
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
    cases = result.scalars().all()
    
    return [
        CaseSummary(
            case_id=c.case_id,
            person_name=c.person_name or c.case_id,
            case_type=c.case_type or "Other Atrocity",
            age=c.age,
            district=c.district,
            state=c.state,
            assigned_counsellor=c.assigned_counsellor_id,
            priority=c.priority,
            monitoring_status=c.monitoring_status or "active",
            consent_status=c.consent_status or "pending",
            case_opened=c.case_opened_date,
            last_counselling=c.last_counselling_date,
            next_follow_up=c.next_follow_up_date,
            last_reading=None,
        )
        for c in cases
    ]


@router.get("/{case_id}", response_model=CaseDetailResponse)
async def get_case(case_id: str, db: AsyncSession = Depends(get_db)):
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
    
    alerts_result = await db.execute(select(Alert).where(Alert.case_id == case_id).order_by(desc(Alert.created_at)).limit(20))
    alerts = alerts_result.scalars().all()
    
    interventions_result = await db.execute(select(Intervention).where(Intervention.case_id == case_id).order_by(desc(Intervention.created_at)).limit(50))
    interventions = interventions_result.scalars().all()
    
    sessions_result = await db.execute(select(CounsellingSession).where(CounsellingSession.case_id == case_id).order_by(desc(CounsellingSession.created_at)).limit(50))
    sessions = sessions_result.scalars().all()
    
    followups_result = await db.execute(select(FollowUp).where(FollowUp.case_id == case_id).order_by(desc(FollowUp.created_at)).limit(20))
    followups = followups_result.scalars().all()
    
    audit_result = await db.execute(select(AuditLog).where(AuditLog.case_id == case_id).order_by(desc(AuditLog.performed_at)).limit(100))
    audits = audit_result.scalars().all()
    
    current_features = {}
    if status.current_features:
        import json
        current_features = json.loads(status.current_features)
    
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
    
    return CaseDetailResponse(
        case_id=status.case_id,
        person_name=status.person_name or status.case_id,
        case_type=status.case_type or "Other Atrocity",
        age=status.age,
        district=status.district,
        state=status.state,
        assigned_counsellor=status.assigned_counsellor_id,
        priority=status.priority,
        monitoring_status=status.monitoring_status,
        consent_status=status.consent_status,
        case_opened=status.case_opened_date,
        last_counselling=status.last_counselling_date,
        next_follow_up=status.next_follow_up_date,
        last_reading=None,
        baseline=baseline_dict,
        current_features=current_features,
        deviations=[
            DeviationOut(
                id=d.id, case_id=d.case_id, feature_name=d.feature_name,
                timestamp=d.timestamp, raw_value=d.raw_value,
                baseline_value=d.baseline_value, absolute_deviation=d.absolute_deviation,
                percentage_deviation=d.percentage_deviation, ewma=d.ewma,
                deviation=d.deviation, z_score=d.z_score,
                persistence_count=d.persistence_count, change_detected=d.change_detected,
            )
            for d in deviations
        ],
        explanation=status.details,
        alerts=[
            AlertOut(
                id=a.id, case_id=a.case_id, priority=a.priority,
                alert_type=a.alert_type, status=a.status,
                explanation=a.explanation, details=a.details,
                feature_snapshot=a.feature_snapshot, baseline_snapshot=a.baseline_snapshot,
                requires_counsellor_review=a.requires_counsellor_review,
                created_at=a.created_at, updated_at=a.updated_at,
            )
            for a in alerts
        ],
        interventions=[
            InterventionOut(
                id=i.id, case_id=i.case_id, alert_id=i.alert_id,
                category=i.category, description=i.description,
                protocol_reference=i.protocol_reference, status=i.status,
                created_by=i.created_by, created_at=i.created_at, updated_at=i.updated_at,
            )
            for i in interventions
        ],
        counselling_sessions=[
            CounsellingSessionOut(
                id=s.id, case_id=s.case_id, counsellor_id=s.counsellor_id,
                session_type=s.session_type, duration_minutes=s.duration_minutes,
                status=s.status, summary=s.summary,
                next_follow_up_date=s.next_follow_up_date, created_at=s.created_at,
            )
            for s in sessions
        ],
        follow_ups=[
            FollowUpOut(
                id=f.id, case_id=f.case_id, counsellor_id=f.counsellor_id,
                purpose=f.purpose, status=f.status, notes=f.notes,
                due_date=f.due_date, created_at=f.created_at,
            )
            for f in followups
        ],
        audit_logs=[
            AuditLogOut(
                id=l.id, case_id=l.case_id, action=l.action,
                entity_type=l.entity_type, entity_id=l.entity_id,
                details=l.details, performed_by=l.performed_by,
                performed_at=l.performed_at,
            )
            for l in audits
        ],
    )


@router.get("/dashboard/state", response_model=dict)
async def state_dashboard(db: AsyncSession = Depends(get_db)):
    total_cases_result = await db.execute(select(func.count()).select_from(CaseStatus))
    total_cases = total_cases_result.scalar() or 0
    
    high_priority_result = await db.execute(select(func.count()).select_from(CaseStatus).where(CaseStatus.priority == "HIGH_PRIORITY"))
    high_priority = high_priority_result.scalar() or 0
    
    watch_result = await db.execute(select(func.count()).select_from(CaseStatus).where(CaseStatus.priority == "WATCH"))
    watch = watch_result.scalar() or 0
    
    normal_result = await db.execute(select(func.count()).select_from(CaseStatus).where(CaseStatus.priority == "NORMAL"))
    normal = normal_result.scalar() or 0
    
    active_result = await db.execute(select(func.count()).select_from(CaseStatus).where(CaseStatus.monitoring_status == "active"))
    active_monitoring = active_result.scalar() or 0
    
    open_alerts_result = await db.execute(select(func.count()).select_from(Alert).where(Alert.status == "OPEN"))
    open_alerts = open_alerts_result.scalar() or 0
    
    followups_due_result = await db.execute(
        select(func.count()).select_from(FollowUp).where(FollowUp.status == "scheduled", FollowUp.due_date <= datetime.utcnow())
    )
    follow_ups_due = followups_due_result.scalar() or 0
    
    district_result = await db.execute(
        select(CaseStatus.district, func.count().label("total"), func.count().filter(CaseStatus.priority == "HIGH_PRIORITY").label("high"), func.count().filter(CaseStatus.priority == "WATCH").label("watch"), func.count().filter(CaseStatus.priority == "NORMAL").label("normal"), func.count().filter(CaseStatus.monitoring_status == "active").label("active"), func.count().filter(Alert.status == "OPEN").label("alerts"))
        .select_from(CaseStatus)
        .outerjoin(Alert, CaseStatus.case_id == Alert.case_id)
        .group_by(CaseStatus.district)
    )
    districts = []
    for row in district_result.all():
        districts.append({
            "district_name": row.district or "Unassigned",
            "total_cases": row.total or 0,
            "high_priority": row.high or 0,
            "watch": row.watch or 0,
            "normal": row.normal or 0,
            "active_monitoring": row.active or 0,
            "open_alerts": row.alerts or 0,
            "counsellors": 0,
        })
    
    return {
        "metrics": {
            "total_cases": total_cases,
            "high_priority": high_priority,
            "watch": watch,
            "normal": normal,
            "active_monitoring": active_monitoring,
            "open_alerts": open_alerts,
            "follow_ups_due": follow_ups_due,
        },
        "districts": districts,
    }


@router.get("/dashboard/district/{district_name}", response_model=DistrictMetrics)
async def district_dashboard(district_name: str, db: AsyncSession = Depends(get_db)):
    district_result = await db.execute(select(District).where(District.name == district_name))
    district = district_result.scalar_one_or_none()
    if not district:
        raise HTTPException(status_code=404, detail="District not found")
    
    total_cases_result = await db.execute(select(func.count()).select_from(CaseStatus).where(CaseStatus.district == district_name))
    total_cases = total_cases_result.scalar() or 0
    
    high_priority_result = await db.execute(select(func.count()).select_from(CaseStatus).where(CaseStatus.district == district_name, CaseStatus.priority == "HIGH_PRIORITY"))
    high_priority = high_priority_result.scalar() or 0
    
    watch_result = await db.execute(select(func.count()).select_from(CaseStatus).where(CaseStatus.district == district_name, CaseStatus.priority == "WATCH"))
    watch = watch_result.scalar() or 0
    
    normal_result = await db.execute(select(func.count()).select_from(CaseStatus).where(CaseStatus.district == district_name, CaseStatus.priority == "NORMAL"))
    normal = normal_result.scalar() or 0
    
    active_result = await db.execute(select(func.count()).select_from(CaseStatus).where(CaseStatus.district == district_name, CaseStatus.monitoring_status == "active"))
    active_monitoring = active_result.scalar() or 0
    
    open_alerts_result = await db.execute(select(func.count()).select_from(Alert).join(CaseStatus, Alert.case_id == CaseStatus.case_id).where(CaseStatus.district == district_name, Alert.status == "OPEN"))
    open_alerts = open_alerts_result.scalar() or 0
    
    followups_due_result = await db.execute(select(func.count()).select_from(FollowUp).join(CaseStatus, FollowUp.case_id == CaseStatus.case_id).where(CaseStatus.district == district_name, FollowUp.status == "scheduled", FollowUp.due_date <= datetime.utcnow()))
    follow_ups_due = followups_due_result.scalar() or 0
    
    counsellors_result = await db.execute(select(func.count()).select_from(Counsellor).where(Counsellor.district_id == district.id, Counsellor.is_active == True))
    counsellors_count = counsellors_result.scalar() or 0
    
    return DistrictMetrics(
        district_name=district_name,
        total_cases=total_cases,
        high_priority=high_priority,
        watch=watch,
        normal=normal,
        active_monitoring=active_monitoring,
        open_alerts=open_alerts,
        follow_ups_due=follow_ups_due,
        counsellors=counsellors_count,
    )


@router.get("/counsellor/{counsellor_id}", response_model=dict)
async def counsellor_dashboard(counsellor_id: str, db: AsyncSession = Depends(get_db)):
    my_cases_result = await db.execute(select(CaseStatus).where(CaseStatus.assigned_counsellor_id == counsellor_id))
    my_cases = my_cases_result.scalars().all()
    
    total_cases = len(my_cases)
    high_priority = sum(1 for c in my_cases if c.priority == "HIGH_PRIORITY")
    watch = sum(1 for c in my_cases if c.priority == "WATCH")
    normal = sum(1 for c in my_cases if c.priority == "NORMAL")
    
    active_monitoring = sum(1 for c in my_cases if c.monitoring_status == "active")
    
    open_alerts_result = await db.execute(select(func.count()).select_from(Alert).where(Alert.case_id.in_([c.case_id for c in my_cases]), Alert.status == "OPEN"))
    open_alerts = open_alerts_result.scalar() or 0
    
    followups_due_result = await db.execute(select(func.count()).select_from(FollowUp).where(FollowUp.counsellor_id == counsellor_id, FollowUp.status == "scheduled", FollowUp.due_date <= datetime.utcnow()))
    follow_ups_due = followups_due_result.scalar() or 0
    
    today_followups_result = await db.execute(select(func.count()).select_from(FollowUp).where(FollowUp.counsellor_id == counsellor_id, FollowUp.status == "scheduled", FollowUp.due_date >= datetime.utcnow().date()))
    today_followups = today_followups_result.scalar() or 0
    
    return {
        "metrics": {
            "my_cases": total_cases,
            "high_priority": high_priority,
            "watch": watch,
            "normal": normal,
            "active_monitoring": active_monitoring,
            "open_alerts": open_alerts,
            "follow_ups_due": follow_ups_due,
            "today_followups": today_followups,
        },
        "cases": [
            {
                "case_id": c.case_id,
                "person_name": c.person_name or c.case_id,
                "priority": c.priority,
                "case_type": c.case_type,
                "monitoring_status": c.monitoring_status,
                "last_counselling": c.last_counselling_date,
                "next_follow_up": c.next_follow_up_date,
            }
            for c in my_cases
        ],
    }
