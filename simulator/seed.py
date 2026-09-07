import asyncio
import random
from datetime import datetime, timedelta
from simulator.wearable import generate_readings
from services.api.database import AsyncSessionLocal
from services.api.models.models import WearableReading
from sqlalchemy import select


async def seed_case(case_id: str, days: int = 8):
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    readings = generate_readings(case_id, start, end, interval_minutes=5)
    async with AsyncSessionLocal() as db:
        db.add_all(readings)
        await db.commit()
    print(f"Seeded {len(readings)} readings for {case_id}")


async def main():
    cases = ["case-001", "case-002", "case-003"]
    for case in cases:
        await seed_case(case)


if __name__ == "__main__":
    asyncio.run(main())
