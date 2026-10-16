from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Versioned(APIModel):
    id: str | None = None
    tenant_id: str = "demo"
    data_mode: str = "LIVE"
    version: int = 1
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserBase(APIModel):
    name: str
    role: str
    phone: str | None = None
    language: str | None = None
    age_band: str | None = None
    interests: list[str] | None = None


class UserCreate(UserBase):
    pass


class UserResponse(Versioned, UserBase):
    pass


class StudentBase(APIModel):
    user_id: str
    age_band: str
    interests: list[str] | None = None
    safeguarding_status: str | None = None


class StudentCreate(StudentBase):
    pass


class StudentResponse(Versioned, StudentBase):
    pass


class SkillFamilyBase(APIModel):
    slug: str
    canonical_name: str
    aliases: dict[str, Any] | None = None


class SkillFamilyCreate(SkillFamilyBase):
    pass


class SkillFamilyResponse(Versioned, SkillFamilyBase):
    pass


class DemandTicketBase(APIModel):
    employer_name: str
    employer_contact: str | None = None
    source_type: str
    audio_key: str | None = None
    transcript_original: str | None = None
    transcript_language: str | None = None
    extraction_method: str | None = None
    proposed_fields: dict[str, Any] | None = None
    missing_fields: list[str] | None = None
    demand_type: str
    confirmed_skill_id: str | None = None
    slots_confirmed: int = 0
    pay_min_minor: int | None = None
    pay_max_minor: int | None = None
    pay_period: str | None = None
    location_text: str | None = None
    block_code: str | None = None
    duration_days: int | None = None
    min_age: int | None = None
    max_age: int | None = None
    valid_until: date | None = None
    status: str = "needs_confirmation"
    confirmed_by: str | None = None
    confirmed_at: datetime | None = None
    pod_id: str | None = None


class DemandTicketCreate(DemandTicketBase):
    pass


class DemandTicketResponse(Versioned, DemandTicketBase):
    pass


class PodBase(APIModel):
    name: str
    skill_family_id: str
    block_code: str
    threshold_slots: int
    confirmed_slots: int = 0
    pod_mode: str
    status: str = "open"
    module_id: str | None = None
    facilitator_user_id: str | None = None


class PodCreate(PodBase):
    pass


class PodResponse(Versioned, PodBase):
    pass


class PodEnrolmentBase(APIModel):
    pod_id: str
    student_id: str
    status: str = "active"


class PodEnrolmentCreate(PodEnrolmentBase):
    pass


class PodEnrolmentResponse(Versioned, PodEnrolmentBase):
    pass


class ModuleBase(APIModel):
    title: str
    skill_family_id: str | None = None
    content_json: dict[str, Any] | None = None
    status: str = "draft"


class ModuleCreate(ModuleBase):
    pass


class ModuleResponse(Versioned, ModuleBase):
    pass


class TaskSubmissionBase(APIModel):
    task_id: str
    pod_id: str
    student_id: str
    submission_json: dict[str, Any] | None = None
    status: str = "submitted"


class TaskSubmissionCreate(TaskSubmissionBase):
    pass


class TaskSubmissionResponse(Versioned, TaskSubmissionBase):
    pass


class OutcomeEventCreate(APIModel):
    event_type: str
    subject_type: str
    subject_id: str
    payload: dict[str, Any] | None = None
    occurred_at: datetime | None = None


class OutcomeEventResponse(Versioned, OutcomeEventCreate):
    occurred_at: datetime


class KnowledgeRecordBase(APIModel):
    record_type: str
    title: str
    authority: str | None = None
    description: str | None = None
    source_url: str | None = None
    last_checked_at: date | None = None
    skill_family_ids: list[str] | None = None
    language_codes: list[str] | None = None
    eligibility_json: dict[str, Any] | None = None
    benefits_json: dict[str, Any] | None = None
    verification_status: str
    valid_until: date | None = None


class KnowledgeRecordCreate(KnowledgeRecordBase):
    pass


class KnowledgeRecordResponse(Versioned, KnowledgeRecordBase):
    pass


class SyncReceiptCreate(APIModel):
    client_op_id: str
    result_json: dict[str, Any] | None = None


class SyncReceiptResponse(Versioned, SyncReceiptCreate):
    pass


class SyncOperation(APIModel):
    client_op_id: str
    entity: str
    operation: str
    payload: dict[str, Any] = Field(default_factory=dict)


class SyncRequest(APIModel):
    operations: list[SyncOperation] = Field(default_factory=list)


class SyncResponse(APIModel):
    receipts: list[SyncReceiptResponse] = Field(default_factory=list)


class HealthResponse(APIModel):
    status: str = "ok"


class Actor(APIModel):
    id: str
    name: str
    role: str
