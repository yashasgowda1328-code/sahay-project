import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List
from unittest.mock import AsyncMock, MagicMock
import numpy as np

from services.api.models.models import WearableReading, ExtractedFeature, PersonalBaseline, DeviationRecord, CaseStatus
try:
    from ml.pipeline import (
        compute_features,
        extract_features_for_case,
        compute_baseline,
        detect_changes,
        compute_priority,
        ewma_series,
        _median,
        _mad,
        _robust_z_score,
        _linear_trend,
        _generate_explanation,
        _generate_shap_explanation,
        WINDOW_MINUTES,
        Z_WATCH,
        Z_HIGH,
        PERSISTENT_WINDOWS,
    )
except ImportError:
    from services.api.ml.pipeline import (
        compute_features,
        extract_features_for_case,
        compute_baseline,
        detect_changes,
        compute_priority,
        ewma_series,
        _median,
        _mad,
        _robust_z_score,
        _linear_trend,
        _generate_explanation,
        _generate_shap_explanation,
        WINDOW_MINUTES,
        Z_WATCH,
        Z_HIGH,
        PERSISTENT_WINDOWS,
    )


def make_readings(case_id: str, timestamps: List[datetime], heart_rates: List[float],
                  activity_levels: List[str] = None, is_inactives: List[bool] = None,
                  steps_increments: List[int] = None) -> List[WearableReading]:
    if activity_levels is None:
        activity_levels = ["sedentary"] * len(timestamps)
    if is_inactives is None:
        is_inactives = [True] * len(timestamps)
    if steps_increments is None:
        steps_increments = [0] * len(timestamps)
    return [
        WearableReading(
            case_id=case_id,
            timestamp=ts,
            heart_rate=hr,
            steps_increment=si,
            activity_level=act,
            is_inactive=ina,
        )
        for ts, hr, act, ina, si in zip(timestamps, heart_rates, activity_levels, is_inactives, steps_increments)
    ]


class TestFeatureExtraction:
    def test_compute_features_basic(self):
        now = datetime.utcnow()
        readings = make_readings(
            "test",
            [now, now + timedelta(minutes=5), now + timedelta(minutes=10)],
            [70.0, 72.0, 71.0],
            ["sedentary", "light", "sedentary"],
            [True, False, True],
        )
        feat = compute_features(readings)
        assert feat is not None
        assert feat.case_id == "test"
        assert feat.hr_mean == pytest.approx(71.0, abs=0.01)
        assert feat.steps_count == 0
        assert feat.active_minutes == pytest.approx(5.0, abs=0.01)
        assert feat.inactive_minutes == pytest.approx(10.0, abs=0.01)
        assert feat.active_ratio == pytest.approx(1/3, abs=0.01)
        assert feat.signal_quality == pytest.approx(1.0, abs=0.01)

    def test_compute_features_signal_quality(self):
        now = datetime.utcnow()
        readings = make_readings(
            "test",
            [now, now + timedelta(minutes=5)],
            [70.0, 72.0],
        )
        feat = compute_features(readings)
        assert feat is not None
        assert feat.signal_quality == pytest.approx(2/3, abs=0.01)

    def test_compute_features_hr_median_mad(self):
        now = datetime.utcnow()
        readings = make_readings(
            "test",
            [now + timedelta(minutes=i*5) for i in range(5)],
            [70.0, 72.0, 71.0, 69.0, 73.0],
        )
        feat = compute_features(readings)
        assert feat is not None
        assert feat.hr_median == pytest.approx(71.0, abs=0.01)
        assert feat.hr_mad is not None
        assert feat.hr_trend is not None

    def test_compute_features_empty(self):
        assert compute_features([]) is None

    def test_extract_features_windows(self):
        now = datetime.utcnow()
        readings = make_readings(
            "test",
            [now + timedelta(minutes=i*5) for i in range(25)],
            [70.0 + i*0.1 for i in range(25)],
        )
        db = AsyncMock()
        features = asyncio.get_event_loop().run_until_complete(
            extract_features_for_case(db, "test", readings)
        )
        assert len(features) == 7
        assert all(f.window_minutes == WINDOW_MINUTES for f in features)


