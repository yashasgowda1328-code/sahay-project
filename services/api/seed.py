import asyncio
import random
from datetime import datetime, timedelta
from sqlalchemy import select
from services.api.database import AsyncSessionLocal
from services.api.models.models import (
    User, Role, District, Counsellor, CaseStatus, PersonalBaseline,
    WearableReading, ExtractedFeature, DeviationRecord, AnalysisHistory,
    Alert, AlertReview, Intervention, Outcome, CounsellingSession, FollowUp, Consent
)
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DISTRICTS = [
    {"name": "Bengaluru Urban", "state": "Karnataka"},
    {"name": "Mysuru", "state": "Karnataka"},
    {"name": "Mandya", "state": "Karnataka"},
    {"name": "Tumakuru", "state": "Karnataka"},
]

ROLES = [
    {"name": "STATE_ADMIN", "description": "State-level administrator"},
    {"name": "DISTRICT_ADMIN", "description": "District administrator"},
    {"name": "COUNSELLOR", "description": "Field counsellor"},
]

USERS = [
    {"username": "state.admin", "password": "demo123", "full_name": "State Administrator", "role": "STATE_ADMIN", "district": None},
    {"username": "district.admin", "password": "demo123", "full_name": "District Administrator", "role": "DISTRICT_ADMIN", "district": "Bengaluru Urban"},
    {"username": "counsellor.anjali", "password": "demo123", "full_name": "Anjali Menon", "role": "COUNSELLOR", "district": "Bengaluru Urban"},
    {"username": "counsellor.rahul", "password": "demo123", "full_name": "Rahul Verma", "role": "COUNSELLOR", "district": "Mysuru"},
    {"username": "counsellor", "password": "demo123", "full_name": "Demo Counsellor", "role": "COUNSELLOR", "district": "Bengaluru Urban"},
]

COUNSELLORS = [
    {"user": "counsellor.anjali", "designation": "Senior Counsellor", "department": "Women and Child Welfare", "phone": "+91-9876543210", "email": "anjali.menon@gov.in"},
    {"user": "counsellor.rahul", "designation": "Counsellor", "department": "Social Welfare", "phone": "+91-9876543211", "email": "rahul.verma@gov.in"},
]

CASES = [
    {"case_id": "CASE-001", "person_name": "Ananya Sharma", "case_type": "Domestic Violence", "district": "Bengaluru Urban", "counsellor": "counsellor.anjali", "priority": "NORMAL", "age": 28},
    {"case_id": "CASE-002", "person_name": "Priya Verma", "case_type": "Sexual Assault", "district": "Bengaluru Urban", "counsellor": "counsellor.anjali", "priority": "WATCH", "age": 24},
    {"case_id": "CASE-003", "person_name": "Meera Nair", "case_type": "Trafficking", "district": "Mysuru", "counsellor": "counsellor.rahul", "priority": "HIGH_PRIORITY", "age": 21},
    {"case_id": "CASE-004", "person_name": "Kavya Singh", "case_type": "Physical Assault", "district": "Mysuru", "counsellor": "counsellor.rahul", "priority": "NORMAL", "age": 30},
    {"case_id": "CASE-005", "person_name": "Neha Kumari", "case_type": "Domestic Violence", "district": "Mandya", "counsellor": "counsellor.anjali", "priority": "WATCH", "age": 26},
    {"case_id": "CASE-006", "person_name": "Rahul Kumar", "case_type": "Other Atrocity", "district": "Mandya", "counsellor": "counsellor.rahul", "priority": "HIGH_PRIORITY", "age": 32},
    {"case_id": "CASE-007", "person_name": "Amit Das", "case_type": "Murder", "district": "Tumakuru", "counsellor": "counsellor.anjali", "priority": "NORMAL", "age": 45},
    {"case_id": "CASE-008", "person_name": "Sanjay Yadav", "case_type": "Physical Assault", "district": "Tumakuru", "counsellor": "counsellor.rahul", "priority": "WATCH", "age": 38},
    {"case_id": "CASE-009", "person_name": "Arjun Patel", "case_type": "Sexual Assault", "district": "Bengaluru Urban", "counsellor": "counsellor.anjali", "priority": "HIGH_PRIORITY", "age": 29},
]

SESSION_TYPES = ["Initial Counselling", "Follow-up", "Crisis Support", "Rehabilitation Support", "Other"]


def generate_readings(case_id: str, start: datetime, end: datetime, hr_base: float, hr_noise: float, active_chance: float) -> list:
    readings = []
    current = start
    idx = 0
    while current <= end:
        hr = max(40, min(180, hr_base + random.uniform(-hr_noise, hr_noise)))
        active = random.random() < active_chance
        steps = random.randint(0, 20) if active else 0
        inactive = random.randint(5, 20) if not active else 0
        readings.append(WearableReading(
            case_id=case_id,
            timestamp=current,
            heart_rate=round(hr, 1),
            steps_increment=steps,
            activity_level="active" if active else "sedentary",
            is_inactive=not active,
        ))
        current += timedelta(minutes=15)
        idx += 1
    return readings


