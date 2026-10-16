import json
import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.llm import SYSTEM_PROMPT, enhance_ticket


class FakeLLMClient:
    def __init__(self, value):
        self.value = value

    def complete_json(self, system, user, timeout_s=20):
        assert system == SYSTEM_PROMPT
        return self.value


def base_result():
    return {
        "skill_family_id": None,
        "slots_requested": None,
        "pay_min_minor": None,
        "location_text": None,
        "field_sources": {},
        "verification_status": "unverified",
    }


def test_flag_off_returns_same_object(monkeypatch):
    monkeypatch.delenv("ENABLE_LLM_EXTRACTION", raising=False)
    result = base_result()
    assert enhance_ticket("Need two helpers", result, FakeLLMClient({})) is result


def test_valid_llm_values_fill_only_unknown_fields(monkeypatch):
    monkeypatch.setenv("ENABLE_LLM_EXTRACTION", "true")
    transcript = "Need two mobile repair helpers"
    candidate = {
        "skill_family_id": "mobile_repair",
        "slots_requested": 2,
        "field_evidence": {
            "skill_family_id": "mobile repair",
            "slots_requested": "two",
        },
    }
    result = enhance_ticket(transcript, base_result(), FakeLLMClient(candidate))
    assert result["skill_family_id"] == "mobile_repair"
    assert result["slots_requested"] == 2
    assert result["field_sources"]["slots_requested"] == "llm"
    assert result["verification_status"] == "unverified"


def test_rule_value_is_not_overridden(monkeypatch):
    monkeypatch.setenv("ENABLE_LLM_EXTRACTION", "true")
    result = base_result()
    result["slots_requested"] = 3
    candidate = {"slots_requested": 2, "field_evidence": {"slots_requested": "two"}}
    assert enhance_ticket("Need two helpers", result, FakeLLMClient(candidate))["slots_requested"] == 3


@pytest.mark.parametrize(
    "candidate",
    [
        {"slots_requested": 2, "field_evidence": {"slots_requested": "absent"}},
        {"slots_requested": 201, "field_evidence": {"slots_requested": "201"}},
        {"skill_family_id": "invented", "field_evidence": {"skill_family_id": "invented"}},
    ],
)
def test_invalid_candidate_falls_back(monkeypatch, candidate):
    monkeypatch.setenv("ENABLE_LLM_EXTRACTION", "true")
    result = base_result()
    assert enhance_ticket("Need two helpers", result, FakeLLMClient(candidate)) == result


def test_client_error_falls_back(monkeypatch):
    monkeypatch.setenv("ENABLE_LLM_EXTRACTION", "true")

    class FailingClient:
        def complete_json(self, system, user, timeout_s=20):
            raise TimeoutError

    result = base_result()
    assert enhance_ticket("Need helpers", result, FailingClient()) == result
