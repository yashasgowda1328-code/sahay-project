from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from database import get_db
from models.models import Alert, AlertReview, Intervention, Outcome, AuditLog
from schemas.schemas import AlertReviewCreate, AlertReviewOut, InterventionCreate, InterventionOut, OutcomeCreate, OutcomeOut, AuditLogOut
import json

router = APIRouter()


@router.post("/alerts/{alert_id}/review", response_model=AlertReviewOut)
async def review_alert(alert_id: int, payload: AlertReviewCreate, db: AsyncSession = Depends(get_db)):
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    review = AlertReview(
        alert_id=alert_id,
        case_id=alert.case_id,
        counsellor_id=payload.counsellor_id,
        review_notes=payload.review_notes,
    )
    db.add(review)

    audit = AuditLog(
        case_id=alert.case_id,
        action="alert_reviewed",
        entity_type="alert",
        entity_id=alert_id,
        details=json.dumps({"counsellor_id": payload.counsellor_id, "notes": payload.review_notes}),
        performed_by=payload.counsellor_id,
    )
    db.add(audit)

    await db.flush()
    return AlertReviewOut(
        id=review.id,
        alert_id=review.alert_id,
        case_id=review.case_id,
        counsellor_id=review.counsellor_id,
        review_notes=review.review_notes,
        reviewed_at=review.reviewed_at,
    )


@router.post("/interventions", response_model=InterventionOut)
async def create_intervention(payload: InterventionCreate, db: AsyncSession = Depends(get_db)):
    intervention = Intervention(
        case_id=payload.case_id,
        alert_id=payload.alert_id,
        category=payload.category,
        description=payload.description,
        protocol_reference=payload.protocol_reference,
        status=payload.status,
        created_by=payload.created_by,
    )
    db.add(intervention)

    audit = AuditLog(
        case_id=payload.case_id,
        action="intervention_created",
        entity_type="intervention",
        entity_id=0,
        details=json.dumps({
            "category": payload.category,
            "status": payload.status,
            "protocol_reference": payload.protocol_reference,
            "description": payload.description,
        }),
        performed_by=payload.created_by,
    )
    db.add(audit)
    await db.flush()

    audit.entity_id = intervention.id
    await db.flush()

    return InterventionOut(
        id=intervention.id,
        case_id=intervention.case_id,
        alert_id=intervention.alert_id,
        category=intervention.category,
        description=intervention.description,
        protocol_reference=intervention.protocol_reference,
        status=intervention.status,
        created_by=intervention.created_by,
        created_at=intervention.created_at,
        updated_at=intervention.updated_at,
    )


@router.post("/outcomes", response_model=OutcomeOut)
async def record_outcome(payload: OutcomeCreate, db: AsyncSession = Depends(get_db)):
    intervention = await db.get(Intervention, payload.intervention_id)
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")

    outcome = Outcome(
        intervention_id=payload.intervention_id,
        case_id=intervention.case_id,
        outcome_notes=payload.outcome_notes,
        recorded_by=payload.recorded_by,
    )
    db.add(outcome)

    audit = AuditLog(
        case_id=intervention.case_id,
        action="outcome_recorded",
        entity_type="outcome",
        entity_id=0,
        details=json.dumps({"intervention_id": payload.intervention_id, "notes": payload.outcome_notes}),
        performed_by=payload.recorded_by,
    )
    db.add(audit)
    await db.flush()

    audit.entity_id = outcome.id
    await db.flush()

    return OutcomeOut(
        id=outcome.id,
        intervention_id=outcome.intervention_id,
        case_id=outcome.case_id,
        outcome_notes=outcome.outcome_notes,
        recorded_by=outcome.recorded_by,
        recorded_at=outcome.recorded_at,
    )


@router.get("/cases/{case_id}/interventions", response_model=list[InterventionOut])
async def get_interventions(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Intervention).where(Intervention.case_id == case_id).order_by(desc(Intervention.created_at)).limit(100)
    )
    interventions = result.scalars().all()
    return [
        InterventionOut(
            id=i.id,
            case_id=i.case_id,
            alert_id=i.alert_id,
            category=i.category,
            description=i.description,
            protocol_reference=i.protocol_reference,
            status=i.status,
            created_by=i.created_by,
            created_at=i.created_at,
            updated_at=i.updated_at,
        )
        for i in interventions
    ]


@router.get("/cases/{case_id}/audit", response_model=list[AuditLogOut])
async def get_audit_logs(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AuditLog).where(AuditLog.case_id == case_id).order_by(desc(AuditLog.performed_at)).limit(200)
    )
    logs = result.scalars().all()
    return [
        AuditLogOut(
            id=l.id,
            case_id=l.case_id,
            action=l.action,
            entity_type=l.entity_type,
            entity_id=l.entity_id,
            details=l.details,
            performed_by=l.performed_by,
            performed_at=l.performed_at,
        )
        for l in logs
    ]


@router.get("/protocols/search")
async def search_protocols(q: str = Query(..., min_length=1), max_results: int = Query(3, ge=1, le=10)):
    from protocols.retriever import search_protocols as search
    results = search(q, max_results=max_results)
    return {"query": q, "results": results}


@router.get("/protocols/{category}")
async def get_protocol(category: str):
    from protocols.retriever import get_protocol as fetch_protocol
    result = fetch_protocol(category)
    if not result:
        raise HTTPException(status_code=404, detail="Protocol not found")
    return result