class TestBaseline:
    def test_median_and_mad(self):
        assert _median([1, 2, 3, 4, 5]) == 3.0
        assert _median([1, 2, 3, 4]) == 2.5
        assert _mad([1, 2, 3, 4, 5], 3.0) == pytest.approx(1.0, abs=0.01)
        assert _mad([1, 2, 3, 4, 5]) == pytest.approx(1.0, abs=0.01)

    def test_robust_z_score(self):
        assert _robust_z_score(10.0, 10.0, 1.0) == 0.0
        assert _robust_z_score(13.0, 10.0, 1.0) == pytest.approx(3.0 / 1.4826, abs=0.01)
        assert _robust_z_score(10.0, None, None) == 0.0

    def test_linear_trend(self):
        assert _linear_trend([1, 2, 3, 4, 5]) == pytest.approx(1.0, abs=0.01)
        assert _linear_trend([5, 4, 3, 2, 1]) == pytest.approx(-1.0, abs=0.01)
        assert _linear_trend([1]) is None

    def test_compute_baseline(self):
        from ml.pipeline import BASELINE_DAYS
        now = datetime.utcnow()
        cutoff = now - timedelta(days=BASELINE_DAYS)
        feats = [
            ExtractedFeature(
                case_id="test",
                timestamp=cutoff + timedelta(days=i),
                window_minutes=WINDOW_MINUTES,
                hr_mean=72.0 + i,
                hr_std=2.0,
                hr_median=72.0 + i,
                hr_mad=1.0,
                steps_count=20,
                active_minutes=5.0,
                inactive_minutes=10.0,
                active_ratio=0.3,
            )
            for i in range(7)
        ]
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = feats
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        db.get = AsyncMock(return_value=None)

        baseline = asyncio.get_event_loop().run_until_complete(compute_baseline(db, "test"))
        assert baseline is not None
        assert baseline.case_id == "test"
        assert baseline.hr_median is not None
        assert baseline.hr_mad is not None
        assert baseline.steps_median is not None
        assert baseline.sample_count == 7


class TestEWMA:
    def test_ewma_series(self):
        values = [10.0, 11.0, 12.0, 15.0]
        result = ewma_series(values, alpha=0.5)
        assert len(result) == 4
        assert result[0] == 10.0
        assert result[1] == pytest.approx(10.5, abs=0.01)
        assert result[2] == pytest.approx(11.25, abs=0.01)

    def test_ewma_empty(self):
        assert ewma_series([]) == []


class TestChangeDetection:
    def test_single_spike_no_high_priority(self):
        now = datetime.utcnow()
        baseline = PersonalBaseline(
            case_id="test",
            hr_median=70.0,
            hr_mad=2.0,
            steps_median=20.0,
            active_ratio_median=0.3,
            inactive_minutes_median=10.0,
        )
        feats = [
            ExtractedFeature(
                case_id="test",
                timestamp=now + timedelta(minutes=i*WINDOW_MINUTES),
                window_minutes=WINDOW_MINUTES,
                hr_mean=70.0,
                hr_std=2.0,
                hr_median=70.0,
                hr_mad=2.0,
                steps_count=20,
                active_minutes=5.0,
                inactive_minutes=10.0,
                active_ratio=0.3,
            )
            for i in range(3)
        ]
        feats[-1].hr_mean = 77.0
        feats[-1].hr_median = 77.0

        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        deviations = asyncio.get_event_loop().run_until_complete(
            detect_changes(db, "test", feats, baseline)
        )
        hr_deviations = [d for d in deviations if d.feature_name == "hr_mean"]
        assert len(hr_deviations) == 3
        assert hr_deviations[-1].change_detected is False
        assert hr_deviations[-1].persistence_count == 1


