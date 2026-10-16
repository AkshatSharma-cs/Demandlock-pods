from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from .db import get_db
from .models import User


def get_actor(
    x_demo_user_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not x_demo_user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="X-Demo-User-Id is required")
    actor = db.get(User, x_demo_user_id)
    if actor is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown demo user")
    return actor


def require_role(*roles: str) -> Callable:
    def dependency(actor: User = Depends(get_actor)) -> User:
        if actor.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return actor

    return dependency
