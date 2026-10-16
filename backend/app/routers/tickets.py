from __future__ import annotations

import uuid
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..deps import get_actor, require_role
from ..models import DemandTicket, SkillFamily, User
from ..services import asr, core

router = APIRouter()


def dump(row: Any) -> dict[str, Any]:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


def ticket_or_404(db: Session, ticket_id: str) -> DemandTicket:
    row = db.get(DemandTicket, ticket_id)
    if row is None:
        raise HTTPException(404, "Ticket not found")
    return row


class TicketCreate(BaseModel):
    employer_name: str
    employer_contact: str | None = None
    source_type: str
    transcript_original: str | None = None
    transcript_language: str | None = None


class TicketConfirm(BaseModel):
    confirmed_skill_id: str
    slots_confirmed: int = Field(ge=1, le=200)
    block_code: str
    demand_type: str
    location_text: str | None = None
    pay_min_minor: int | None = Field(default=None, ge=0)
    pay_max_minor: int | None = Field(default=None, ge=0)
    pay_period: str | None = None
    duration_days: int | None = Field(default=None, ge=0)
    min_age: int | None = Field(default=None, ge=0)
    max_age: int | None = Field(default=None, ge=0)
    valid_until: date | None = None


@router.post("/demand-tickets")
def create_ticket(
    payload: TicketCreate,
    actor: User = Depends(require_role("employer", "facilitator")),
    db: Session = Depends(get_db),
) -> dict:
    if payload.source_type not in {"voice", "text", "manual"}:
        raise HTTPException(422, "Invalid source_type")
    return dump(core.create_ticket(db, payload.model_dump(), actor))


@router.post("/demand-tickets/{ticket_id}/audio")
async def upload_audio(
    ticket_id: str,
    file: UploadFile = File(...),
    actor: User = Depends(require_role("employer", "facilitator")),
    db: Session = Depends(get_db),
) -> dict:
    row = ticket_or_404(db, ticket_id)
    extension = Path(file.filename or "audio").suffix.lower()
    if not extension or not extension[1:].isalnum():
        extension = ".audio"
    directory = Path(settings.audio_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{ticket_id}{extension}"
    path.write_bytes(await file.read())
    row.audio_key = path.name
    if settings.enable_asr:
        try:
            result = asr.transcribe_file(str(path), language=row.transcript_language)
            row.transcript_original = result.get("text")
            row.transcript_language = result.get("language")
        except Exception:
            pass
    db.commit()
    db.refresh(row)
    return dump(row)


@router.post("/demand-tickets/{ticket_id}/extract")
def extract_ticket(
    ticket_id: str,
    actor: User = Depends(require_role("employer", "facilitator")),
    db: Session = Depends(get_db),
) -> dict:
    row = ticket_or_404(db, ticket_id)
    return dump(core.extract_ticket(db, row))


@router.get("/demand-tickets")
def list_tickets(
    status: str | None = None,
    block_code: str | None = None,
    skill_family_id: str | None = None,
    actor: User = Depends(get_actor),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = select(DemandTicket)
    if status:
        query = query.where(DemandTicket.status == status)
    if block_code:
        query = query.where(DemandTicket.block_code == block_code)
    if skill_family_id:
        query = query.where(DemandTicket.confirmed_skill_id == skill_family_id)
    return [dump(row) for row in db.scalars(query).all()]


@router.get("/demand-tickets/{ticket_id}")
def get_ticket(ticket_id: str, actor: User = Depends(get_actor), db: Session = Depends(get_db)) -> dict:
    return dump(ticket_or_404(db, ticket_id))


@router.post("/demand-tickets/{ticket_id}/confirm")
def confirm_ticket(
    ticket_id: str,
    payload: TicketConfirm,
    actor: User = Depends(require_role("employer", "facilitator")),
    db: Session = Depends(get_db),
) -> dict:
    row = ticket_or_404(db, ticket_id)
    if row.status == "confirmed":
        raise HTTPException(409, "Ticket is already confirmed")
    if payload.demand_type not in {"employment", "training", "service_contract"}:
        raise HTTPException(422, "Invalid demand_type")
    if payload.pay_min_minor is not None and payload.pay_max_minor is not None and payload.pay_min_minor > payload.pay_max_minor:
        raise HTTPException(422, "pay_min_minor cannot exceed pay_max_minor")
    if payload.min_age is not None and payload.max_age is not None and payload.min_age > payload.max_age:
        raise HTTPException(422, "min_age cannot exceed max_age")
    if not payload.block_code.strip():
        raise HTTPException(422, "block_code is required")
    family = db.get(SkillFamily, payload.confirmed_skill_id)
    if family is None:
        family = db.scalar(select(SkillFamily).where(SkillFamily.slug == payload.confirmed_skill_id))
    if family is None:
        raise HTTPException(422, "Unknown skill family")
    values = payload.model_dump()
    values["confirmed_skill_id"] = family.id
    return dump(core.confirm_ticket(db, row, values, actor))