class TestPriority:
    def test_priority_normal_stable(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)
        db.get = AsyncMock(return_value=None)
        db.add = MagicMock()
        db.flush = AsyncMock()

        status = asyncio.get_event_loop().run_until_complete(compute_priority(db, "stable"))
        assert status.priority == "NORMAL"

    def test_priority_watch_persistent(self):
        now = datetime.utcnow()
        deviations = []
        for i in range(PERSISTENT_WINDOWS):
            deviations.append(
                DeviationRecord(
                    case_id="watch",
                    feature_name="hr_mean",
                    timestamp=now + timedelta(minutes=i*WINDOW_MINUTES),
                    raw_value=75.0,
                    baseline_value=70.0,
                    z_score=Z_WATCH + 0.1,
                    persistence_count=i + 1,
                    change_detected=False,
                )
            )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = deviations
        mock_result.scalar_one_or_none.return_value = None
        db = AsyncMock()
        db.execute = AsyncMock(return_value=mock_result)
        db.get = AsyncMock(return_value=None)
        db.add = MagicMock()
        db.flush = AsyncMock()

        status = asyncio.get_event_loop().run_until_complete(compute_priority(db, "watch"))
        assert status.priority == "WATCH"

    def test_priority_high(self):
        now = datetime.utcnow()
        deviations = [
            DeviationRecord(
                case_id="high",
                feature_name="hr_mean",
                timestamp=now,
                raw_value=120.0,
                baseline_value=70.0,
                z_score=Z_HIGH + 1.0,
                persistence_count=PERSISTENT_WINDOWS,
                change_detected=True,
            )
            for _ in range(PERSISTENT_WINDOWS)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = deviations
        mock_result.scalar_one_or_none.return_value = None
        db = AsyncMock()
        db.execute = AsyncMock(return_value=mock_result)
        db.get = AsyncMock(return_value=None)
        db.add = MagicMock()
        db.flush = AsyncMock()

        status = asyncio.get_event_loop().run_until_complete(compute_priority(db, "high"))
        assert status.priority == "HIGH_PRIORITY"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestExplanationGeneration:
    def test_explain_high_priority(self):
        now = datetime.utcnow()
        deviations = [
            DeviationRecord(
                case_id="high",
                feature_name="hr_mean",
                timestamp=now,
                raw_value=120.0,
                baseline_value=70.0,
                z_score=Z_HIGH + 1.0,
                persistence_count=PERSISTENT_WINDOWS,
                change_detected=True,
            )
        ]
        explanation = _generate_explanation(
            priority="HIGH_PRIORITY",
            high_features={"hr_mean"},
            watch_features=set(),
            recent=deviations,
            latest_features={"hr_mean": {"raw_value": 120.0, "baseline_value": 70.0, "z_score": Z_HIGH + 1.0, "persistence_count": PERSISTENT_WINDOWS, "change_detected": True}},
        )
        assert "High priority alert" in explanation
        assert "heart rate" in explanation
        assert "persisted" in explanation

    def test_explain_watch(self):
        now = datetime.utcnow()
        deviations = [
            DeviationRecord(
                case_id="watch",
                feature_name="steps_count",
                timestamp=now,
                raw_value=100.0,
                baseline_value=5000.0,
                z_score=Z_WATCH + 0.1,
                persistence_count=PERSISTENT_WINDOWS,
                change_detected=False,
            )
        ]
        explanation = _generate_explanation(
            priority="WATCH",
            high_features=set(),
            watch_features={"steps_count"},
            recent=deviations,
            latest_features={"steps_count": {"raw_value": 100.0, "baseline_value": 5000.0, "z_score": Z_WATCH + 0.1, "persistence_count": PERSISTENT_WINDOWS, "change_detected": False}},
        )
        assert "Watch status" in explanation
        assert "activity level" in explanation

    def test_explain_normal(self):
        explanation = _generate_explanation(
            priority="NORMAL",
            high_features=set(),
            watch_features=set(),
            recent=[],
            latest_features={},
        )
        assert "No significant" in explanation

    def test_shap_explanation(self):
        now = datetime.utcnow()
        deviations = [
            DeviationRecord(
                case_id="shap",
                feature_name="hr_mean",
                timestamp=now,
                raw_value=120.0,
                baseline_value=70.0,
                z_score=3.0,
                persistence_count=1,
                change_detected=False,
            ),
            DeviationRecord(
                case_id="shap",
                feature_name="steps_count",
                timestamp=now,
                raw_value=100.0,
                baseline_value=5000.0,
                z_score=1.0,
                persistence_count=1,
                change_detected=False,
            ),
        ]
        shap = _generate_shap_explanation(deviations, {})
        assert "hr_mean" in shap
        assert "steps_count" in shap
        total = sum(shap.values())
        assert abs(total - 1.0) < 0.01


class TestAlertCreation:
    def test_compute_priority_creates_alert(self):
        now = datetime.utcnow()
        deviations = [
            DeviationRecord(
                case_id="high",
                feature_name="hr_mean",
                timestamp=now,
                raw_value=120.0,
                baseline_value=70.0,
                z_score=Z_HIGH + 1.0,
                persistence_count=PERSISTENT_WINDOWS,
                change_detected=True,
            )
            for _ in range(PERSISTENT_WINDOWS)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = deviations
        mock_result.scalar_one_or_none.return_value = None
        db = AsyncMock()
        db.execute = AsyncMock(return_value=mock_result)
        db.get = AsyncMock(return_value=None)
        db.add = MagicMock()
        db.flush = AsyncMock()

        status = asyncio.get_event_loop().run_until_complete(compute_priority(db, "high"))
        assert status.priority == "HIGH_PRIORITY"
        added_calls = db.add.call_args_list
        alert_added = any(
            len(call.args) == 1 and getattr(call.args[0], "__tablename__", None) == "alerts"
            for call in added_calls
        )
        assert alert_added

    def test_compute_priority_no_alert_for_normal(self):
        now = datetime.utcnow()
        deviations = []

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = deviations
        mock_result.scalar_one_or_none.return_value = None
        db = AsyncMock()
        db.execute = AsyncMock(return_value=mock_result)
        db.get = AsyncMock(return_value=None)
        db.add = MagicMock()
        db.flush = AsyncMock()

        status = asyncio.get_event_loop().run_until_complete(compute_priority(db, "stable"))
        assert status.priority == "NORMAL"
        added_calls = db.add.call_args_list
        alert_added = any(
            len(call.args) == 1 and getattr(call.args[0], "__tablename__", None) == "alerts"
            for call in added_calls
        )
        assert not alert_added


class TestAlertRetrieval:
    def test_list_alerts(self):
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "api"))
        from unittest.mock import AsyncMock, MagicMock
        from fastapi.testclient import TestClient
        from main import app
        from database import get_db

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)
        app.dependency_overrides[get_db] = lambda: mock_db

        client = TestClient(app)
        response = client.get("/api/v1/alerts")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

        app.dependency_overrides.clear()

    def test_get_alert_not_found(self):
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "api"))
        from unittest.mock import AsyncMock, MagicMock
        from fastapi.testclient import TestClient
        from main import app
        from database import get_db

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        app.dependency_overrides[get_db] = lambda: mock_db

        client = TestClient(app)
        response = client.get("/api/v1/alerts/999999")
        assert response.status_code == 404

        app.dependency_overrides.clear()


