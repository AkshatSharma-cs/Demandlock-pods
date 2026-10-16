import json
import sys
import unicodedata
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.extractor import extract_ticket


def assert_common(result):
    assert result["verification_status"] == "unverified"
    assert result["needs_confirmation"] is True
    assert "age_eligibility" in result["missing_fields"]


@pytest.mark.parametrize(
    ("transcript", "expected"),
    [
        (
            "मुझे मोबाइल स्क्रीन रिपेयर के लिए 2 हेल्पर चाहिए, जगह तांबरम, वेतन 12000 रुपये महीना।",
            {
                "skill_family_id": "mobile_repair",
                "demand_type": "employment",
                "slots_requested": 2,
                "pay_min_minor": 1200000,
                "pay_max_minor": 1200000,
                "pay_period": "monthly",
                "location_text": "Tambaram",
            },
        ),
        (
            "सिलाई का काम सीखने के लिए 5 लड़कियों को प्रशिक्षण चाहिए।",
            {
                "skill_family_id": "tailoring",
                "demand_type": "training",
                "slots_requested": 5,
                "pay_min_minor": None,
                "pay_max_minor": None,
            },
        ),
        (
            "सोलर पैनल की मरम्मत के लिए दो लोग चाहिए, रोज़ 500 रुपये, अवधि 10 दिन।",
            {
                "skill_family_id": "solar_maintenance",
                "demand_type": "employment",
                "slots_requested": 2,
                "pay_min_minor": 50000,
                "pay_max_minor": 50000,
                "pay_period": "daily",
                "duration_days": 10,
                "location_text": None,
            },
        ),
        (
            "दुकान में कंप्यूटर ऑपरेटर चाहिए। अनुभव जरूरी है।",
            {
                "skill_family_id": "digital_services",
                "demand_type": "employment",
                "slots_requested": None,
                "pay_min_minor": None,
                "pay_max_minor": None,
                "location_text": None,
                "requirements": ["experience_required"],
            },
        ),
        (
            "மொபைல் திரை பழுது பார்க்க இரண்டு உதவியாளர்கள் தேவை. இடம் தாம்பரம். மாதம் 12000 ரூபாய்.",
            {
                "skill_family_id": "mobile_repair",
                "demand_type": "employment",
                "slots_requested": 2,
                "pay_min_minor": 1200000,
                "pay_max_minor": 1200000,
                "pay_period": "monthly",
                "location_text": "Tambaram",
            },
        ),
        (
            "தையல் பயிற்சிக்கு ஐந்து மாணவர்கள் வேண்டும். பயிற்சி இலவசம்.",
            {
                "skill_family_id": "tailoring",
                "demand_type": "training",
                "slots_requested": 5,
                "pay_min_minor": None,
                "pay_max_minor": None,
                "flags": ["training_free"],
            },
        ),
        (
            "சோலார் பேனல் பராமரிப்புக்கு இரண்டு பேர் தேவை. தினம் 500 ரூபாய்.",
            {
                "skill_family_id": "solar_maintenance",
                "demand_type": "employment",
                "slots_requested": 2,
                "pay_min_minor": 50000,
                "pay_max_minor": 50000,
                "pay_period": "daily",
                "duration_days": None,
                "location_text": None,
            },
        ),
        (
            "கணினி வேலைக்கு ஆட்கள் தேவை. சம்பளம் இன்னும் முடிவு செய்யவில்லை.",
            {
                "skill_family_id": "digital_services",
                "demand_type": "employment",
                "slots_requested": None,
                "pay_min_minor": None,
                "pay_max_minor": None,
                "flags": ["pay_undecided"],
            },
        ),
        (
            "Need 3 kitchen helpers in Chengalpattu for 7 days, Rs 600 per day. No experience needed.",
            {
                "skill_family_id": "food_service",
                "demand_type": "employment",
                "slots_requested": 3,
                "pay_min_minor": 60000,
                "pay_max_minor": 60000,
                "pay_period": "daily",
                "duration_days": 7,
                "location_text": "Chengalpattu",
                "requirements": ["no_experience_needed"],
            },
        ),
        (
            "Looking for two mobile screen repair assistants. Location and salary to be decided.",
            {
                "skill_family_id": "mobile_repair",
                "demand_type": "employment",
                "slots_requested": 2,
                "pay_min_minor": None,
                "pay_max_minor": None,
                "location_text": None,
                "flags": ["pay_undecided", "location_undecided"],
            },
        ),
    ],
)
def test_extract_ticket(transcript, expected):
    result = extract_ticket(transcript)
    for field, value in expected.items():
        assert result[field] == value
    assert_common(result)


def _script_name(character):
    try:
        return unicodedata.name(character)
    except ValueError:
        return ""


def test_every_alias_uses_one_script():
    data = json.loads(
        (BACKEND_DIR / "app/data/skill_aliases.json").read_text(encoding="utf-8")
    )
    for family in data.values():
        for language, aliases in family["aliases"].items():
            for alias in aliases:
                if language == "en":
                    assert alias.isascii()
                elif language == "hi":
                    assert not any("஀" <= char <= "௿" for char in alias)
                    assert not any(
                        _script_name(character).startswith("LATIN")
                        for character in alias
                    )
                elif language == "ta":
                    assert not any("ऀ" <= char <= "ॿ" for char in alias)
                    assert not any(
                        _script_name(character).startswith("LATIN")
                        for character in alias
                    )


@pytest.mark.parametrize(
    "transcript",
    [
        "सिलाई प्रशिक्षण के लिए 5 लड़कियां चाहिए।",
        "தையல் பயிற்சிக்கு ஐந்து மாணவர்கள் வேண்டும்.",
        "sewing training for five students",
    ],
)
def test_training_never_becomes_employment(transcript):
    result = extract_ticket(transcript)
    assert result["demand_type"] == "training"
    assert_common(result)


def test_pay_figure_is_not_returned_as_slots():
    result = extract_ticket("Salary is 10000 rupees per month for two helpers.")
    assert result["slots_requested"] == 2
    assert result["pay_min_minor"] == 1000000
    assert result["pay_max_minor"] == 1000000
    assert_common(result)


def test_empty_string_returns_all_none_extractable_fields():
    result = extract_ticket("")
    assert result["skill_family_id"] is None
    assert result["slots_requested"] is None
    assert result["pay_min_minor"] is None
    assert result["pay_max_minor"] is None
    assert result["location_text"] is None
    assert result["duration_days"] is None
    assert result["age_min"] is None
    assert result["age_max"] is None
    assert result["skill_candidates"] == []
    assert result["requirements"] == []
    assert result["flags"] == []
    assert set(result["missing_fields"]) == {
        "skill",
        "slots",
        "pay",
        "location",
        "duration",
        "age_eligibility",
    }
    assert_common(result)