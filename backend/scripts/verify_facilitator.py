from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import select

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db import SessionLocal, create_all
from app.models import User


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/verify_facilitator.py <phone>")
    create_all()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.phone == sys.argv[1], User.role == "facilitator"))
        if user is None:
            raise SystemExit("Facilitator not found")
        user.facilitator_verified = True
        db.commit()
        print(f"Verified facilitator {user.phone}")


if __name__ == "__main__":
    main()