class TestPhase5Workflow:
    def test_alert_review_creates_audit(self):
        import sys
        import os
        from datetime import datetime
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "api"))
        from unittest.mock import AsyncMock, MagicMock
        from fastapi.testclient import TestClient
        from main import app
        from database import get_db
        from models.models import Alert, AlertReview, AuditLog

        mock_db = AsyncMock()
        alert = Alert(id=1, case_id="case1", priority="HIGH_PRIORITY", alert_type="HIGH_PRIORITY_REVIEW", status="OPEN", requires_counsellor_review=True)
        review = AlertReview(id=1, alert_id=1, case_id="case1", counsellor_id="c1", review_notes="ok", reviewed_at=datetime.utcnow())
        audit = AuditLog(id=1, case_id="case1", action="alert_reviewed", entity_type="alert", entity_id=1, details="{}", performed_by="c1", performed_at=datetime.utcnow())
        mock_db.get = AsyncMock(return_value=alert)

        def add_side_effect(obj):
            if isinstance(obj, AlertReview):
                obj.id = review.id
                obj.reviewed_at = review.reviewed_at
            elif isinstance(obj, AuditLog):
                obj.id = audit.id
                obj.performed_at = audit.performed_at

        mock_db.add = MagicMock(side_effect=add_side_effect)
        mock_db.flush = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        client = TestClient(app)
        response = client.post("/api/v1/alerts/1/review", json={"counsellor_id": "c1", "review_notes": "ok"})
        assert response.status_code == 200
        data = response.json()
        assert data["counsellor_id"] == "c1"
        assert data["review_notes"] == "ok"

        app.dependency_overrides.clear()

    def test_create_intervention_and_outcome(self):
        import sys
        import os
        from datetime import datetime
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "api"))
        from unittest.mock import AsyncMock, MagicMock
        from fastapi.testclient import TestClient
        from main import app
        from database import get_db
        from models.models import Intervention, Outcome

        mock_db = AsyncMock()
        intervention = Intervention(id=10, case_id="case1", category="counselling", status="PLANNED", created_by="c1", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
        outcome = Outcome(id=5, intervention_id=10, case_id="case1", outcome_notes="stable", recorded_by="c1", recorded_at=datetime.utcnow())
        mock_db.get = AsyncMock(side_effect=lambda model, id: intervention if model == Intervention and id == 10 else (outcome if model == Outcome and id == 5 else None))

        def add_side_effect(obj):
            if isinstance(obj, Intervention):
                obj.id = intervention.id
                obj.created_at = intervention.created_at
                obj.updated_at = intervention.updated_at
            elif isinstance(obj, Outcome):
                obj.id = outcome.id
                obj.recorded_at = outcome.recorded_at

        mock_db.add = MagicMock(side_effect=add_side_effect)
        mock_db.flush = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        client = TestClient(app)

        create_resp = client.post("/api/v1/interventions", json={
            "case_id": "case1",
            "alert_id": 1,
            "category": "counselling",
            "description": "initial session",
            "protocol_reference": "protocols/counselling.md",
            "status": "PLANNED",
            "created_by": "c1",
        })
        assert create_resp.status_code == 200
        created = create_resp.json()
        assert created["category"] == "counselling"

        outcome_resp = client.post("/api/v1/outcomes", json={
            "intervention_id": 10,
            "outcome_notes": "stable",
            "recorded_by": "c1",
        })
        assert outcome_resp.status_code == 200
        outcome_data = outcome_resp.json()
        assert outcome_data["outcome_notes"] == "stable"

        app.dependency_overrides.clear()

    def test_audit_logs_endpoint(self):
        import sys
        import os
        from datetime import datetime
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "api"))
        from unittest.mock import AsyncMock, MagicMock
        from fastapi.testclient import TestClient
        from main import app
        from database import get_db
        from models.models import AuditLog

        mock_db = AsyncMock()
        log = AuditLog(id=1, case_id="case1", action="alert_reviewed", entity_type="alert", entity_id=1, details="{}", performed_by="c1", performed_at=datetime.utcnow())
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [log]
        mock_db.execute = AsyncMock(return_value=mock_result)
        app.dependency_overrides[get_db] = lambda: mock_db

        client = TestClient(app)
        response = client.get("/api/v1/cases/case1/audit")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["action"] == "alert_reviewed"

        app.dependency_overrides.clear()

    def test_protocol_retrieval(self):
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "api"))
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.get("/api/v1/protocols/search?q=counselling&max_results=2")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) >= 1
        assert data["results"][0]["category"] == "counselling"

    def test_protocol_by_category(self):
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "api"))
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        response = client.get("/api/v1/protocols/counselling")
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "counselling"
        assert "source" in data
        assert "content" in data


