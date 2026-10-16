from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..deps import get_actor
from ..models import DemandTicket, OutcomeEvent, Pod, User

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
    return {
        "data_mode": "SIMULATED" if settings.demo_mode else "LIVE",
        "outcomes": stages,
        "counts_by_stage_and_verification_level": stages,
        "tickets_by_status": grouped(db.scalars(select(DemandTicket)).all(), "status"),
        "pods_by_status": grouped(db.scalars(select(Pod)).all(), "status"),
    }
