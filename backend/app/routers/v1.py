from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..deps import get_actor, require_role, require_verified_facilitator
from ..models import (
    Block, DemandTicket, KnowledgeRecord, Module, OutcomeEvent, Pod, PodEnrolment,
    SkillFamily, Student, TaskSubmission, User,
)
from ..services import asr, extractor, llm, module_draft, retrieval, safeguarding
from ..db import get_db

router = APIRouter()


def fail(code: int, message: str) -> None:
    raise HTTPException(code, detail=message)


@router.get("/blocks")
def list_blocks(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    return [
        {"code": block.code, "name": block.name, "district": block.district, "state": block.state}
        for block in db.scalars(select(Block).order_by(Block.name)).all()
    ]


def dump(row: Any) -> dict[str, Any]:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


class TicketCreate(BaseModel):
    id: str | None = None
    employer_name: str
    employer_contact: str | None = None
    source_type: str
    transcript_original: str | None = None
    transcript_language: str | None = None


class TicketConfirm(BaseModel):
    confirmed_skill_id: str
    slots_confirmed: int = Field(ge=1, le=200)
    block_code: str
    location_text: str | None = None
    demand_type: str
    pay_min_minor: int | None = Field(default=None, ge=0)
    pay_max_minor: int | None = Field(default=None, ge=0)
    pay_period: str | None = None
    duration_days: int | None = Field(default=None, ge=0)
    min_age: int | None = Field(default=None, ge=0)
    max_age: int | None = Field(default=None, ge=0)
    valid_until: date | None = None


class Evaluate(BaseModel):
    block_code: str
    skill_family_id: str
    pod_mode: str = "work_trial"


class EnrolmentCreate(BaseModel):
    student_id: str


class ModuleCreate(BaseModel):
    id: str | None = None
    title: str
    language: str
    skill_family_id: str
    pricing_model: str
    price_minor: int | None = Field(default=None, ge=0)
    content_json: dict[str, Any] | None = None


class Publish(BaseModel):
    human_reviewed: bool


class SubmissionCreate(BaseModel):
    id: str | None = None
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


class SyncOperation(BaseModel):
    client_op_id: str
    entity_type: str
    action: str
    entity_id: str | None = None
    base_version: int | None = None
    payload: dict[str, Any] = {}
    client_occurred_at: str | None = None


class SyncPush(BaseModel):
    ops: list[SyncOperation]


class OutcomeCreate(BaseModel):
    id: str | None = None
    student_id: str
    pod_id: str
    stage: str
    verification_level: str
    evidence_key: str | None = None
    notes: str | None = None


def _ticket(db: Session, ticket_id: str) -> DemandTicket:
    row = db.get(DemandTicket, ticket_id)
    if row is None:
        fail(404, "Ticket not found")
    return row


@router.get("/me")
def me(actor: User = Depends(get_actor)) -> dict[str, Any]:
    return {"user": dump(actor), "auth_mode": "DEMO" if settings.demo_mode else "LIVE"}


@router.post("/demand-tickets")
def create_ticket(payload: TicketCreate, actor: User = Depends(require_role("employer", "facilitator")), db: Session = Depends(get_db)):
    if payload.source_type not in {"voice", "text", "manual"}:
        fail(422, "Invalid source_type")
    row = DemandTicket(
        id=payload.id or str(uuid.uuid4()), employer_name=payload.employer_name,
        employer_contact=payload.employer_contact, source_type=payload.source_type,
        transcript_original=payload.transcript_original, transcript_language=payload.transcript_language,
        demand_type="unknown", status="draft", data_mode="LIVE",
    )
    db.add(row); db.commit(); db.refresh(row)
    return dump(row)


@router.post("/demand-tickets/{ticket_id}/audio")
async def add_audio(ticket_id: str, file: UploadFile = File(...), actor: User = Depends(require_role("employer", "facilitator")), db: Session = Depends(get_db)):
    row = _ticket(db, ticket_id)
    directory = Path(settings.audio_dir); directory.mkdir(parents=True, exist_ok=True)
    key = f"{ticket_id}-{uuid.uuid4().hex}{Path(file.filename or 'audio').suffix}"
    path = directory / key
    path.write_bytes(await file.read())
    row.audio_key = key
    if settings.enable_asr:
        try:
            result = asr.transcribe_file(str(path))
            row.transcript_original, row.transcript_language = result.get("text"), result.get("language")
        except Exception:
            pass
    db.commit(); db.refresh(row)
    return dump(row)


@router.post("/demand-tickets/{ticket_id}/extract")
def extract_ticket(ticket_id: str, actor: User = Depends(require_role("employer", "facilitator")), db: Session = Depends(get_db)):
    row = _ticket(db, ticket_id)
    proposed = extractor.extract_ticket(row.transcript_original or "", row.transcript_language)
    proposed = llm.enhance_ticket(row.transcript_original or "", proposed)
    row.proposed_fields = proposed
    row.missing_fields = proposed.get("missing_fields")
    row.demand_type = proposed.get("demand_type") or "unknown"
    row.extraction_method = "rules"
    row.status = "needs_confirmation"
    db.commit(); db.refresh(row)
    return dump(row)


@router.get("/demand-tickets")
def list_tickets(status: str | None = None, block_code: str | None = None, skill_family_id: str | None = None,
                 actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    query = select(DemandTicket)
    if status: query = query.where(DemandTicket.status == status)
    if block_code: query = query.where(DemandTicket.block_code == block_code)
    if skill_family_id: query = query.where(DemandTicket.confirmed_skill_id == skill_family_id)
    return [dump(row) for row in db.scalars(query).all()]


@router.get("/demand-tickets/{ticket_id}")
def get_ticket(ticket_id: str, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    return dump(_ticket(db, ticket_id))


@router.post("/demand-tickets/{ticket_id}/confirm")
def confirm_ticket(ticket_id: str, payload: TicketConfirm, actor: User = Depends(require_role("employer", "facilitator")), db: Session = Depends(get_db)):
    row = _ticket(db, ticket_id)
    if row.status == "confirmed": fail(409, "Ticket is already confirmed")
    if not db.get(SkillFamily, payload.confirmed_skill_id): fail(422, "Unknown skill family")
    if payload.demand_type not in {"employment", "training", "service_contract"}: fail(422, "Invalid demand_type")
    for key, value in payload.model_dump().items(): setattr(row, key, value)
    row.status, row.confirmed_by, row.confirmed_at, row.version = "confirmed", actor.id, datetime.now(timezone.utc), row.version + 1
    db.commit(); db.refresh(row)
    return dump(row)


@router.post("/pods/evaluate")
def evaluate_pod(payload: Evaluate, actor: User = Depends(require_verified_facilitator), db: Session = Depends(get_db)):
    if not db.get(SkillFamily, payload.skill_family_id): fail(422, "Unknown skill family")
    today = date.today()
    tickets = db.scalars(select(DemandTicket).where(
        DemandTicket.status == "confirmed", DemandTicket.demand_type == "employment",
        DemandTicket.block_code == payload.block_code, DemandTicket.confirmed_skill_id == payload.skill_family_id,
    )).all()
    tickets = [t for t in tickets if t.valid_until is None or t.valid_until >= today]
    total = sum(t.slots_confirmed for t in tickets)
    threshold = settings.pod_threshold
    base = {"threshold_slots": threshold, "confirmed_slots": total, "eligible_ticket_count": len(tickets)}
    if total < threshold: return {"result": "below_threshold", **base}
    pod = db.scalar(select(Pod).where(Pod.block_code == payload.block_code, Pod.skill_family_id == payload.skill_family_id,
                                     Pod.status.in_(["proposed", "open", "running"])))
    result = "pod_updated" if pod else "pod_proposed"
    if not pod:
        pod = Pod(name=f"{payload.skill_family_id} pod", skill_family_id=payload.skill_family_id, block_code=payload.block_code,
                  threshold_slots=threshold, pod_mode=payload.pod_mode, status="proposed", facilitator_user_id=actor.id)
        db.add(pod); db.flush()
    pod.confirmed_slots, pod.version = total, pod.version + 1
    for ticket in tickets: ticket.pod_id = pod.id
    db.commit()
    return {"result": result, **base, "pod_id": pod.id}


@router.get("/pods")
def list_pods(block_code: str | None = None, skill_family_id: str | None = None, status: str | None = None,
              actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    query = select(Pod)
    if block_code: query = query.where(Pod.block_code == block_code)
    if skill_family_id: query = query.where(Pod.skill_family_id == skill_family_id)
    if status: query = query.where(Pod.status == status)
    return [dump(row) for row in db.scalars(query).all()]


@router.get("/pods/{pod_id}")
def get_pod(pod_id: str, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    row = db.get(Pod, pod_id)
    if not row: fail(404, "Pod not found")
    records = db.scalars(select(KnowledgeRecord)).all()
    raw = [dump(record) for record in records]
    matched = retrieval.retrieve(raw, row.skill_family_id)
    claims = retrieval.build_claims(matched) if matched else retrieval.explain_unknown()
    tickets = db.scalars(select(DemandTicket).where(DemandTicket.pod_id == pod_id)).all()
    enrolments = db.scalars(select(PodEnrolment).where(PodEnrolment.pod_id == pod_id)).all()
    result = dump(row) | {"tickets": [dump(t) for t in tickets], "claims": claims, "enrolments": [dump(e) for e in enrolments]}
    result["money_card"] = {"pay_min_minor": min((t.pay_min_minor for t in tickets if t.pay_min_minor is not None), default=None),
                            "pay_max_minor": max((t.pay_max_minor for t in tickets if t.pay_max_minor is not None), default=None),
                            "pay_period": next((t.pay_period for t in tickets if t.pay_period), None),
                            "basis": "employer-stated, unverified", "travel_cost": "unknown", "funding": "unknown"}
    return result


@router.post("/pods/{pod_id}/enrolments")
def enrol(pod_id: str, payload: EnrolmentCreate, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    pod = db.get(Pod, pod_id); student = db.get(Student, payload.student_id)
    if not pod or not student: fail(404, "Pod or student not found")
    user = db.get(User, student.user_id)
    allowed, reason = safeguarding.can_enrol(user.age_band or student.age_band, pod.pod_mode)
    if not allowed: fail(403, reason)
    row = PodEnrolment(pod_id=pod_id, student_id=student.id, status="active")
    db.add(row); db.commit(); db.refresh(row)
    return dump(row)


@router.get("/students/{student_id}/pods")
def student_pods(student_id: str, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    student = db.get(Student, student_id)
    if not student: fail(404, "Student not found")
    user = db.get(User, student.user_id)
    pods = db.scalars(select(Pod).where(Pod.skill_family_id.in_(student.interests or []))).all()
    return [dump(p) | {"explanation": safeguarding.can_enrol(user.age_band or student.age_band, p.pod_mode)[1],
                       "can_enrol": safeguarding.can_enrol(user.age_band or student.age_band, p.pod_mode)[0]} for p in pods]


@router.post("/modules")
def create_module(payload: ModuleCreate, actor: User = Depends(require_verified_facilitator), db: Session = Depends(get_db)):
    if payload.pricing_model not in {"free", "pay_per_module", "subscription"}: fail(422, "Invalid pricing_model")
    content = payload.content_json or module_draft.generate_module_draft(payload.skill_family_id, payload.language)
    row = Module(id=payload.id or str(uuid.uuid4()), title=payload.title, skill_family_id=payload.skill_family_id,
                 content_json=content, status="draft", data_mode="LIVE")
    db.add(row); db.commit(); db.refresh(row)
    return dump(row)


@router.get("/modules")
def list_modules(skill_family_id: str | None = None, status: str | None = None, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    query = select(Module)
    if skill_family_id: query = query.where(Module.skill_family_id == skill_family_id)
    if status: query = query.where(Module.status == status)
    return [dump(row) for row in db.scalars(query).all()]


@router.post("/modules/{module_id}/publish")
def publish_module(module_id: str, payload: Publish, actor: User = Depends(require_verified_facilitator), db: Session = Depends(get_db)):
    if not payload.human_reviewed: fail(422, "human_reviewed must be true")
    row = db.get(Module, module_id)
    if not row: fail(404, "Module not found")
    row.status = "published"; db.commit(); db.refresh(row)
    return dump(row)


@router.post("/tasks/{task_id}/submissions")
def create_submission(task_id: str, payload: SubmissionCreate, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    student = db.get(Student, payload.student_id)
    if not student: fail(404, "Student not found")
    if not db.scalar(select(PodEnrolment).where(PodEnrolment.pod_id == payload.pod_id,
                                               PodEnrolment.student_id == student.id,
                                               PodEnrolment.status == "active")):
        fail(403, "Student is not enrolled in this pod")
    prior = db.scalars(select(TaskSubmission).where(TaskSubmission.task_id == task_id,
                                                     TaskSubmission.pod_id == payload.pod_id,
                                                     TaskSubmission.student_id == student.id)).all()
    row = TaskSubmission(id=payload.id or str(uuid.uuid4()), task_id=task_id, pod_id=payload.pod_id,
                         student_id=student.id, submission_json={"submitted_text": payload.submitted_text,
                         "media_key": payload.media_key, "revision": len(prior) + 1},
                         status="submitted")
    db.add(row); db.commit(); db.refresh(row)
    return dump(row)


@router.post("/submissions/{submission_id}/teacher-review")
def teacher_review(submission_id: str, payload: TeacherReview,
                   actor: User = Depends(require_verified_facilitator), db: Session = Depends(get_db)):
    row = db.get(TaskSubmission, submission_id)
    if not row: fail(404, "Submission not found")
    if payload.decision not in {"teacher_reviewed", "returned_for_revision", "accepted"}: fail(422, "Invalid decision")
    row.status = payload.decision
    row.submission_json = {**(row.submission_json or {}), "rubric_scores": payload.rubric_scores,
                           "teacher_feedback": payload.teacher_feedback}
    db.commit(); db.refresh(row)
    return dump(row)


@router.post("/submissions/{submission_id}/employer-review")
def employer_review(submission_id: str, payload: EmployerReview,
                    actor: User = Depends(require_role("employer")), db: Session = Depends(get_db)):
    row = db.get(TaskSubmission, submission_id)
    if not row: fail(404, "Submission not found")
    student = db.get(Student, row.student_id); user = db.get(User, student.user_id)
    allowed, reason = safeguarding.can_record_outcome(user.age_band or student.age_band, "employer_reviewed")
    if not allowed: fail(403, reason)
    if payload.decision not in {"accepted", "rejected", "returned_for_revision"}: fail(422, "Invalid decision")
    row.status = payload.decision
    row.submission_json = {**(row.submission_json or {}), "employer_feedback": payload.employer_feedback}
    db.commit(); db.refresh(row)
    return dump(row)


@router.post("/outcomes")
def create_outcome(payload: OutcomeCreate, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    student = db.get(Student, payload.student_id); pod = db.get(Pod, payload.pod_id)
    if not student or not pod: fail(404, "Student or pod not found")
    user = db.get(User, student.user_id)
    allowed, reason = safeguarding.can_record_outcome(user.age_band or student.age_band, payload.stage)
    if not allowed: fail(403, reason)
    if payload.stage in safeguarding.WORK_STAGES and pod.pod_mode != safeguarding.WORK_TRIAL_MODE: fail(422, "Work stages require work_trial")
    if payload.stage == "first_payment_verified" and payload.verification_level not in {"employer_confirmed", "evidence_checked"}: fail(422, "First payment requires employer confirmation or checked evidence")
    row = OutcomeEvent(id=payload.id or str(uuid.uuid4()), event_type=payload.stage, subject_type="student", subject_id=student.id,
                       payload={"pod_id": pod.id, "verification_level": payload.verification_level, "evidence_key": payload.evidence_key, "notes": payload.notes})
    db.add(row); db.commit(); db.refresh(row)
    return dump(row)


@router.get("/outcomes")
def list_outcomes(pod_id: str | None = None, student_id: str | None = None, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    values = db.scalars(select(OutcomeEvent)).all()
    return [dump(v) for v in values if (pod_id is None or (v.payload or {}).get("pod_id") == pod_id)
            and (student_id is None or v.subject_id == student_id)]


@router.get("/dashboard/impact")
def impact(actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    tickets = db.scalars(select(DemandTicket)).all()
    pods = db.scalars(select(Pod)).all()
    outcomes = db.scalars(select(OutcomeEvent)).all()
    ticket_counts: dict[str, int] = {}
    pod_counts: dict[str, int] = {}
    stage_counts: dict[str, dict[str, int]] = {}
    for row in tickets: ticket_counts[row.status] = ticket_counts.get(row.status, 0) + 1
    for row in pods: pod_counts[row.status] = pod_counts.get(row.status, 0) + 1
    for row in outcomes:
        level = (row.payload or {}).get("verification_level", "unknown")
        stage_counts.setdefault(row.event_type, {})[level] = stage_counts.setdefault(row.event_type, {}).get(level, 0) + 1
    return {"data_mode": "SIMULATED" if any(row.data_mode == "SIMULATED" for row in tickets + pods) else "LIVE",
            "tickets_by_status": ticket_counts, "pods_by_status": pod_counts, "outcomes": stage_counts}


@router.post("/sync/push")
def sync_push(payload: SyncPush, actor: User = Depends(get_actor), db: Session = Depends(get_db)):
    results = []
    receipts = db.scalars(select(OutcomeEvent)).all()
    seen = {str((r.payload or {}).get("client_op_id")): r for r in receipts}
    for op in payload.ops:
        if op.client_op_id in seen:
            results.append({"client_op_id": op.client_op_id, "status": "duplicate",
                            "entity_id": seen[op.client_op_id].id, "server_version": 1})
            continue
        if op.action == "create_outcome":
            try:
                created = create_outcome(OutcomeCreate(**op.payload), actor, db)
                results.append({"client_op_id": op.client_op_id, "status": "applied",
                                "entity_id": created["id"], "server_version": 1})
            except HTTPException as exc:
                results.append({"client_op_id": op.client_op_id, "status": "rejected", "reason": str(exc.detail)})
        else:
            results.append({"client_op_id": op.client_op_id, "status": "rejected", "reason": "Unsupported sync action"})
    return {"results": results, "server_time": datetime.now(timezone.utc).isoformat()}
