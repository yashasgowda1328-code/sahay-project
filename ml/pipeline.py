import json
import math
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
try:
    from models.models import WearableReading, ExtractedFeature, PersonalBaseline, DeviationRecord, CaseStatus, AnalysisHistory, Alert
except ImportError:
    from services.api.models.models import WearableReading, ExtractedFeature, PersonalBaseline, DeviationRecord, CaseStatus, AnalysisHistory, Alert


WINDOW_MINUTES = 15
BASELINE_DAYS = 7
EWMA_ALPHA = 0.3
Z_WATCH = 2.0
Z_HIGH = 3.0
PERSISTENT_WINDOWS = 3


def _median(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return float(np.median(values))


def _mad(values: List[float], median_val: Optional[float] = None) -> Optional[float]:
    if not values:
        return None
    if median_val is None:
        median_val = _median(values)
    if median_val is None:
        return None
    return float(np.median([abs(v - median_val) for v in values]))


def _robust_z_score(value: float, median_val: Optional[float], mad: Optional[float]) -> float:
    if median_val is None or mad is None or mad == 0:
        return 0.0
    return abs(value - median_val) / (1.4826 * mad)


def _linear_trend(values: List[float]) -> Optional[float]:
    if len(values) < 2:
        return None
    x = np.arange(len(values))
    y = np.array(values)
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    numerator = np.sum((x - x_mean) * (y - y_mean))
    denominator = np.sum((x - x_mean) ** 2)
    if denominator == 0:
        return 0.0
    return float(numerator / denominator)


def compute_features(readings: List[WearableReading]) -> Optional[ExtractedFeature]:
    if not readings:
        return None

    hrs = [r.heart_rate for r in readings]
    steps = sum(r.steps_increment for r in readings)
    active = sum(1 for r in readings if r.activity_level in ("light", "moderate", "vigorous"))
    inactive = sum(1 for r in readings if r.is_inactive)
    total = len(readings)

    hr_mean = float(np.mean(hrs))
    hr_std = float(np.std(hrs)) if len(hrs) > 1 else 0.0
    hr_median = _median(hrs)
    hr_mad = _mad(hrs, hr_median)
    hr_min = float(np.min(hrs))
    hr_max = float(np.max(hrs))
    hr_trend = _linear_trend(hrs)

    active_minutes = (active / total) * WINDOW_MINUTES if total else 0.0
    inactive_minutes = (inactive / total) * WINDOW_MINUTES if total else 0.0
    active_ratio = active / total if total else 0.0

    signal_quality = 1.0
    expected_count = max(1, int(WINDOW_MINUTES / 5))
    if total < expected_count:
        signal_quality = total / expected_count

    ts = readings[0].timestamp
    return ExtractedFeature(
        case_id=readings[0].case_id,
        timestamp=ts,
        window_minutes=WINDOW_MINUTES,
        hr_mean=hr_mean,
        hr_std=hr_std,
        hr_median=hr_median,
        hr_mad=hr_mad,
        hr_min=hr_min,
        hr_max=hr_max,
        hr_trend=hr_trend,
        signal_quality=signal_quality,
        steps_count=steps,
        active_minutes=active_minutes,
        inactive_minutes=inactive_minutes,
        active_ratio=active_ratio,
        consecutive_inactive_windows=0,
    )


async def extract_features_for_case(db: AsyncSession, case_id: str, readings: List[WearableReading]):
    features = []
    readings_sorted = sorted(readings, key=lambda r: r.timestamp)
    current_window = []
    window_start = None
    consecutive_inactive = 0

    for r in readings_sorted:
        if window_start is None:
            window_start = r.timestamp
            current_window.append(r)
            continue

        if (r.timestamp - window_start).total_seconds() <= WINDOW_MINUTES * 60:
            current_window.append(r)
        else:
            feat = compute_features(current_window)
            if feat:
                feat.consecutive_inactive_windows = consecutive_inactive
                features.append(feat)
                if all(not r.is_inactive for r in current_window):
                    consecutive_inactive += 1
                else:
                    consecutive_inactive = 0
            current_window = [r]
            window_start = r.timestamp

    if current_window:
        feat = compute_features(current_window)
        if feat:
            feat.consecutive_inactive_windows = consecutive_inactive
            features.append(feat)

    db.add_all(features)
    await db.flush()
    return features


async def compute_baseline(db: AsyncSession, case_id: str) -> Optional[PersonalBaseline]:
    cutoff = datetime.utcnow() - timedelta(days=BASELINE_DAYS)
    result = await db.execute(
        select(ExtractedFeature).where(
            ExtractedFeature.case_id == case_id,
            ExtractedFeature.timestamp >= cutoff,
        )
    )
    feats = result.scalars().all()

    if not feats:
        return None

    hr_means = [f.hr_mean for f in feats if f.hr_mean is not None]
    hr_medians = [f.hr_median for f in feats if f.hr_median is not None]
    hr_mads = [f.hr_mad for f in feats if f.hr_mad is not None]
    hr_stds = [f.hr_std for f in feats if f.hr_std is not None]
    steps = [f.steps_count for f in feats]
    active_ratios = [f.active_ratio for f in feats]
    inactive_mins = [f.inactive_minutes for f in feats]

    existing_result = await db.execute(select(PersonalBaseline).where(PersonalBaseline.case_id == case_id))
    existing = existing_result.scalar_one_or_none()
    if existing:
        existing.hr_mean = float(np.mean(hr_means)) if hr_means else None
        existing.hr_median = _median(hr_medians) if hr_medians else None
        existing.hr_mad = _mad(hr_medians) if hr_medians else None
        existing.hr_std = float(np.mean(hr_stds)) if hr_stds else None
        existing.steps_mean = float(np.mean(steps)) if steps else None
        existing.steps_median = _median(steps) if steps else None
        existing.active_ratio_mean = float(np.mean(active_ratios)) if active_ratios else None
        existing.active_ratio_median = _median(active_ratios) if active_ratios else None
        existing.inactive_minutes_mean = float(np.mean(inactive_mins)) if inactive_mins else None
        existing.inactive_minutes_median = _median(inactive_mins) if inactive_mins else None
        existing.sample_count = len(feats)
        existing.computed_at = datetime.utcnow()
        baseline = existing
    else:
        baseline = PersonalBaseline(
            case_id=case_id,
            window=f"{BASELINE_DAYS}d",
            hr_mean=float(np.mean(hr_means)) if hr_means else None,
            hr_median=_median(hr_medians) if hr_medians else None,
            hr_mad=_mad(hr_medians) if hr_medians else None,
            hr_std=float(np.mean(hr_stds)) if hr_stds else None,
            steps_mean=float(np.mean(steps)) if steps else None,
            steps_median=_median(steps) if steps else None,
            active_ratio_mean=float(np.mean(active_ratios)) if active_ratios else None,
            active_ratio_median=_median(active_ratios) if active_ratios else None,
            inactive_minutes_mean=float(np.mean(inactive_mins)) if inactive_mins else None,
            inactive_minutes_median=_median(inactive_mins) if inactive_mins else None,
            sample_count=len(feats),
        )
        db.add(baseline)
    await db.flush()
    return baseline


async def get_baseline(db: AsyncSession, case_id: str) -> Optional[PersonalBaseline]:
    result = await db.execute(
        select(PersonalBaseline).where(PersonalBaseline.case_id == case_id)
    )
    return result.scalar_one_or_none()


def ewma_series(values: List[float], alpha: float = EWMA_ALPHA) -> List[float]:
    if not values:
        return []
    result = [values[0]]
    for v in values[1:]:
        result.append(alpha * v + (1 - alpha) * result[-1])
    return result


async def detect_changes(db: AsyncSession, case_id: str, features: List[ExtractedFeature], baseline: PersonalBaseline):
    if not baseline or not features:
        return []

    feature_map = {
        "hr_mean": (baseline.hr_median, baseline.hr_mad),
        "steps_count": (baseline.steps_median, _mad([baseline.steps_mean] if baseline.steps_mean else [])),
        "active_ratio": (baseline.active_ratio_median, _mad([baseline.active_ratio_mean] if baseline.active_ratio_mean else [])),
        "inactive_minutes": (baseline.inactive_minutes_median, _mad([baseline.inactive_minutes_mean] if baseline.inactive_minutes_mean else [])),
    }

    deviations = []
    for name, (b_median, b_mad) in feature_map.items():
        if b_median is None:
            continue
        values = [getattr(f, name) for f in features]
        ewma_values = ewma_series(values)
        persistence_count = 0
        for f, ewma_val in zip(features, ewma_values):
            raw = getattr(f, name)
            dev = abs(raw - ewma_val) if ewma_val is not None else 0.0
            pct_dev = ((raw - b_median) / b_median * 100) if b_median != 0 else 0.0
            z = _robust_z_score(raw, b_median, b_mad)

            if z >= Z_WATCH:
                persistence_count += 1
            else:
                persistence_count = 0

            change_detected = persistence_count >= PERSISTENT_WINDOWS or z >= Z_HIGH

            deviations.append(
                DeviationRecord(
                    case_id=case_id,
                    feature_name=name,
                    timestamp=f.timestamp,
                    raw_value=raw,
                    baseline_value=b_median,
                    absolute_deviation=dev,
                    percentage_deviation=pct_dev,
                    ewma=ewma_val,
                    deviation=dev,
                    z_score=z,
                    persistence_count=persistence_count,
                    change_detected=change_detected,
                )
            )
    db.add_all(deviations)
    await db.flush()
    return deviations


async def compute_priority(db: AsyncSession, case_id: str) -> CaseStatus:
    result = await db.execute(
        select(DeviationRecord).where(DeviationRecord.case_id == case_id).order_by(DeviationRecord.timestamp.desc()).limit(50)
    )
    recent = result.scalars().all()

    high_features = set()
    watch_features = set()

    feature_timeline: Dict[str, List[DeviationRecord]] = {}
    for d in sorted(recent, key=lambda x: x.timestamp):
        feature_timeline.setdefault(d.feature_name, []).append(d)

    for feature_name, records in feature_timeline.items():
        consecutive_watch = 0
        max_consecutive_high = 0
        for rec in records:
            if rec.z_score >= Z_HIGH:
                consecutive_watch += 1
                max_consecutive_high = max(max_consecutive_high, consecutive_watch)
            elif rec.z_score >= Z_WATCH:
                consecutive_watch += 1
            else:
                consecutive_watch = 0

        if max_consecutive_high >= PERSISTENT_WINDOWS:
            high_features.add(feature_name)
        elif consecutive_watch >= PERSISTENT_WINDOWS:
            watch_features.add(feature_name)

    if high_features:
        priority = "HIGH_PRIORITY"
    elif watch_features:
        priority = "WATCH"
    else:
        priority = "NORMAL"

    latest_features = {}
    for d in sorted(recent, key=lambda x: x.timestamp)[-10:]:
        latest_features[d.feature_name] = {
            "raw_value": d.raw_value,
            "baseline_value": d.baseline_value,
            "z_score": d.z_score,
            "persistence_count": d.persistence_count,
            "change_detected": d.change_detected,
        }

    details = {
        "high_features": sorted(high_features),
        "watch_features": sorted(watch_features),
        "recent_deviations": [
            {"feature": d.feature_name, "z_score": d.z_score, "timestamp": d.timestamp.isoformat(), "persistence": d.persistence_count}
            for d in sorted(recent, key=lambda x: x.timestamp)[:5]
        ],
    }

    explanation = _generate_explanation(
        priority=priority,
        high_features=high_features,
        watch_features=watch_features,
        recent=recent,
        latest_features=latest_features,
    )

    status = await db.get(CaseStatus, case_id)
    if status:
        status.priority = priority
        status.computed_at = datetime.utcnow()
        status.details = json.dumps(details)
        status.current_features = json.dumps(latest_features)
        status.updated_at = datetime.utcnow()
    else:
        status = CaseStatus(
            case_id=case_id,
            priority=priority,
            details=json.dumps(details),
            current_features=json.dumps(latest_features),
        )
        db.add(status)

    baseline = await get_baseline(db, case_id)
    baseline_snapshot = {}
    if baseline:
        baseline_snapshot = {
            "hr_median": baseline.hr_median,
            "hr_mad": baseline.hr_mad,
            "steps_median": baseline.steps_median,
            "active_ratio_median": baseline.active_ratio_median,
            "inactive_minutes_median": baseline.inactive_minutes_median,
        }

    shap_explanation = _generate_shap_explanation(recent, baseline_snapshot)

    history = AnalysisHistory(
        case_id=case_id,
        priority=priority,
        details=json.dumps(details),
        feature_snapshot=json.dumps(latest_features),
        baseline_snapshot=json.dumps(baseline_snapshot),
        explanation=explanation,
    )
    db.add(history)

    if priority == "HIGH_PRIORITY":
        alert = Alert(
            case_id=case_id,
            priority=priority,
            alert_type="HIGH_PRIORITY_REVIEW",
            explanation=explanation,
            details=json.dumps(details),
            feature_snapshot=json.dumps(latest_features),
            baseline_snapshot=json.dumps(baseline_snapshot),
            requires_counsellor_review=True,
        )
        db.add(alert)

    await db.flush()
    return status


def _generate_explanation(
    priority: str,
    high_features: set,
    watch_features: set,
    recent: List[DeviationRecord],
    latest_features: Dict[str, Any],
) -> str:
    parts: List[str] = []

    if priority == "HIGH_PRIORITY":
        parts.append("High priority alert: immediate counsellor review is recommended.")
    elif priority == "WATCH":
        parts.append("Watch status: sustained deviations detected across multiple windows.")
    else:
        parts.append("No significant sustained deviations detected.")

    feature_descriptions = {
        "hr_mean": "heart rate",
        "steps_count": "activity level",
        "active_ratio": "activity ratio",
        "inactive_minutes": "inactivity",
    }

    for feature in sorted(high_features | watch_features):
        label = feature_descriptions.get(feature, feature)
        recs = [r for r in recent if r.feature_name == feature]
        if not recs:
            continue
        latest = max(recs, key=lambda r: r.timestamp)
        if latest.z_score >= Z_HIGH:
            parts.append(f"{label} shows a strong deviation from personal baseline (z-score {latest.z_score:.2f}).")
        elif latest.z_score >= Z_WATCH:
            parts.append(f"{label} shows a moderate deviation from personal baseline (z-score {latest.z_score:.2f}).")

        persistence = latest.persistence_count
        if persistence >= PERSISTENT_WINDOWS:
            parts.append(f"This change has persisted across {persistence} consecutive windows.")

    if not parts:
        return "Analysis completed. No significant deviations from personal baseline."

    return " ".join(parts)


def _generate_shap_explanation(recent: List[DeviationRecord], baseline_snapshot: Dict[str, Any]) -> Dict[str, float]:
    contributions: Dict[str, float] = {}
    for d in recent:
        name = d.feature_name
        z = d.z_score if d.z_score is not None else 0.0
        contributions[name] = contributions.get(name, 0.0) + abs(z)
    total = sum(contributions.values())
    if total > 0:
        for k in contributions:
            contributions[k] = round(contributions[k] / total, 4)
    return contributions


async def run_analysis(case_id: str, db: AsyncSession) -> CaseStatus:
    result = await db.execute(
        select(WearableReading).where(WearableReading.case_id == case_id).order_by(WearableReading.timestamp)
    )
    readings = result.scalars().all()
    if not readings:
        status = await db.get(CaseStatus, case_id)
        if not status:
            status = CaseStatus(case_id=case_id, priority="NORMAL", details="{}")
            db.add(status)
            await db.flush()
        return status

    features = await extract_features_for_case(db, case_id, readings)
    baseline = await compute_baseline(db, case_id)
    if baseline:
        await detect_changes(db, case_id, features, baseline)
    status = await compute_priority(db, case_id)
    await db.commit()
    return status
