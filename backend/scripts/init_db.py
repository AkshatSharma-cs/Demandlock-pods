from __future__ import annotations

import json
import sys
import time
from datetime import date
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import settings  # noqa: E402
from app.db import SessionLocal, create_all, engine  # noqa: E402
from app.models import Block, KnowledgeRecord, SkillFamily  # noqa: E402


def wait_for_db() -> None:
    for attempt in range(30):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return
        except OperationalError:
            if attempt == 29:
                raise
            time.sleep(1)


def load_reference_data() -> None:
    with SessionLocal() as db:
        aliases = json.loads(
            (BACKEND_ROOT / "app" / "data" / "skill_aliases.json").read_text(encoding="utf-8")
        )
        for slug, item in aliases.items():
            family = db.scalar(select(SkillFamily).where(SkillFamily.slug == slug))
            if family is None:
                db.add(
                    SkillFamily(
                        slug=slug,
                        canonical_name=item["canonical_name"],
                        aliases=item["aliases"],
                        data_mode="LIVE",
                    )
                )

        records = json.loads(
            (BACKEND_ROOT / "seed" / "knowledge_records.json").read_text(encoding="utf-8")
        )
        for item in records:
            if "REPLACE-WITH-REAL-SOURCE" in (item.get("source_url") or ""):
                continue
            if db.get(KnowledgeRecord, item["id"]) is not None:
                continue
            values = {**item, "data_mode": "LIVE"}
            values["last_checked_at"] = (
                date.fromisoformat(values["last_checked_at"])
                if values.get("last_checked_at")
                else None
            )
            if values.get("valid_until"):
                values["valid_until"] = date.fromisoformat(values["valid_until"])
            db.add(KnowledgeRecord(**values))

        blocks_path = BACKEND_ROOT / "seed" / "blocks.json"
        if blocks_path.exists():
            for item in json.loads(blocks_path.read_text(encoding="utf-8")):
                if db.scalar(select(Block).where(Block.code == item["code"])) is None:
                    db.add(Block(**item, data_mode="LIVE"))
        db.commit()


if __name__ == "__main__":
    wait_for_db()
    create_all()
    load_reference_data()
