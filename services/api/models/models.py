from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime


class Base(DeclarativeBase):
    pass


class WearableReading(Base):
    __tablename__ = "wearable_readings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True)
    timestamp: Mapped[datetime] = mapped_column(index=True)
    heart_rate: Mapped[float] = mapped_column(Float)
    steps_increment: Mapped[int] = mapped_column(Integer, default=0)
    activity_level: Mapped[str] = mapped_column(String(32), default="sedentary")
    is_inactive: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class ExtractedFeature(Base):
    __tablename__ = "extracted_features"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True)
    timestamp: Mapped[datetime] = mapped_column(index=True)
    window_minutes: Mapped[int] = mapped_column(Integer, default=15)
    hr_mean: Mapped[float] = mapped_column(Float, nullable=True)
    hr_std: Mapped[float] = mapped_column(Float, nullable=True)
    hr_median: Mapped[float] = mapped_column(Float, nullable=True)
    hr_mad: Mapped[float] = mapped_column(Float, nullable=True)
    hr_min: Mapped[float] = mapped_column(Float, nullable=True)
    hr_max: Mapped[float] = mapped_column(Float, nullable=True)
    hr_trend: Mapped[float] = mapped_column(Float, nullable=True)
    signal_quality: Mapped[float] = mapped_column(Float, nullable=True)
    steps_count: Mapped[int] = mapped_column(Integer, default=0)
    active_minutes: Mapped[float] = mapped_column(Float, default=0.0)
    inactive_minutes: Mapped[float] = mapped_column(Float, default=0.0)
    active_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    consecutive_inactive_windows: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class PersonalBaseline(Base):
    __tablename__ = "personal_baselines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    computed_at: Mapped[datetime] = mapped_column(server_default=func.now())
    window: Mapped[str] = mapped_column(String(32), default="7d")
    hr_mean: Mapped[float] = mapped_column(Float, nullable=True)
    hr_median: Mapped[float] = mapped_column(Float, nullable=True)
    hr_mad: Mapped[float] = mapped_column(Float, nullable=True)
    hr_std: Mapped[float] = mapped_column(Float, nullable=True)
    steps_mean: Mapped[float] = mapped_column(Float, nullable=True)
    steps_median: Mapped[float] = mapped_column(Float, nullable=True)
    active_ratio_mean: Mapped[float] = mapped_column(Float, nullable=True)
    active_ratio_median: Mapped[float] = mapped_column(Float, nullable=True)
    inactive_minutes_mean: Mapped[float] = mapped_column(Float, nullable=True)
    inactive_minutes_median: Mapped[float] = mapped_column(Float, nullable=True)
    sample_count: Mapped[int] = mapped_column(Integer, default=0)


