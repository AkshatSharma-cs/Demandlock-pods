from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import Student, User

router = APIRouter()
failed_attempts: defaultdict[str, list[float]] = defaultdict(list)


class RegisterRequest(BaseModel):
    name: str
    phone: str
    pin: str = Field(pattern=r"^\d{4,6}$")
    role: str
    age_band: str
    language: str


class LoginRequest(BaseModel):
    phone: str
    pin: str


def hash_pin(pin: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(pin.encode(), salt=salt, n=16384, r=8, p=1)
    return f"scrypt${base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"


def verify_pin(pin: str, encoded: str | None) -> bool:
    try:
        _, salt_text, digest_text = encoded.split("$")
        salt = base64.urlsafe_b64decode(salt_text)
        expected = base64.urlsafe_b64decode(digest_text)
        actual = hashlib.scrypt(pin.encode(), salt=salt, n=16384, r=8, p=1)
        return hmac.compare_digest(actual, expected)
    except (AttributeError, ValueError):
        return False


def user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "phone": user.phone,
        "role": user.role,
        "age_band": user.age_band,
        "language": user.language,
        "facilitator_verified": user.facilitator_verified,
    }


def issue_token(user: User) -> str:
    encoded = base64.urlsafe_b64encode(
        json.dumps({"uid": user.id, "exp": int(time.time()) + 12 * 60 * 60}, separators=(",", ":")).encode()
    ).decode().rstrip("=")
    signature = base64.urlsafe_b64encode(
        hmac.new(settings.secret_key.encode(), encoded.encode(), hashlib.sha256).digest()
    ).decode().rstrip("=")
    return f"{encoded}.{signature}"


@router.post("/auth/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> dict:
    if payload.role not in {"employer", "student", "facilitator"}:
        raise HTTPException(422, "Invalid role")
    if payload.age_band not in {"under_14", "14_17", "18_plus"}:
        raise HTTPException(422, "Invalid age_band")
    if db.scalar(select(User).where(User.phone == payload.phone)) is not None:
        raise HTTPException(409, "Phone number is already registered")
    user = User(
        name=payload.name,
        phone=payload.phone,
        pin_hash=hash_pin(payload.pin),
        role=payload.role,
        age_band=payload.age_band,
        language=payload.language,
        facilitator_verified=False,
        data_mode="LIVE",
    )
    db.add(user)
    try:
        db.flush()
        if payload.role == "student":
            db.add(Student(user_id=user.id, age_band=payload.age_band, data_mode="LIVE"))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Phone number is already registered") from None
    db.refresh(user)
    return {"user": user_payload(user)}


@router.post("/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict:
    now = time.time()
    failed_attempts[payload.phone] = [stamp for stamp in failed_attempts[payload.phone] if now - stamp < 600]
    if len(failed_attempts[payload.phone]) >= 5:
        raise HTTPException(429, "Too many failed attempts; try again later")
    user = db.scalar(select(User).where(User.phone == payload.phone))
    if user is None or not verify_pin(payload.pin, user.pin_hash):
        failed_attempts[payload.phone].append(now)
        raise HTTPException(401, "Invalid phone or PIN")
    failed_attempts.pop(payload.phone, None)
    return {"token": issue_token(user), "user": user_payload(user)}
