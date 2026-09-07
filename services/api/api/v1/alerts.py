from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from database import get_db
from models.models import Alert
from schemas.schemas import AlertOut


router = APIRouter()


@router.get("/alerts", response_model=list[AlertOut])
async def list_alerts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Alert).where(Alert.status == "OPEN").order_by(desc(Alert.created_at)).limit(100)
    )
    alerts = result.scalars().all()
    return [
        AlertOut(
            id=a.id,
            case_id=a.case_id,
            priority=a.priority,
            alert_type=a.alert_type,
            status=a.status,
            explanation=a.explanation,
            details=a.details,
            feature_snapshot=a.feature_snapshot,
            baseline_snapshot=a.baseline_snapshot,
            requires_counsellor_review=a.requires_counsellor_review,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in alerts
    ]


@router.get("/alerts/{alert_id}", response_model=AlertOut)
async def get_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertOut(
        id=alert.id,
        case_id=alert.case_id,
        priority=alert.priority,
        alert_type=alert.alert_type,
        status=alert.status,
        explanation=alert.explanation,
        details=alert.details,
        feature_snapshot=alert.feature_snapshot,
        baseline_snapshot=alert.baseline_snapshot,
        requires_counsellor_review=alert.requires_counsellor_review,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )
