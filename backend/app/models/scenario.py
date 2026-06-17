"""Pydantic models for the matching platform."""

from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class ScenarioStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"


class FieldType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    SLIDER = "slider"
    DATE = "date"
    TAG_INPUT = "tag_input"
    CONTACT = "contact"  # WeChat/phone/QQ — required in every scenario


class FormField(BaseModel):
    key: str
    type: FieldType
    label: str
    required: bool = True
    placeholder: Optional[str] = None
    options: Optional[list[str]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None


class FormSchema(BaseModel):
    fields: list[FormField]


class MatchConfig(BaseModel):
    embedding_source: str = "composite"
    embedding_fields: list[str] = Field(default_factory=list)
    filter_fields: list[str] = Field(default_factory=list)
    weight_fields: dict[str, float] = Field(default_factory=dict)
    top_k: int = 10
    min_similarity: float = 0.7


class UIConfig(BaseModel):
    theme_color: str = "#1a1a2e"
    card_layout: str = "grid"
    result_display: list[str] = Field(default_factory=lambda: ["name", "similarity_score"])


# --- Scenario ---

class ScenarioCreate(BaseModel):
    name: str
    description: str = ""
    form_schema: FormSchema
    match_config: MatchConfig = MatchConfig()
    ui_config: UIConfig = UIConfig()
    status: ScenarioStatus = ScenarioStatus.DRAFT


class ScenarioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    form_schema: Optional[FormSchema] = None
    match_config: Optional[MatchConfig] = None
    ui_config: Optional[UIConfig] = None
    status: Optional[ScenarioStatus] = None


class ScenarioResponse(BaseModel):
    id: str
    creator_id: str
    name: str
    description: str
    form_schema: FormSchema
    match_config: MatchConfig
    ui_config: UIConfig
    status: ScenarioStatus
    created_at: str
    submission_count: int = 0


# --- Submission ---

class SubmissionCreate(BaseModel):
    scenario_id: str
    form_data: dict[str, Any]


class SubmissionResponse(BaseModel):
    id: str
    scenario_id: str
    user_id: str
    form_data: dict[str, Any]
    created_at: str


# --- Matching ---

class MatchResultItem(BaseModel):
    submission_id: str
    matched_submission_id: str
    similarity_score: float
    matched_user_name: str
    matched_form_data: dict[str, Any]
    explanation: str = ""


class MatchResponse(BaseModel):
    submission_id: str
    matches: list[MatchResultItem]


# --- AI Generation ---

class GenerateScenarioRequest(BaseModel):
    prompt: str
    """Natural language description of the matching scenario."""


class GenerateScenarioResponse(BaseModel):
    name: str
    description: str
    form_schema: FormSchema
    match_config: MatchConfig
    ui_config: UIConfig


# --- Stats ---

class ScenarioStats(BaseModel):
    scenario_id: str
    scenario_name: str
    submission_count: int
    match_count: int
    status: ScenarioStatus


# --- Auth ---

class UserRegister(BaseModel):
    email: str
    username: str
    password: str
    contact_info: str = Field(..., min_length=1, description="微信号/手机号/QQ号 — 必填")
    role: str = "participant"  # participant | designer


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    model_config = {"extra": "ignore"}
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    model_config = {"extra": "ignore"}
    id: str
    email: str
    username: str
    role: str
    contact_info: str = ""
    tags: list[str] = []
    created_at: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    contact_info: Optional[str] = None
    tags: Optional[list[str]] = None


class AdminStatsResponse(BaseModel):
    total_scenarios: int
    active_scenarios: int
    total_users: int
    users_by_role: dict[str, int]
    total_submissions: int
    total_matches: int
    recent_users_7d: int
    recent_submissions_7d: int
