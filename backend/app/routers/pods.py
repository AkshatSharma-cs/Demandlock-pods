from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_actor, require_role
from ..models import DemandTicket, KnowledgeRecord, Module, Pod, PodEnrolment, SkillFamily, Student, TaskSubmission, User
from ..services import pods_rule, retrieval, safeguarding

router = APIRouter()


def dump(row: Any) -> dict[str, Any]:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


class Evaluate(BaseModel):
    block_code: str
    skill_family_id: str
    pod_mode: str = "work_trial"


class EnrolmentCreate(BaseModel):
    student_id: str


def pod_or_404(db: Session, pod_id: str) -> Pod:
    pod = db.get(Pod, pod_id)
    if pod is None:
        raise HTTPException(404, "Pod not found")
    return pod


def pod_details(db: Session, pod: Pod) -> dict:
    tickets = db.scalars(select(DemandTicket).where(DemandTicket.pod_id == pod.id)).all()
    records = [dump(record) for record in db.scalars(select(KnowledgeRecord)).all()]
    matches = retrieval.retrieve_with_fallback(records, pod.skill_family_id)
    claims = retrieval.build_claims(matches) if isinstance(matches, list) else matches
    pay_min = min((ticket.pay_min_minor for ticket in tickets if ticket.pay_min_minor is not None), default=None)
    pay_max = max((ticket.pay_max_minor for ticket in tickets if ticket.pay_max_minor is not None), default=None)
    return dump(pod) | {
        "tickets": [dump(ticket) for ticket in tickets],
        "enrolments": [dump(item) for item in db.scalars(select(PodEnrolment).where(PodEnrolment.pod_id == pod.id)).all()],
        "claims": claims,
        "money_card": {
            "pay_min_minor": pay_min if pay_min is not None else "unknown",
            "pay_max_minor": pay_max if pay_max is not None else "unknown",
            "pay_period": next((ticket.pay_period for ticket in tickets if ticket.pay_period), "unknown"),
            "basis": "employer-stated, unverified",
            "travel_cost": "unknown",
            "funding": "unknown",
        },
    }


@router.post("/pods/evaluate")
def evaluate_pod(
    payload: Evaluate,
    actor: User = Depends(require_role("facilitator", "admin")),
    db: Session = Depends(get_db),
) -> dict:
    family = db.get(SkillFamily, payload.skill_family_id)
    if family is None:
        family = db.scalar(select(SkillFamily).where(SkillFamily.slug == payload.skill_family_id))
    if family is None:
        raise HTTPException(422, "Unknown skill family")
    return pods_rule.evaluate(db, payload.block_code, family.id, payload.pod_mode)


@router.get("/pods")
def list_pods(
    block_code: str | None = None,
    skill_family_id: str | None = None,
    status: str | None = None,
    actor: User = Depends(get_actor),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = select(Pod)
    if block_code:
        query = query.where(Pod.block_code == block_code)
    if skill_family_id:
        query = query.where(Pod.skill_family_id == skill_family_id)
    if status:
        query = query.where(Pod.status == status)
    return [pod_details(db, pod) for pod in db.scalars(query).all()]


@router.get("/pods/{pod_id}")
def get_pod(pod_id: str, actor: User = Depends(get_actor), db: Session = Depends(get_db)) -> dict:
    return pod_details(db, pod_or_404(db, pod_id))


@router.get("/pods/{pod_id}/submissions")
def pod_submissions(
    pod_id: str,
    actor: User = Depends(require_role("facilitator")),
    db: Session = Depends(get_db),
) -> list[dict]:
    pod_or_404(db, pod_id)
    students = {student.id: db.get(User, student.user_id) for student in db.scalars(select(Student)).all()}
    rows = db.scalars(select(TaskSubmission).where(TaskSubmission.pod_id == pod_id)).all()
    return [
        {
            "student_name": students[row.student_id].name if students.get(row.student_id) else "unknown",
            "age_band": (students[row.student_id].age_band if students.get(row.student_id) else None) or "unknown",
            "task_id": row.task_id,
            "submission_json": row.submission_json,
            "status": row.status,
            "id": row.id,
        }
        for row in rows
    ]


class ModuleLink(BaseModel):
    module_id: str


@router.post("/pods/{pod_id}/module")
def attach_module(
    pod_id: str,
    payload: ModuleLink,
    actor: User = Depends(require_role("facilitator")),
    db: Session = Depends(get_db),
) -> dict:
    pod = pod_or_404(db, pod_id)
    module = db.get(Module, payload.module_id)
    if module is None:
        raise HTTPException(404, "Module not found")
    pod.module_id = module.id
    pod.version += 1
    db.commit()
    db.refresh(pod)
    return dump(pod)


@router.post("/pods/{pod_id}/enrolments")
def enrol(
    pod_id: str,
    payload: EnrolmentCreate,
    actor: User = Depends(get_actor),
    db: Session = Depends(get_db),
) -> dict:
    pod = pod_or_404(db, pod_id)
    student = db.get(Student, payload.student_id)
    if student is None:
        raise HTTPException(404, "Student not found")
    user = db.get(User, student.user_id)
    age_band = student.age_band or (user.age_band if user else "unknown")
    allowed, reason = safeguarding.can_enrol(age_band, pod.pod_mode)
    if not allowed:
        raise HTTPException(403, reason)
    existing = db.scalar(select(PodEnrolment).where(PodEnrolment.pod_id == pod.id, PodEnrolment.student_id == student.id))
    if existing is not None:
        return dump(existing)
    row = PodEnrolment(pod_id=pod.id, student_id=student.id, status="active")
    db.add(row)
    db.commit()
    db.refresh(row)
    return dump(row)


@router.get("/students/{student_id}/pods")
def student_pods(student_id: str, actor: User = Depends(get_actor), db: Session = Depends(get_db)) -> list[dict]:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(404, "Student not found")
    user = db.get(User, student.user_id)
    interests = set(student.interests or []) | set(user.interests or [] if user else [])
    families = {family.id: family.slug for family in db.scalars(select(SkillFamily)).all()}
    age_band = student.age_band or (user.age_band if user else "unknown")
    result = []
    for pod in db.scalars(select(Pod)).all():
        if pod.skill_family_id not in interests and families.get(pod.skill_family_id) not in interests:
            continue
        allowed, reason = safeguarding.can_enrol(age_band, pod.pod_mode)
        result.append(dump(pod) | {
            "can_enrol": allowed,
            "explanation": f"{reason} This pod offers learning practice; participation does not promise a job or income.",
        })
    return result
