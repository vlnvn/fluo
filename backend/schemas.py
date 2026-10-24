"""Versioned HTTP schemas; oracle labels are forbidden at inference boundaries."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class Telemetry(StrictModel):
    timestamp: datetime
    site_id: str = Field(min_length=1, max_length=40)
    minute_id: int = Field(ge=0)
    split: str = Field(min_length=1, max_length=40)
    operating_mode: Literal['production', 'startup', 'shutdown', 'idle']
    throughput_index: float | None
    steam_flow_obs_kg_h: float | None = Field(ge=0)
    condensate_return_obs_kg_h: float | None = Field(ge=0)
    steam_pressure_obs_barg: float | None
    steam_temperature_obs_C: float | None
    return_temperature_obs_C: float | None
    link_online: Literal[0, 1]
    data_quality_flag: str = Field(min_length=1, max_length=80)

    @field_validator('timestamp')
    @classmethod
    def require_timezone(cls, value):
        if value.tzinfo is None:
            raise ValueError('timestamp must include a timezone')
        return value


class InferenceRequest(StrictModel):
    rows: list[Telemetry] = Field(min_length=1, max_length=5000)
    run_mode: Literal['SYNTHETIC_REPLAY'] = 'SYNTHETIC_REPLAY'


class CreateSession(StrictModel):
    scenario_id: str = 'return-diversion'


class ReplayCommand(StrictModel):
    action: Literal['play', 'pause', 'reset', 'rewind', 'forward', 'seek', 'speed', 'scenario']
    cursor: int | None = Field(default=None, ge=0)
    speed: Literal[1, 2] | None = None
    scenario_id: str | None = None


class Readings(StrictModel):
    steam_kg_h: float | None
    return_kg_h: float | None
    pressure_barg: float | None
    steam_temperature_C: float | None
    return_temperature_C: float | None


class InferenceResult(StrictModel):
    score: float | None
    warning: bool
    persistence_hits: int
    triage_status: str
    score_meaning: str
    next_safe_action: str
    recovery_eligibility: Literal['UNKNOWN_REQUIRES_SITE_ASSESSMENT']
    auto_actuation_allowed: Literal[False]
    fixed_ratio_warning: bool
    physics_residual_warning: bool


class Frame(StrictModel):
    timestamp: str
    minute_id: int
    site_id: str
    operating_mode: str
    link_online: bool
    data_quality_flag: str
    quality_action: str
    readings: Readings
    inference: InferenceResult


class Scenario(StrictModel):
    id: str
    name: str
    group: str
    description: str
    site_id: str
    start_timestamp: str
    end_timestamp: str
    total_frames: int
    default_cursor: int
    source_kind: Literal['simulated research telemetry']
    setup_is_not_diagnosis: Literal[True]


class Lineage(StrictModel):
    model_sha256: str
    dataset_sha256: str
    model: str
    source_kind: Literal['simulated research telemetry']
    sample_period_seconds: Literal[60]
    replay_seconds_per_sample_at_1x: Literal[1]
    field_validation: Literal[False]
    facility_is_fictional: Literal[True]


class Event(StrictModel):
    id: str
    site_id: str
    timestamp: str
    end_timestamp: str
    category: Literal['return', 'quality']
    title: str
    state: str
    duration_min: int
    minute_id: int
    peak_score: float | None
    evidence: list[str]
    review_status: str = 'pending'


class SessionState(StrictModel):
    schema_version: Literal['1.0']
    session_id: str
    scenario: Scenario
    cursor: int
    speed: Literal[1, 2]
    playback: Literal['PLAYING', 'PAUSED', 'ENDED']
    current: Frame
    frames: list[Frame]
    events: list[Event]
    active_event_id: str | None
    lineage: Lineage
    review_scope: str


class ReviewStep(StrictModel):
    step_id: str
    label: str
    checked: bool = False
    evidence: str = Field(default='', max_length=1000)


class ReviewUpdate(StrictModel):
    checked_steps: list[str] = Field(max_length=4)
    note: str = Field(default='', max_length=2000)
    revision: int = Field(ge=0)


class PreferencesUpdate(StrictModel):
    warning_sound: bool


class Review(StrictModel):
    event_id: str
    operator_id: str
    operator_label: Literal['Local operator (unverified)']
    authenticated: Literal[False]
    revision: int
    status: Literal['draft', 'submitted', 'pending']
    steps: list[ReviewStep]
    note: str
    updated_at: str | None
    submitted_at: str | None
    audit: list[dict]


class EventDetail(StrictModel):
    event: Event
    frame: Frame
    context: list[Frame]
    review: Review
    lineage: Lineage
    limitations: list[str]
