"""Deterministic pod threshold rules with database orchestration kept separate."""

from __future__ import annotations

from datetime import date
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import DemandTicket, Pod, SkillFamily


def count_eligible_tickets(
    tickets: Iterable[DemandTicket],
    today: date | None = None,
) -> tuple[int, int]:
    current_date = today or date.today()
    eligible = [
        ticket
        for ticket in tickets
        if ticket.status == "confirmed"
        and ticket.demand_type == "employment"
        and (ticket.valid_until is None or ticket.valid_until >= current_date)
    ]
    return sum(ticket.slots_confirmed for ticket in eligible), len(eligible)


def evaluate(
    db: Session,
    block_code: str,
    skill_family_id: str,
    pod_mode: str,
) -> dict:
    """Evaluate and persist one pod candidate atomically."""
    if db.in_transaction():
        db.commit()
    with db.begin():
        tickets = db.scalars(
            select(DemandTicket)
            .where(
                DemandTicket.block_code == block_code,
                DemandTicket.confirmed_skill_id == skill_family_id,
            )
        ).all()
        confirmed_slots, eligible_count = count_eligible_tickets(tickets)
        result = {
            "threshold_slots": settings.pod_threshold,
            "confirmed_slots": confirmed_slots,
            "eligible_ticket_count": eligible_count,
        }
        if confirmed_slots < settings.pod_threshold:
            return {"result": "below_threshold", **result}

        pod = db.scalar(
            select(Pod).where(
                Pod.block_code == block_code,
                Pod.skill_family_id == skill_family_id,
                Pod.pod_mode == pod_mode,
                Pod.status.in_(("proposed", "open", "running")),
            )
        )
        if pod is None:
            family = db.get(SkillFamily, skill_family_id)
            pod = Pod(
                name=f"{family.canonical_name if family else skill_family_id} pod",
                skill_family_id=skill_family_id,
                block_code=block_code,
                threshold_slots=settings.pod_threshold,
                confirmed_slots=confirmed_slots,
                pod_mode=pod_mode,
                status="proposed",
            )
            db.add(pod)
            db.flush()
            result_name = "pod_proposed"
        else:
            pod.confirmed_slots = confirmed_slots
            pod.version += 1
            result_name = "pod_updated"

        for ticket in tickets:
            if ticket.status == "confirmed" and ticket.demand_type == "employment":
                ticket.pod_id = pod.id
        return {"result": result_name, **result, "pod_id": pod.id}