class DeviationRecord(Base):
    __tablename__ = "deviation_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True)
    feature_name: Mapped[str] = mapped_column(String(64), index=True)
    timestamp: Mapped[datetime] = mapped_column(index=True)
    raw_value: Mapped[float] = mapped_column(Float)
    baseline_value: Mapped[float] = mapped_column(Float, nullable=True)
    absolute_deviation: Mapped[float] = mapped_column(Float, nullable=True)
    percentage_deviation: Mapped[float] = mapped_column(Float, nullable=True)
    ewma: Mapped[float] = mapped_column(Float, nullable=True)
    deviation: Mapped[float] = mapped_column(Float, nullable=True)
    z_score: Mapped[float] = mapped_column(Float, nullable=True)
    persistence_count: Mapped[int] = mapped_column(Integer, default=0)
    change_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class CaseStatus(Base):
    __tablename__ = "case_status"

    case_id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    priority: Mapped[str] = mapped_column(String(32), default="NORMAL", index=True)
    computed_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    details: Mapped[str] = mapped_column(Text, nullable=True)
    current_features: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    person_name: Mapped[str] = mapped_column(String(128), nullable=True)
    age: Mapped[int] = mapped_column(Integer, nullable=True)
    case_type: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    district: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    state: Mapped[str] = mapped_column(String(64), nullable=True, default="Karnataka")
    assigned_counsellor_id: Mapped[str] = mapped_column(String(64), nullable=True, index=True)
    consent_status: Mapped[str] = mapped_column(String(32), nullable=True, default="pending")
    consent_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    consent_version: Mapped[str] = mapped_column(String(32), nullable=True)
    consent_recorded_by: Mapped[str] = mapped_column(String(64), nullable=True)
    monitoring_status: Mapped[str] = mapped_column(String(32), nullable=True, default="active")
    last_counselling_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    next_follow_up_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    case_opened_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True)
    priority: Mapped[str] = mapped_column(String(32), index=True)
    computed_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    details: Mapped[str] = mapped_column(Text, nullable=True)
    feature_snapshot: Mapped[str] = mapped_column(Text, nullable=True)
    baseline_snapshot: Mapped[str] = mapped_column(Text, nullable=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=True)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True)
    priority: Mapped[str] = mapped_column(String(32), index=True)
    alert_type: Mapped[str] = mapped_column(String(64), default="HIGH_PRIORITY_REVIEW")
    status: Mapped[str] = mapped_column(String(32), default="OPEN", index=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=True)
    details: Mapped[str] = mapped_column(Text, nullable=True)
    feature_snapshot: Mapped[str] = mapped_column(Text, nullable=True)
    baseline_snapshot: Mapped[str] = mapped_column(Text, nullable=True)
    requires_counsellor_review: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class AlertReview(Base):
    __tablename__ = "alert_reviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    alert_id: Mapped[int] = mapped_column(Integer, ForeignKey("alerts.id"), index=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True)
    counsellor_id: Mapped[str] = mapped_column(String(64))
    review_notes: Mapped[str] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)


class Intervention(Base):
    __tablename__ = "interventions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True)
    alert_id: Mapped[int] = mapped_column(Integer, ForeignKey("alerts.id"), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    protocol_reference: Mapped[str] = mapped_column(String(256), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="PLANNED", index=True)
    created_by: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class Outcome(Base):
    __tablename__ = "outcomes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    intervention_id: Mapped[int] = mapped_column(Integer, ForeignKey("interventions.id"), index=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True)
    outcome_notes: Mapped[str] = mapped_column(Text, nullable=True)
    outcome_status: Mapped[str] = mapped_column(String(32), nullable=True)
    recorded_by: Mapped[str] = mapped_column(String(64))
    recorded_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    entity_id: Mapped[int] = mapped_column(Integer, index=True)
    details: Mapped[str] = mapped_column(Text, nullable=True)
    performed_by: Mapped[str] = mapped_column(String(64))
    performed_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)


class DemoState(Base):
    __tablename__ = "demo_state"

    id: Mapped[int] = mapped_column(primary_key=True)
    phase: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(128), nullable=True)


class District(Base):
    __tablename__ = "districts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    state: Mapped[str] = mapped_column(String(64), default="Karnataka")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(256))
    full_name: Mapped[str] = mapped_column(String(128))
    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id"), index=True)
    district_id: Mapped[int] = mapped_column(Integer, ForeignKey("districts.id"), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Counsellor(Base):
    __tablename__ = "counsellors"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, index=True)
    designation: Mapped[str] = mapped_column(String(64), nullable=True)
    department: Mapped[str] = mapped_column(String(64), nullable=True)
    district_id: Mapped[int] = mapped_column(Integer, ForeignKey("districts.id"), nullable=True, index=True)
    phone: Mapped[str] = mapped_column(String(32), nullable=True)
    email: Mapped[str] = mapped_column(String(128), nullable=True)
    assigned_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    active_cases: Mapped[int] = mapped_column(Integer, default=0)
    sessions_completed: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Consent(Base):
    __tablename__ = "consents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    consent_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    consent_version: Mapped[str] = mapped_column(String(32), nullable=True)
    recorded_by: Mapped[str] = mapped_column(String(64), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class CounsellingSession(Base):
    __tablename__ = "counselling_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True)
    counsellor_id: Mapped[str] = mapped_column(String(64), index=True)
    session_type: Mapped[str] = mapped_column(String(32))
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="completed")
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    next_follow_up_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    case_id: Mapped[str] = mapped_column(String(64), index=True)
    counsellor_id: Mapped[str] = mapped_column(String(64), index=True)
    purpose: Mapped[str] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="scheduled")
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
