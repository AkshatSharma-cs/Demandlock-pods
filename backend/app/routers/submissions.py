from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_actor, require_role
from ..models import Student, TaskSubmission, User
from ..models import Module
from ..services import core, safeguarding

router = APIRouter()


def dump(row: Any) -> dict[str, Any]:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


class SubmissionCreate(BaseModel):
    pod_id: str
    student_id: str
    submitted_text: str | None = None
    media_key: str | None = None


class TeacherReview(BaseModel):
    rubric_scores: dict[str, Any]
    teacher_feedback: str | None = None
    decision: str


class EmployerReview(BaseModel):
    decision: str
    employer_feedback: str | None = None


@router.post("/tasks/{task_id}/submissions")
def create_submission(
    task_id: str,
    payload: SubmissionCreate,
    actor: User = Depends(get_actor),
    db: Session = Depends(get_db),
) -> dict:
    try:
        module_id, index = task_id.split(":", 1)
        if not module_id or not index.isdigit():
            raise ValueError
    except ValueError as exc:
        raise HTTPException(422, "task_id must be formatted as {module_id}:{index}") from exc
    if db.get(Module, module_id) is None:
        raise HTTPException(404, "Module not found")
    student = db.get(Student, payload.student_id)
    if student is None:
        raise HTTPException(404, "Student not found")
    try:
        row = core.create_submission(
            db,
            task_id,
            payload.pod_id,
            student.id,
            {"submitted_text": payload.submitted_text, "media_key": payload.media_key},
        )
    except ValueError as exc:
        raise HTTPException(403, str(exc)) from exc
    return dump(row)


@router.post("/submissions/{submission_id}/teacher-review")
def review_by_teacher(
    submission_id: str,
    payload: TeacherReview,
    actor: User = Depends(require_role("facilitator")),
    db: Session = Depends(get_db),
) -> dict:
    row = db.get(TaskSubmission, submission_id)
    if row is None:
        raise HTTPException(404, "Submission not found")
    try:
        return dump(core.teacher_review(db, row, **payload.model_dump()))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/submissions/{submission_id}/employer-review")
def review_by_employer(
    submission_id: str,
    payload: EmployerReview,
    actor: User = Depends(require_role("employer")),
    db: Session = Depends(get_db),
) -> dict:
    row = db.get(TaskSubmission, submission_id)
    if row is None:
        raise HTTPException(404, "Submission not found")
    student = db.get(Student, row.student_id)
    user = db.get(User, student.user_id) if student else None
    allowed, reason = safeguarding.can_record_outcome(
        (user.age_band if user else None) or (student.age_band if student else "unknown"),
        "employer_reviewed",
    )
    if not allowed:
        raise HTTPException(403, reason)
    try:
        return dump(core.employer_review(db, row, **payload.model_dump()))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
