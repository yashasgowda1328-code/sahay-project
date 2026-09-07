from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.models import User, Role, District
from schemas.schemas import UserLogin, UserCreate, UserOut, RoleOut, DistrictOut
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/login")
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == payload.username))
    user = result.scalar_one_or_none()
    if not user or not pwd_context.verify(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive account")
    
    role_result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = role_result.scalar_one_or_none()
    
    district_name = None
    if user.district_id:
        district_result = await db.execute(select(District).where(District.id == user.district_id))
        district = district_result.scalar_one_or_none()
        district_name = district.name if district else None
    
    return {
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": role.name if role else None,
        "district": district_name,
        "demo": True,
    }


@router.get("/roles", response_model=list[RoleOut])
async def list_roles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Role).order_by(Role.id))
    roles = result.scalars().all()
    return [RoleOut(id=r.id, name=r.name, description=r.description) for r in roles]


@router.get("/districts", response_model=list[DistrictOut])
async def list_districts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(District).where(District.is_active == True).order_by(District.name))
    districts = result.scalars().all()
    return [DistrictOut(id=d.id, name=d.name, state=d.state, is_active=d.is_active) for d in districts]


@router.post("/users", response_model=UserOut)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    role_result = await db.execute(select(Role).where(Role.name == payload.role_name))
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    district_id = None
    if payload.district_name:
        district_result = await db.execute(select(District).where(District.name == payload.district_name))
        district = district_result.scalar_one_or_none()
        if not district:
            raise HTTPException(status_code=400, detail="Invalid district")
        district_id = district.id
    
    user = User(
        username=payload.username,
        hashed_password=pwd_context.hash(payload.password),
        full_name=payload.full_name,
        role_id=role.id,
        district_id=district_id,
    )
    db.add(user)
    await db.flush()
    
    district_name = None
    if district_id:
        district_result = await db.execute(select(District).where(District.id == district_id))
        district = district_result.scalar_one_or_none()
        district_name = district.name if district else None
    
    return UserOut(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        role_name=role.name,
        district_name=district_name,
        is_active=user.is_active,
    )
