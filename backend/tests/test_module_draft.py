import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.module_draft import DISCLAIMER, generate_module_draft


@pytest.mark.parametrize(
    "skill_family_id",
    ["mobile_repair", "tailoring", "solar_maintenance", "food_service", "digital_services"],
)
def test_known_skill_has_three_tasks_and_safe_metadata(skill_family_id):
    draft = generate_module_draft(skill_family_id)
    assert len(draft["objectives"]) == 3
    assert len(draft["tasks"]) == 3
    assert all(len(task["rubric"]) == 1 for task in draft["tasks"])
    assert draft["disclaimer"] == DISCLAIMER
    assert draft["ai_generated"] is False
    assert draft["human_reviewed"] is False


def test_unknown_skill_is_marked_for_authoring():
    draft = generate_module_draft("unknown")
    assert "needs_teacher_authoring" in draft["flags"]
    assert len(draft["tasks"]) == 3


def test_non_english_keeps_text_and_requests_translation():
    draft = generate_module_draft("tailoring", language="hi")
    assert draft["language"] == "hi"
    assert draft["needs_translation"] is True


def test_references_only_copy_source_fields():
    draft = generate_module_draft(
        "food_service",
        knowledge_records=[
            {"title": "Guide", "source_url": "https://example.invalid/a", "last_checked_at": "2026-10-16", "secret": "drop"},
            {"title": "Missing URL"},
            "not a record",
        ],
    )
    assert draft["source_references"] == [
        {"title": "Guide", "source_url": "https://example.invalid/a", "last_checked_at": "2026-10-16"}
    ]
