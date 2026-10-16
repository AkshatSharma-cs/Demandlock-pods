from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_actor
from ..models import DemandTicket, Module, Pod, Student, SyncReceipt, User
from ..services import core, safeguarding

router = APIRouter()


class SyncOperation(BaseModel):
    client_op_id: str
    entity_type: str
    action: str
    entity_id: str | None = None
    base_version: int | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    client_occurred_at: str | None = None


class SyncPush(BaseModel):
    ops: list[SyncOperation]


def dump(row: Any) -> dict[str, Any]:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


def _apply(db: Session, operation: SyncOperation, actor: User) -> dict[str, Any]:
    payload = dict(operation.payload)
    if operation.entity_id is not None:
        payload.setdefault("id", operation.entity_id)

    if operation.entity_type == "demand_ticket" and operation.action == "create":
        if actor.role not in {"employer", "facilitator"}:
            raise PermissionError("Insufficient role")
        row = core.create_ticket(db, payload, actor)
        return {"entity": "demand_ticket", "entity_id": row.id, "result": dump(row)}

    if operation.entity_type == "demand_ticket" and operation.action in {"update_draft", "update"}:
        if actor.role not in {"employer", "facilitator"}:
            raise PermissionError("Insufficient role")
        if not operation.entity_id:
            raise ValueError("entity_id is required")
        row = db.get(DemandTicket, operation.entity_id)
        if row is None:
            raise ValueError("Ticket not found")
        row = core.update_ticket_draft(db, row, payload, operation.base_version)
        return {"entity": "demand_ticket", "entity_id": row.id, "result": dump(row)}

    if operation.entity_type == "submission" and operation.action == "create":
        task_id = payload["task_id"]
        module_id, index = task_id.split(":", 1)
        if not module_id or not index.isdigit():
            raise ValueError("task_id must be formatted as {module_id}:{index}")
        if db.get(Module, module_id) is None:
            raise ValueError("Module not found")
        student_id = payload.get("student_id")
        student = db.get(Student, student_id)
        if student is None:
            raise ValueError("Student not found")
        row = core.create_submission(
            db,
            payload["task_id"],
            payload["pod_id"],
            student.id,
            {
                "submitted_text": payload.get("submitted_text"),
                "media_key": payload.get("media_key"),
            },
            entity_id=operation.entity_id,
        )
        return {"entity": "submission", "entity_id": row.id, "result": dump(row)}

    if operation.entity_type == "outcome" and operation.action == "create":
        student = db.get(Student, payload.get("student_id"))
        pod = db.get(Pod, payload.get("pod_id"))
        if student is None or pod is None:
            raise ValueError("Student or pod not found")
        user = db.get(User, student.user_id)
        allowed, reason = safeguarding.can_record_outcome(
            (user.age_band if user else None) or student.age_band,
            payload["stage"],
        )
        if not allowed:
            raise PermissionError(reason)
        if payload["stage"] in safeguarding.WORK_STAGES and pod.pod_mode != safeguarding.WORK_TRIAL_MODE:
            raise ValueError("Work stages require work_trial")
        if payload["stage"] == "first_payment_verified" and payload.get("verification_level") not in {
            "employer_confirmed",
            "evidence_checked",
        }:
            raise ValueError("First payment requires employer confirmation or checked evidence")
        row = core.create_outcome(
            db,
            student,
            pod,
            payload["stage"],
            payload["verification_level"],
            payload.get("evidence_key"),
            payload.get("notes"),
            entity_id=operation.entity_id,
            data_mode="LIVE",
        )
        return {"entity": "outcome", "entity_id": row.id, "result": dump(row)}

    raise ValueError("Unsupported sync operation")


@router.post("/sync/push")
def sync_push(
    payload: SyncPush,
    actor: User = Depends(get_actor),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for operation in payload.ops:
        existing = db.scalar(select(SyncReceipt).where(SyncReceipt.client_op_id == operation.client_op_id))
        if existing is not None:
            stored = dict(existing.result_json or {})
            stored["status"] = "duplicate"
            results.append(stored)
            continue

        try:
            applied = _apply(db, operation, actor)
            result = {"client_op_id": operation.client_op_id, "status": "applied", **applied}
        except PermissionError as exc:
            db.rollback()
            result = {"client_op_id": operation.client_op_id, "status": "rejected", "reason": str(exc)}
        except ValueError as exc:
            db.rollback()
            reason = str(exc)
            result = {
                "client_op_id": operation.client_op_id,
                "status": "conflict" if "version" in reason.lower() or "confirmed" in reason.lower() else "rejected",
                "reason": reason,
            }
        except (IntegrityError, KeyError) as exc:
            db.rollback()
            result = {"client_op_id": operation.client_op_id, "status": "rejected", "reason": str(exc)}

        receipt = SyncReceipt(
            client_op_id=operation.client_op_id,
            result_json=jsonable_encoder(result),
            data_mode="LIVE",
        )
        db.add(receipt)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            existing = db.scalar(select(SyncReceipt).where(SyncReceipt.client_op_id == operation.client_op_id))
            result = dict(existing.result_json or {}) if existing else result
            result["status"] = "duplicate"
        results.append(result)

    return {"results": results, "server_time": datetime.now(timezone.utc).isoformat()}
