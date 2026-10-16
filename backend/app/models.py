from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CommonModel(Base):
    __abstract__ = True

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    tenant_id: Mapped[str] = mapped_column(String(100), default="demo", nullable=False, index=True)
    data_mode: Mapped[str] = mapped_column(String(20), default="LIVE", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class User(CommonModel):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50))
    language: Mapped[str | None] = mapped_column(String(20))
    age_band: Mapped[str | None] = mapped_column(String(30))
    interests: Mapped[list[str] | None] = mapped_column(JSON)


class Student(CommonModel):
    __tablename__ = "students"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, unique=True)
    age_band: Mapped[str] = mapped_column(String(30), nullable=False)
    interests: Mapped[list[str] | None] = mapped_column(JSON)
    safeguarding_status: Mapped[str | None] = mapped_column(String(50))


class SkillFamily(CommonModel):
    __tablename__ = "skill_families"

    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    canonical_name: Mapped[str] = mapped_column(String(200), nullable=False)
    aliases: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class DemandTicket(CommonModel):
    __tablename__ = "demand_tickets"

    employer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    employer_contact: Mapped[str | None] = mapped_column(String(200))
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    audio_key: Mapped[str | None] = mapped_column(String(500))
    transcript_original: Mapped[str | None] = mapped_column(Text)
    transcript_language: Mapped[str | None] = mapped_column(String(20))
    extraction_method: Mapped[str | None] = mapped_column(String(50))
    proposed_fields: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    missing_fields: Mapped[list[str] | None] = mapped_column(JSON)
    demand_type: Mapped[str] = mapped_column(String(50), nullable=False)
    confirmed_skill_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("skill_families.id"))
    slots_confirmed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pay_min_minor: Mapped[int | None] = mapped_column(Integer)
    pay_max_minor: Mapped[int | None] = mapped_column(Integer)
    pay_period: Mapped[str | None] = mapped_column(String(30))
    location_text: Mapped[str | None] = mapped_column(String(300))
    block_code: Mapped[str | None] = mapped_column(String(100))
    duration_days: Mapped[int | None] = mapped_column(Integer)
    min_age: Mapped[int | None] = mapped_column(Integer)
    max_age: Mapped[int | None] = mapped_column(Integer)
    valid_until: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    confirmed_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pod_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("pods.id"))
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class Pod(CommonModel):
    __tablename__ = "pods"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    skill_family_id: Mapped[str] = mapped_column(String(36), ForeignKey("skill_families.id"), nullable=False)
    block_code: Mapped[str] = mapped_column(String(100), nullable=False)
    threshold_slots: Mapped[int] = mapped_column(Integer, nullable=False)
    confirmed_slots: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pod_mode: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    module_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("modules.id"))
    facilitator_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class PodEnrolment(CommonModel):
    __tablename__ = "pod_enrolments"
    __table_args__ = (UniqueConstraint("pod_id", "student_id", name="uq_pod_student"),)

    pod_id: Mapped[str] = mapped_column(String(36), ForeignKey("pods.id"), nullable=False)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)


class Module(CommonModel):
    __tablename__ = "modules"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    skill_family_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("skill_families.id"))
    content_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class TaskSubmission(CommonModel):
    __tablename__ = "task_submissions"

    task_id: Mapped[str] = mapped_column(String(100), nullable=False)
    pod_id: Mapped[str] = mapped_column(String(36), ForeignKey("pods.id"), nullable=False)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("students.id"), nullable=False)
    submission_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(50), default="submitted", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class OutcomeEvent(CommonModel):
    __tablename__ = "outcome_events"

    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_type: Mapped[str] = mapped_column(String(100), nullable=False)
    subject_id: Mapped[str] = mapped_column(String(36), nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class KnowledgeRecord(CommonModel):
    __tablename__ = "knowledge_records"

    record_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    authority: Mapped[str | None] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(1000))
    last_checked_at: Mapped[date | None] = mapped_column(Date)
    skill_family_ids: Mapped[list[str] | None] = mapped_column(JSON)
    language_codes: Mapped[list[str] | None] = mapped_column(JSON)
    eligibility_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    benefits_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    verification_status: Mapped[str] = mapped_column(String(50), nullable=False)
    valid_until: Mapped[date | None] = mapped_column(Date)


class SyncReceipt(CommonModel):
    __tablename__ = "sync_receipts"
    __table_args__ = (UniqueConstraint("client_op_id", name="uq_sync_client_op_id"),)

    client_op_id: Mapped[str] = mapped_column(String(200), nullable=False)
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON)
