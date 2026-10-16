from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..deps import get_actor
from ..models import (
    Block, DemandTicket, KnowledgeRecord, Module, OutcomeEvent, Pod, PodEnrolment,
    SkillFamily, Student, SyncReceipt, TaskSubmission, User,
)

router = APIRouter()


@router.get("/dashboard/impact")
def impact(actor: User = Depends(get_actor), db: Session = Depends(get_db)) -> dict[str, Any]:
    def grouped(rows: list[Any], field: str) -> dict[str, int]:
        result: dict[str, int] = {}
        for row in rows:
            value = getattr(row, field)
            result[value] = result.get(value, 0) + 1
        return result

    outcomes = db.scalars(select(OutcomeEvent)).all()
    stages: dict[str, dict[str, int]] = {}
    for outcome in outcomes:
        level = (outcome.payload or {}).get("verification_level", "unknown")
        stages.setdefault(outcome.event_type, {})
        stages[outcome.event_type][level] = stages[outcome.event_type].get(level, 0) + 1
    models = (
        Block, DemandTicket, KnowledgeRecord, Module, OutcomeEvent, Pod, PodEnrolment,
        SkillFamily, Student, SyncReceipt, TaskSubmission, User,
    )
    has_simulated_data = any(
        db.scalar(select(model.id).where(model.data_mode == "SIMULATED").limit(1)) is not None
        for model in models
    )
    return {
        "data_mode": "SIMULATED" if has_simulated_data else "LIVE",
        "outcomes": stages,
        "counts_by_stage_and_verification_level": stages,
        "tickets_by_status": grouped(db.scalars(select(DemandTicket)).all(), "status"),
        "pods_by_status": grouped(db.scalars(select(Pod)).all(), "status"),
    }
