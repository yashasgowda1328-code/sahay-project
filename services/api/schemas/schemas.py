from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any


class WearableReadingIn(BaseModel):
    case_id: str
    timestamp: datetime
    heart_rate: float
    steps_increment: int = 0
    activity_level: str = "sedentary"
    is_inactive: bool = True


class WearableReadingBatch(BaseModel):
    case_id: str
    readings: List[WearableReadingIn]


class FeatureOut(BaseModel):
    id: int
    case_id: str
    timestamp: datetime
    window_minutes: int
    hr_mean: Optional[float]
    hr_std: Optional[float]
    hr_median: Optional[float]
    hr_mad: Optional[float]
    hr_min: Optional[float]
    hr_max: Optional[float]
    hr_trend: Optional[float]
    signal_quality: Optional[float]
    steps_count: int
    active_minutes: float
    inactive_minutes: float
    active_ratio: float
    consecutive_inactive_windows: int


class BaselineOut(BaseModel):
    id: int
    case_id: str
    computed_at: datetime
    window: str
    hr_mean: Optional[float]
    hr_median: Optional[float]
    hr_mad: Optional[float]
    hr_std: Optional[float]
    steps_mean: Optional[float]
    steps_median: Optional[float]
    active_ratio_mean: Optional[float]
    active_ratio_median: Optional[float]
    inactive_minutes_mean: Optional[float]
    inactive_minutes_median: Optional[float]
    sample_count: int


class DeviationOut(BaseModel):
    id: int
    case_id: str
    feature_name: str
    timestamp: datetime
    raw_value: float
    baseline_value: Optional[float]
    absolute_deviation: Optional[float]
    percentage_deviation: Optional[float]
    ewma: Optional[float]
    deviation: Optional[float]
    z_score: Optional[float]
    persistence_count: int
    change_detected: bool


class CaseStatusOut(BaseModel):
    case_id: str
    priority: str
    computed_at: datetime
    details: Optional[str]
    current_features: Optional[str]


class AnalysisHistoryOut(BaseModel):
    id: int
    case_id: str
    priority: str
    computed_at: datetime
    details: Optional[str]
    feature_snapshot: Optional[str]
    baseline_snapshot: Optional[str]
    explanation: Optional[str]


class AlertOut(BaseModel):
    id: int
    case_id: str
    priority: str
    alert_type: str
    status: str
    explanation: Optional[str]
    details: Optional[str]
    feature_snapshot: Optional[str]
    baseline_snapshot: Optional[str]
    requires_counsellor_review: bool
    created_at: datetime
    updated_at: datetime


class AlertCreate(BaseModel):
    case_id: str
    priority: str
    explanation: Optional[str] = None
    details: Optional[str] = None
    feature_snapshot: Optional[str] = None
    baseline_snapshot: Optional[str] = None
    requires_counsellor_review: bool = True


class AlertReviewCreate(BaseModel):
    counsellor_id: str
    review_notes: Optional[str] = None


class AlertReviewOut(BaseModel):
    id: int
    alert_id: int
    case_id: str
    counsellor_id: str
    review_notes: Optional[str]
    reviewed_at: datetime


class InterventionCreate(BaseModel):
    case_id: str
    alert_id: Optional[int] = None
    category: str
    description: Optional[str] = None
    protocol_reference: Optional[str] = None
    status: str = "PLANNED"
    created_by: str


class InterventionOut(BaseModel):
    id: int
    case_id: str
    alert_id: Optional[int]
    category: str
    description: Optional[str]
    protocol_reference: Optional[str]
    status: str
    created_by: str
    created_at: datetime
    updated_at: datetime


class OutcomeCreate(BaseModel):
    intervention_id: int
    outcome_notes: Optional[str] = None
    recorded_by: str


class OutcomeOut(BaseModel):
    id: int
    intervention_id: int
    case_id: str
    outcome_notes: Optional[str]
    recorded_by: str
    recorded_at: datetime


