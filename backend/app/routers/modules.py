from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_actor, require_role, require_verified_facilitator
from ..models import KnowledgeRecord, Module, SkillFamily, User
from ..services import core

router = APIRouter()


def dump(row: Any) -> dict[str, Any]:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


class ModuleCreate(BaseModel):
    title: str
    language: str = "en"
    skill_family_id: str
    content_json: dict[str, Any] | None = None
    pricing_model: str = "free"
    price_minor: int | None = None


class PublishRequest(BaseModel):
    human_reviewed: bool


@router.post("/modules")
def create_module(
    payload: ModuleCreate,
    actor: User = Depends(require_verified_facilitator),
    db: Session = Depends(get_db),
) -> dict:
    if payload.pricing_model not in {"free", "pay_per_module", "subscription"}:
        raise HTTPException(422, "Invalid pricing_model")
    try:
        return dump(core.create_module(db, **payload.model_dump(), actor=actor))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/modules")
def list_modules(
    skill_family_id: str | None = None,
    status: str | None = None,
    actor: User = Depends(get_actor),
    db: Session = Depends(get_db),
) -> list[dict]:
    query = select(Module)
    if skill_family_id:
        family = db.get(SkillFamily, skill_family_id) or db.scalar(select(SkillFamily).where(SkillFamily.slug == skill_family_id))
        query = query.where(Module.skill_family_id == (family.id if family else skill_family_id))
    if status:
        query = query.where(Module.status == status)
    return [dump(row) for row in db.scalars(query).all()]


@router.post("/modules/{module_id}/publish")
def publish_module(
    module_id: str,
    payload: PublishRequest,
    actor: User = Depends(require_verified_facilitator),
    db: Session = Depends(get_db),
) -> dict:
    if not payload.human_reviewed:
        raise HTTPException(422, "human_reviewed must be true")
    row = db.get(Module, module_id)
    if row is None:
        raise HTTPException(404, "Module not found")
    return dump(core.publish_module(db, row))
