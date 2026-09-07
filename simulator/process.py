import asyncio
from datetime import datetime
from services.api.database import AsyncSessionLocal
from services.api.models.models import WearableReading, ExtractedFeature, PersonalBaseline, DeviationRecord, CaseStatus
from ml.pipeline import extract_features_for_case, compute_baseline, detect_changes, compute_priority
from sqlalchemy import select


async def process_case(case_id: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(WearableReading).where(WearableReading.case_id == case_id).order_by(WearableReading.timestamp)
        )
        readings = result.scalars().all()
        if not readings:
            print(f"No readings for {case_id}")
            return

        features = await extract_features_for_case(db, case_id, readings)
        baseline = await compute_baseline(db, case_id)
        if baseline:
            await detect_changes(db, case_id, features, baseline)
        status = await compute_priority(db, case_id)
        await db.commit()
        print(f"Processed {case_id}: {len(features)} features, priority={status.priority}")


async def main():
    cases = ["case-001", "case-002", "case-003"]
    for case in cases:
        await process_case(case)


if __name__ == "__main__":
    asyncio.run(main())
