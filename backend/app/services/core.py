"""Shared business operations used by HTTP and offline sync adapters."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import select

from ..models import (
    DemandTicket,
    KnowledgeRecord,
    Module,
    OutcomeEvent,
    Pod,
    PodEnrolment,
    SkillFamily,
    Student,
    TaskSubmission,
    User,
)
from . import extractor, llm


def create_ticket(db: Session, values: dict[str, Any], actor: User) -> DemandTicket:
    row = DemandTicket(
        id=values.get("id"),
        employer_name=values["employer_name"],
        employer_contact=values.get("employer_contact"),
        source_type=values["source_type"],
        transcript_original=values.get("transcript_original"),
        transcript_language=values.get("transcript_language"),
        demand_type="unknown",
        status="draft",
        data_mode="LIVE",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_ticket_draft(
    db: Session,
    row: DemandTicket,
    values: dict[str, Any],
    base_version: int | None,
) -> DemandTicket:
    if row.status == "confirmed":
        raise ValueError("Ticket is already confirmed")
    if base_version is not None and row.version != base_version:
        raise ValueError("Stale ticket version")
    allowed = {
        "employer_name",
        "employer_contact",
        "source_type",
        "transcript_original",
        "transcript_language",
    }
    for key in allowed:
        if key in values:
            setattr(row, key, values[key])
    row.version += 1
    db.commit()
    db.refresh(row)
    return row


def extract_ticket(db: Session, row: DemandTicket) -> DemandTicket:
    proposed = extractor.extract_ticket(row.transcript_original or "", row.transcript_language)
    proposed = llm.enhance_ticket(row.transcript_original or "", proposed)
    row.proposed_fields = proposed
    row.missing_fields = proposed.get("missing_fields")
    row.demand_type = proposed.get("demand_type") or "unknown"
    row.extraction_method = "rules"
    db.commit()
    db.refresh(row)
    return row


def confirm_ticket(
    db: Session,
    row: DemandTicket,
    values: dict[str, Any],
    actor: User,
) -> DemandTicket:
    for key, value in values.items():
        setattr(row, key, value)
    row.status = "confirmed"
    row.confirmed_by = actor.id
    row.confirmed_at = datetime.now(timezone.utc)
    row.version += 1
    db.commit()
    db.refresh(row)
    return row


def require_skill_family(db: Session, skill_family_id: str) -> SkillFamily:
    family = db.get(SkillFamily, skill_family_id)
    if family is None:
        family = db.scalar(select(SkillFamily).where(SkillFamily.slug == skill_family_id))
    if family is None:
        raise ValueError("Unknown skill family")
    return family


def create_module(
    db: Session,
    title: str,
    skill_family_id: str,
    language: str,
    content_json: dict[str, Any] | None,
    actor: User,
) -> Module:
    family = require_skill_family(db, skill_family_id)
    if content_json is None:
        records = db.query(KnowledgeRecord).all()
        from .module_draft import generate_module_draft

        knowledge_dicts = [
            {
                column.name: (
                    getattr(record, column.name).isoformat()
                    if hasattr(getattr(record, column.name), "isoformat")
                    else getattr(record, column.name)
                )
                for column in record.__table__.columns
            }
            for record in records
        ]
        content_json = generate_module_draft(
            family.slug,
            language,
            knowledge_dicts,
        )
    row = Module(
        title=title,
        skill_family_id=family.id,
        content_json=content_json,
        status="draft",
        data_mode="LIVE",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def publish_module(db: Session, row: Module) -> Module:
    row.status = "published"
    row.version += 1
    db.commit()
    db.refresh(row)
    return row


def create_submission(
    db: Session,
    task_id: str,
    pod_id: str,
    student_id: str,
    submission_json: dict[str, Any],
    entity_id: str | None = None,
) -> TaskSubmission:
    if db.scalar(
        select(PodEnrolment).where(
            PodEnrolment.pod_id == pod_id,
            PodEnrolment.student_id == student_id,
            PodEnrolment.status == "active",
        )
    ) is None:
        raise ValueError("Student is not enrolled in this pod")
    prior = db.scalars(
        select(TaskSubmission).where(
            TaskSubmission.task_id == task_id,
            TaskSubmission.pod_id == pod_id,
            TaskSubmission.student_id == student_id,
        )
    ).all()
    row = TaskSubmission(
        id=entity_id,
        task_id=task_id,
        pod_id=pod_id,
        student_id=student_id,
        submission_json={**submission_json, "revision": len(prior) + 1},
        status="submitted",
        data_mode="LIVE",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def teacher_review(
    db: Session,
    row: TaskSubmission,
    rubric_scores: dict[str, Any],
    teacher_feedback: str | None,
    decision: str,
) -> TaskSubmission:
    if decision not in {"teacher_reviewed", "returned_for_revision", "accepted"}:
        raise ValueError("Invalid decision")
    row.status = decision
    row.submission_json = {
        **(row.submission_json or {}),
        "rubric_scores": rubric_scores,
        "teacher_feedback": teacher_feedback,
    }
    row.version += 1
    db.commit()
    db.refresh(row)
    return row


def employer_review(
    db: Session,
    row: TaskSubmission,
    decision: str,
    employer_feedback: str | None,
) -> TaskSubmission:
    if decision not in {"accepted", "rejected", "returned_for_revision"}:
        raise ValueError("Invalid decision")
    row.status = decision
    row.submission_json = {
        **(row.submission_json or {}),
        "employer_feedback": employer_feedback,
    }
    row.version += 1
    db.commit()
    db.refresh(row)
    return row


def create_outcome(
    db: Session,
    student: Student,
    pod: Pod,
    stage: str,
    verification_level: str,
    evidence_key: str | None,
    notes: str | None,
    entity_id: str | None = None,
    data_mode: str = "SIMULATED",
) -> OutcomeEvent:
    row = OutcomeEvent(
        id=entity_id,
        event_type=stage,
        subject_type="student",
        subject_id=student.id,
        payload={
            "pod_id": pod.id,
            "verification_level": verification_level,
            "evidence_key": evidence_key,
            "notes": notes,
        },
        data_mode=data_mode,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