class AuditLogOut(BaseModel):
    id: int
    case_id: str
    action: str
    entity_type: str
    entity_id: int
    details: Optional[str]
    performed_by: str
    performed_at: datetime


class CaseStatusResponse(BaseModel):
    case_id: str
    priority: str
    computed_at: datetime
    details: Optional[str]
    current_features: Optional[Dict[str, Any]]
    baseline: Optional[Dict[str, Any]]
    deviations: List[DeviationOut] = []


class RoleOut(BaseModel):
    id: int
    name: str
    description: Optional[str]


class DistrictOut(BaseModel):
    id: int
    name: str
    state: str
    is_active: bool


class UserLogin(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role_name: str
    district_name: Optional[str] = None


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role_name: str
    district_name: Optional[str]
    is_active: bool


class CounsellorOut(BaseModel):
    id: int
    user_id: int
    full_name: str
    designation: Optional[str]
    department: Optional[str]
    district_name: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    assigned_date: Optional[datetime]
    active_cases: int
    sessions_completed: int


class ConsentOut(BaseModel):
    id: int
    case_id: str
    status: str
    consent_date: Optional[datetime]
    consent_version: Optional[str]
    recorded_by: Optional[str]
    notes: Optional[str]


class CounsellingSessionIn(BaseModel):
    case_id: str
    counsellor_id: str
    session_type: str
    duration_minutes: Optional[int] = None
    status: str = "completed"
    summary: Optional[str] = None
    next_follow_up_date: Optional[datetime] = None


class CounsellingSessionOut(BaseModel):
    id: int
    case_id: str
    counsellor_id: str
    session_type: str
    duration_minutes: Optional[int]
    status: str
    summary: Optional[str]
    next_follow_up_date: Optional[datetime]
    created_at: datetime


class FollowUpIn(BaseModel):
    case_id: str
    counsellor_id: str
    purpose: Optional[str] = None
    status: str = "scheduled"
    notes: Optional[str] = None
    due_date: Optional[datetime] = None


class FollowUpOut(BaseModel):
    id: int
    case_id: str
    counsellor_id: str
    purpose: Optional[str]
    status: str
    notes: Optional[str]
    due_date: Optional[datetime]
    created_at: datetime


class DashboardMetrics(BaseModel):
    total_cases: int
    high_priority: int
    watch: int
    normal: int
    active_monitoring: int
    open_alerts: int
    follow_ups_due: int


class DistrictMetrics(DashboardMetrics):
    district_name: str
    counsellors: int


class CaseSummary(BaseModel):
    case_id: str
    person_name: str
    case_type: str
    age: Optional[int]
    district: Optional[str]
    state: Optional[str]
    assigned_counsellor: Optional[str]
    priority: str
    monitoring_status: Optional[str]
    consent_status: Optional[str]
    case_opened: Optional[datetime]
    last_counselling: Optional[datetime]
    next_follow_up: Optional[datetime]
    last_reading: Optional[datetime]


class CaseDetailResponse(BaseModel):
    case_id: str
    person_name: str
    case_type: str
    age: Optional[int]
    district: Optional[str]
    state: Optional[str]
    assigned_counsellor: Optional[str]
    priority: str
    monitoring_status: Optional[str]
    consent_status: Optional[str]
    case_opened: Optional[datetime]
    last_counselling: Optional[datetime]
    next_follow_up: Optional[datetime]
    last_reading: Optional[datetime]
    baseline: Optional[Dict[str, Any]]
    current_features: Optional[Dict[str, Any]]
    deviations: List[DeviationOut] = []
    explanation: Optional[str]
    alerts: List[AlertOut] = []
    interventions: List[InterventionOut] = []
    counselling_sessions: List[CounsellingSessionOut] = []
    follow_ups: List[FollowUpOut] = []
    audit_logs: List[AuditLogOut] = []
