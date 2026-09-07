from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
from database import get_db
from models.models import CounsellingSession, AuditLog
from schemas.schemas import CounsellingSessionIn, CounsellingSessionOut

router = APIRouter()


@router.post("/", response_model=CounsellingSessionOut)
async def create_session(payload: CounsellingSessionIn, db: AsyncSession = Depends(get_db)):
    session = CounsellingSession(
        case_id=payload.case_id,
        counsellor_id=payload.counsellor_id,
        session_type=payload.session_type,
        duration_minutes=payload.duration_minutes,
        status=payload.status,
        summary=payload.summary,
        next_follow_up_date=payload.next_follow_up_date,
    )
    db.add(session)
    
    from models.models import CaseStatus
    status_result = await db.execute(select(CaseStatus).where(CaseStatus.case_id == payload.case_id))
    status = status_result.scalar_one_or_none()
    if status:
        status.last_counselling_date = datetime.utcnow()
        if payload.next_follow_up_date:
            status.next_follow_up_date = payload.next_follow_up_date
    
    audit = AuditLog(
        case_id=payload.case_id,
        action="counselling_session_recorded",
        entity_type="counselling_session",
        entity_id=0,
        details=f'{{"session_type": "{payload.session_type}", "counsellor_id": "{payload.counsellor_id}"}}',
        performed_by=payload.counsellor_id,
    )
    db.add(audit)
    await db.flush()
    audit.entity_id = session.id
    await db.flush()
    
    return CounsellingSessionOut(
        id=session.id,
        case_id=session.case_id,
        counsellor_id=session.counsellor_id,
        session_type=session.session_type,
        duration_minutes=session.duration_minutes,
        status=session.status,
        summary=session.summary,
        next_follow_up_date=session.next_follow_up_date,
        created_at=session.created_at,
    )


@router.get("/counselling/cases/{case_id}", response_model=list[CounsellingSessionOut])
async def list_sessions(case_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CounsellingSession).where(CounsellingSession.case_id == case_id).order_by(desc(CounsellingSession.created_at)).limit(50)
    )
    sessions = result.scalars().all()
    return [
        CounsellingSessionOut(
            id=s.id,
            case_id=s.case_id,
            counsellor_id=s.counsellor_id,
            session_type=s.session_type,
            duration_minutes=s.duration_minutes,
            status=s.status,
            summary=s.summary,
            next_follow_up_date=s.next_follow_up_date,
            created_at=s.created_at,
        )
        for s in sessions
    ]