class TestDemoMode:
    def test_demo_start_and_state(self):
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "api"))
        from unittest.mock import AsyncMock, MagicMock, patch
        from fastapi.testclient import TestClient
        from main import app
        from database import get_db

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.get = AsyncMock(return_value=None)
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        with patch('simulator.demo.AsyncSessionLocal') as mock_session_local:
            mock_session = AsyncMock()
            mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_local.return_value.__aexit__ = AsyncMock(return_value=False)
            app.dependency_overrides[get_db] = lambda: mock_db

            client = TestClient(app)
            start_resp = client.post("/api/v1/demo/start")
            assert start_resp.status_code == 200
            start_data = start_resp.json()
            assert start_data["case_id"] == "demo-case-001"
            assert start_data["phase"] == 0
            assert start_data["status"] == "started"

            state_resp = client.get("/api/v1/demo/state")
            assert state_resp.status_code == 200
            state_data = state_resp.json()
            assert state_data["case_id"] == "demo-case-001"
            assert state_data["phase"] == 0
            assert state_data["status"] == "not_started"

            app.dependency_overrides.clear()

    def test_demo_tick_progression(self):
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "api"))
        from unittest.mock import AsyncMock, MagicMock, patch
        from fastapi.testclient import TestClient
        from main import app
        from database import get_db

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.get = AsyncMock(return_value=None)
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        with patch('simulator.demo.AsyncSessionLocal') as mock_session_local, \
             patch('api.v1.demo.start_demo', return_value={"case_id": "demo-case-001", "phase": 0, "status": "started", "message": "Demo started."}), \
             patch('api.v1.demo.tick_demo', side_effect=[
                 {"case_id": "demo-case-001", "phase": 1, "status": "baseline_complete", "message": "Baseline complete.", "priority": "NORMAL", "details": "{}", "alert_count": 0, "readings_added": 100},
                 {"case_id": "demo-case-001", "phase": 2, "status": "watch_possible", "message": "Watch possible.", "priority": "WATCH", "details": "{}", "alert_count": 0, "readings_added": 50},
             ]) as mock_tick, \
             patch('api.v1.demo.reset_demo', return_value={"case_id": "demo-case-001", "status": "reset", "message": "Demo reset."}):
            mock_session = AsyncMock()
            mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_local.return_value.__aexit__ = AsyncMock(return_value=False)
            app.dependency_overrides[get_db] = lambda: mock_db

            client = TestClient(app)
            client.post("/api/v1/demo/start")

            tick1 = client.post("/api/v1/demo/tick")
            assert tick1.status_code == 200
            data1 = tick1.json()
            assert data1["phase"] == 1
            assert data1["status"] == "baseline_complete"

            tick2 = client.post("/api/v1/demo/tick")
            assert tick2.status_code == 200
            data2 = tick2.json()
            assert data2["phase"] == 2
            assert data2["status"] == "watch_possible"

            client.post("/api/v1/demo/reset")

        app.dependency_overrides.clear()

    def test_demo_reset(self):
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "api"))
        from unittest.mock import AsyncMock, MagicMock, patch
        from fastapi.testclient import TestClient
        from main import app
        from database import get_db

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.get = AsyncMock(return_value=None)
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        mock_db.commit = AsyncMock()

        with patch('simulator.demo.AsyncSessionLocal') as mock_session_local, \
             patch('api.v1.demo.start_demo', return_value={"case_id": "demo-case-001", "phase": 0, "status": "started", "message": "Demo started."}), \
             patch('api.v1.demo.tick_demo', return_value={"case_id": "demo-case-001", "phase": 1, "status": "baseline_complete", "message": "Baseline complete.", "priority": "NORMAL", "details": "{}", "alert_count": 0, "readings_added": 100}), \
             patch('api.v1.demo.reset_demo', return_value={"case_id": "demo-case-001", "status": "reset", "message": "Demo reset."}), \
             patch('api.v1.demo.get_demo_state', return_value={"case_id": "demo-case-001", "phase": 0, "status": "not_started"}):
            mock_session = AsyncMock()
            mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            mock_session_local.return_value.__aexit__ = AsyncMock(return_value=False)
            app.dependency_overrides[get_db] = lambda: mock_db

            client = TestClient(app)
            client.post("/api/v1/demo/start")
            client.post("/api/v1/demo/tick")

            reset_resp = client.post("/api/v1/demo/reset")
            assert reset_resp.status_code == 200
            assert reset_resp.json()["status"] == "reset"

            state_resp = client.get("/api/v1/demo/state")
            assert state_resp.json()["phase"] == 0

            app.dependency_overrides.clear()

    def test_cases_list_endpoint(self):
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "services", "api"))
        from unittest.mock import AsyncMock, MagicMock
        from fastapi.testclient import TestClient
        from main import app
        from database import get_db
        from models.models import CaseStatus

        mock_db = AsyncMock()
        case1 = CaseStatus(case_id="case1", priority="NORMAL", computed_at=datetime.utcnow())
        case2 = CaseStatus(case_id="case2", priority="HIGH_PRIORITY", computed_at=datetime.utcnow())
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [case1, case2]
        mock_db.execute = AsyncMock(return_value=mock_result)
        app.dependency_overrides[get_db] = lambda: mock_db

        client = TestClient(app)
        response = client.get("/api/v1/cases")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["case_id"] == "case1"
        assert data[1]["priority"] == "HIGH_PRIORITY"

        app.dependency_overrides.clear()
