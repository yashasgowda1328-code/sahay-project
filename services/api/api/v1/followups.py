from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from database import get_db
from models.models import FollowUp, AuditLog, CaseStatus
from schemas.schemas import FollowUpIn, FollowUpOut

router = APIRouter()


@router.post("/", response_model=FollowUpOut)
async def create_followup(payload: FollowUpIn, db: AsyncSession = Depends(get_db)):
    followup = FollowUp(
        case_id=payload.case_id,
        counsellor_id=payload.counsellor_id,
        purpose=payload.purpose,
        status=payload.status,
        notes=payload.notes,
        due_date=payload.due_date,
    )
    db.add(followup)
    
    status_result = await db.execute(select(CaseStatus).where(CaseStatus.case_id == payload.case_id))
    status = status_result.scalar_one_or_none()
    if status and payload.due_date:
        status.next_follow_up_date = payload.due_date
    
    audit = AuditLog(
        case_id=payload.case_id,
        action="follow_up_scheduled",
        entity_type="follow_up",
        entity_id=0,
        details=f'{{"counsellor_id": "{payload.counsellor_id}", "purpose": "{payload.purpose or ""}"}}',
        performed_by=payload.counsellor_id,
    )
    db.add(audit)
    await db.flush()
    audit.entity_id = followup.id
    await db.flush()
    
    return FollowUpOut(
        id=followup.id,
        case_id=followup.case_id,
        counsellor_id=followup.counsellor_id,
        purpose=followup.purpose,
        status=followup.status,
        notes=followup.notes,
        due_date=followup.due_date,
        created_at=followup.created_at,
    )


@router.get("/followups/cases/{case_id}", response_model=list[FollowUpOut])
async def list_followups(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FollowUp).where(FollowUp.case_id == case_id).order_by(desc(FollowUp.created_at)).limit(20)
    )
    followups = result.scalars().all()
    return [
        FollowUpOut(
            id=f.id,
            case_id=f.case_id,
            counsellor_id=f.counsellor_id,
            purpose=f.purpose,
            status=f.status,
            notes=f.notes,
            due_date=f.due_date,
            created_at=f.created_at,
        )
        for f in followups
    ]