async def seed():
    async with AsyncSessionLocal() as db:
        for d in DISTRICTS:
            existing = await db.execute(select(District).where(District.name == d["name"]))
            if not existing.scalar_one_or_none():
                db.add(District(name=d["name"], state=d["state"]))
        
        for r in ROLES:
            existing = await db.execute(select(Role).where(Role.name == r["name"]))
            if not existing.scalar_one_or_none():
                db.add(Role(name=r["name"], description=r["description"]))
        
        await db.flush()
        
        for u in USERS:
            role_result = await db.execute(select(Role).where(Role.name == u["role"]))
            role = role_result.scalar_one_or_none()
            district_id = None
            if u["district"]:
                district_result = await db.execute(select(District).where(District.name == u["district"]))
                district = district_result.scalar_one_or_none()
                district_id = district.id if district else None
            
            existing = await db.execute(select(User).where(User.username == u["username"]))
            if existing.scalar_one_or_none():
                continue
            
            user = User(
                username=u["username"],
                hashed_password=pwd_context.hash(u["password"]),
                full_name=u["full_name"],
                role_id=role.id,
                district_id=district_id,
            )
            db.add(user)
        
        await db.flush()
        
        for c in COUNSELLORS:
            user_result = await db.execute(select(User).where(User.username == c["user"]))
            user = user_result.scalar_one_or_none()
            if not user:
                continue
            district_result = await db.execute(select(District).where(District.name == c["department"]))
            district = district_result.scalar_one_or_none()
            
            existing = await db.execute(select(Counsellor).where(Counsellor.user_id == user.id))
            if existing.scalar_one_or_none():
                continue
            
            db.add(Counsellor(
                user_id=user.id,
                designation=c["designation"],
                department=c["department"],
                district_id=district.id if district else None,
                phone=c["phone"],
                email=c["email"],
                assigned_date=datetime.utcnow() - timedelta(days=30),
                active_cases=0,
                sessions_completed=0,
            ))
        
        await db.flush()
        
        counsellor_map = {}
        for c in COUNSELLORS:
            user_result = await db.execute(select(User).where(User.username == c["user"]))
            user = user_result.scalar_one_or_none()
            if not user:
                continue
            counsellor_result = await db.execute(select(Counsellor).where(Counsellor.user_id == user.id))
            counsellor = counsellor_result.scalar_one_or_none()
            if counsellor:
                counsellor_map[c["user"]] = str(counsellor.id)
        
        for case in CASES:
            existing = await db.execute(select(CaseStatus).where(CaseStatus.case_id == case["case_id"]))
            if existing.scalar_one_or_none():
                continue
            
            status = CaseStatus(
                case_id=case["case_id"],
                priority=case["priority"],
                person_name=case["person_name"],
                age=case["age"],
                case_type=case["case_type"],
                district=case["district"],
                state="Karnataka",
                assigned_counsellor_id=case["counsellor"],
                consent_status="granted",
                consent_date=datetime.utcnow() - timedelta(days=10),
                consent_version="v1.0",
                consent_recorded_by=case["counsellor"],
                monitoring_status="active",
                case_opened_date=datetime.utcnow() - timedelta(days=30),
                last_counselling_date=datetime.utcnow() - timedelta(days=3),
                next_follow_up_date=datetime.utcnow() + timedelta(days=7),
            )
            db.add(status)
            
            db.add(Consent(
                case_id=case["case_id"],
                status="granted",
                consent_date=datetime.utcnow() - timedelta(days=10),
                consent_version="v1.0",
                recorded_by=case["counsellor"],
                notes="Consent obtained for monitoring and support.",
            ))
        
        await db.flush()
        
        for case in CASES:
            counsellor_id = counsellor_map.get(case["counsellor"], "1")
            for i in range(3):
                session_type = random.choice(SESSION_TYPES)
                db.add(CounsellingSession(
                    case_id=case["case_id"],
                    counsellor_id=counsellor_id,
                    session_type=session_type,
                    duration_minutes=random.randint(30, 90),
                    status="completed",
                    summary=f"{session_type} session conducted. Case discussed and support provided.",
                    next_follow_up_date=datetime.utcnow() + timedelta(days=random.randint(7, 30)),
                ))
            
            db.add(FollowUp(
                case_id=case["case_id"],
                counsellor_id=counsellor_id,
                purpose="Routine follow-up",
                status="scheduled",
                notes="Follow up on recent progress and wearable data.",
                due_date=datetime.utcnow() + timedelta(days=random.randint(1, 14)),
            ))
        
        await db.commit()
    print("Seed data created successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
