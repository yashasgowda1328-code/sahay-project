from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.models import User, Counsellor, District
from schemas.schemas import CounsellorOut

router = APIRouter()


@router.get("/", response_model=list[CounsellorOut])
async def list_counsellors(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Counsellor, User, District)
        .join(User, Counsellor.user_id == User.id)
        .outerjoin(District, Counsellor.district_id == District.id)
        .where(Counsellor.is_active == True)
    )
    rows = result.all()
    return [
        CounsellorOut(
            id=c.id,
            user_id=c.user_id,
            full_name=u.full_name,
            designation=c.designation,
            department=c.department,
            district_name=d.name if d else None,
            phone=c.phone,
            email=c.email,
            assigned_date=c.assigned_date,
            active_cases=c.active_cases,
            sessions_completed=c.sessions_completed,
        )
        for c, u, d in rows
    ]


@router.get("/{counsellor_id}", response_model=CounsellorOut)
async def get_counsellor(counsellor_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Counsellor, User, District)
        .join(User, Counsellor.user_id == User.id)
        .outerjoin(District, Counsellor.district_id == District.id)
        .where(Counsellor.id == counsellor_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Counsellor not found")
    c, u, d = row
    return CounsellorOut(
        id=c.id,
        user_id=c.user_id,
        full_name=u.full_name,
        designation=c.designation,
        department=c.department,
        district_name=d.name if d else None,
        phone=c.phone,
        email=c.email,
        assigned_date=c.assigned_date,
        active_cases=c.active_cases,
        sessions_completed=c.sessions_completed,
    )
