import base64
import hashlib
import hmac
import json
import time
from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from .db import get_db
from .models import User
from .config import settings


def get_actor(
    authorization: str | None = Header(default=None),
    x_demo_user_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    user_id = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        try:
            encoded, signature = token.split(".", 1)
            expected = hmac.new(settings.secret_key.encode(), encoded.encode(), hashlib.sha256).digest()
            if not hmac.compare_digest(
                expected,
                base64.urlsafe_b64decode(signature + "=" * (-len(signature) % 4)),
            ):
                raise ValueError
            payload = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
            if int(payload["exp"]) <= int(time.time()):
                raise ValueError
            user_id = str(payload["uid"])
        except (ValueError, KeyError, TypeError, json.JSONDecodeError):
            raise HTTPException(status_code=401, detail="Invalid or expired token") from None
    elif x_demo_user_id and settings.demo_mode:
        user_id = x_demo_user_id
    elif x_demo_user_id:
        raise HTTPException(status_code=401, detail="Demo authentication is disabled")
    else:
        raise HTTPException(status_code=401, detail="Bearer token is required")
    actor = db.get(User, user_id)
    if actor is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown user")
    return actor


def require_role(*roles: str) -> Callable:
    def dependency(actor: User = Depends(get_actor)) -> User:
        if actor.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return actor

    return dependency


def require_verified_facilitator(actor: User = Depends(require_role("facilitator", "admin"))) -> User:
    if actor.role == "facilitator" and not settings.demo_mode and not actor.facilitator_verified:
        raise HTTPException(status_code=403, detail="Facilitator verification is required")
    return actor
