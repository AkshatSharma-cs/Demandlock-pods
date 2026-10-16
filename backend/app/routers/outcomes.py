from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_actor
from ..models import OutcomeEvent, Pod, Student, User
from ..services import core, safeguarding

router = APIRouter()


def dump(row: Any) -> dict[str, Any]:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


class OutcomeCreate(BaseModel):
    student_id: str
    pod_id: str
    stage: str
    verification_level: str
    evidence_key: str | None = None
    notes: str | None = None


@router.post("/outcomes")
def create_outcome(
    payload: OutcomeCreate,
    actor: User = Depends(get_actor),
    db: Session = Depends(get_db),
) -> dict:
    student = db.get(Student, payload.student_id)
    pod = db.get(Pod, payload.pod_id)
    if student is None or pod is None:
        raise HTTPException(404, "Student or pod not found")
    user = db.get(User, student.user_id)
    allowed, reason = safeguarding.can_record_outcome(
        (user.age_band if user else None) or student.age_band,
        payload.stage,
    )
    if not allowed:
        raise HTTPException(403, reason)
    if payload.stage in safeguarding.WORK_STAGES and pod.pod_mode != safeguarding.WORK_TRIAL_MODE:
        raise HTTPException(422, "Work stages require work_trial")
    if payload.stage == "first_payment_verified" and payload.verification_level not in {"employer_confirmed", "evidence_checked"}:
        raise HTTPException(422, "First payment requires employer confirmation or checked evidence")
    return dump(core.create_outcome(db, student, pod, **payload.model_dump(exclude={"student_id", "pod_id"})))


@router.get("/outcomes")
def list_outcomes(
    pod_id: str | None = None,
    student_id: str | None = None,
    actor: User = Depends(get_actor),
    db: Session = Depends(get_db),
) -> list[dict]:
    values = db.scalars(select(OutcomeEvent)).all()
    return [
        dump(value)
        for value in values
        if (pod_id is None or (value.payload or {}).get("pod_id") == pod_id)
        and (student_id is None or value.subject_id == student_id)
    ]
