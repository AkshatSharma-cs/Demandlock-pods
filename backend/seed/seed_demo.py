from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy import select

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db import SessionLocal, create_all  # noqa: E402
from app.models import (  # noqa: E402
    DemandTicket,
    KnowledgeRecord,
    Pod,
    SkillFamily,
    Student,
    User,
)


def get_or_create(db, model, defaults=None, **filters):
    row = db.scalar(select(model).filter_by(**filters))
    if row is None:
        values = {**filters, **(defaults or {})}
        values["data_mode"] = "SIMULATED"
        row = model(**values)
        db.add(row)
        db.flush()
    return row


def seed() -> None:
    create_all()
    with SessionLocal() as db:
        aliases = json.loads((BACKEND_ROOT / "app" / "data" / "skill_aliases.json").read_text(encoding="utf-8"))
        families = {}
        for slug, item in aliases.items():
            families[slug] = get_or_create(
                db,
                SkillFamily,
                slug=slug,
                defaults={"canonical_name": item["canonical_name"], "aliases": item["aliases"]},
            )

        facilitator = get_or_create(db, User, name="Teacher Meena", role="facilitator")
        employers = [
            get_or_create(db, User, name=name, role="employer")
            for name in ("Shop A", "Shop B", "Shop C")
        ]
        ravi = get_or_create(db, User, name="Ravi", role="student", defaults={"age_band": "18_plus", "interests": ["mobile_repair"]})
        kavya = get_or_create(db, User, name="Kavya", role="student", defaults={"age_band": "14_17", "interests": ["mobile_repair"]})
        for user, age_band in ((ravi, "18_plus"), (kavya, "14_17")):
            get_or_create(db, Student, user_id=user.id, defaults={"age_band": age_band, "interests": ["mobile_repair"]})

        for employer, index in zip(employers, range(1, 4)):
            get_or_create(
                db,
                DemandTicket,
                employer_name=employer.name,
                demand_type="employment",
                status="confirmed",
                defaults={
                    "employer_contact": employer.id,
                    "source_type": "demo",
                    "confirmed_skill_id": families["mobile_repair"].id,
                    "slots_confirmed": 2,
                    "block_code": "demo-block-01",
                    "confirmed_by": facilitator.id,
                    "confirmed_at": datetime.now(timezone.utc),
                },
            )
        get_or_create(
            db,
            DemandTicket,
            employer_name="Training Centre",
            demand_type="training",
            status="confirmed",
            defaults={
                "source_type": "demo",
                "confirmed_skill_id": families["tailoring"].id,
                "slots_confirmed": 5,
                "block_code": "demo-block-01",
                "confirmed_by": facilitator.id,
                "confirmed_at": datetime.now(timezone.utc),
            },
        )
        get_or_create(
            db,
            DemandTicket,
            employer_name="Unknown Employer",
            demand_type="employment",
            status="needs_confirmation",
            defaults={"source_type": "demo", "confirmed_skill_id": families["mobile_repair"].id, "missing_fields": ["pay"]},
        )
        get_or_create(
            db,
            Pod,
            name="Mobile repair practice (supervised)",
            skill_family_id=families["mobile_repair"].id,
            block_code="demo-block-01",
            defaults={
                "threshold_slots": 5,
                "pod_mode": "supervised_practice",
                "status": "open",
                "facilitator_user_id": facilitator.id,
            },
        )

        records = json.loads((BACKEND_ROOT / "seed" / "knowledge_records.json").read_text(encoding="utf-8"))
        for item in records:
            item["last_checked_at"] = date.fromisoformat(item["last_checked_at"])
            if item["valid_until"] is not None:
                item["valid_until"] = date.fromisoformat(item["valid_until"])
            get_or_create(db, KnowledgeRecord, id=item["id"], defaults={**item, "data_mode": "SIMULATED"})
        db.commit()
        print("Seeded users:")
        for user in (facilitator, *employers, ravi, kavya):
            print(f"{user.name}: {user.id}")


if __name__ == "__main__":
    seed()
