import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.retrieval import (
    build_claims,
    explain_unknown,
    retrieve,
    retrieve_with_fallback,
)


TODAY = "2026-10-16"


def record(
    record_id,
    *,
    family="mobile_repair",
    status="verified",
    language_codes=None,
    title="Mobile screen repair",
    description="Repair mobile screen",
    last_checked_at="2026-10-15",
    valid_until=None,
    source_url="https://example.invalid/official",
    eligibility_json=None,
    benefits_json=None,
):
    return {
        "id": record_id,
        "record_type": "occupation",
        "title": title,
        "authority": "Simulated authority for testing",
        "description": description,
        "source_url": source_url,
        "last_checked_at": last_checked_at,
        "skill_family_ids": [family],
        "language_codes": language_codes or ["en"],
        "eligibility_json": eligibility_json or {},
        "benefits_json": benefits_json or {},
        "verification_status": status,
        "valid_until": valid_until,
    }


def test_verified_records_rank_before_unverified_despite_other_signals():
    records = [
        record(
            "unverified",
            status="unverified",
            language_codes=["en"],
            title="Mobile screen repair",
            last_checked_at="2026-10-16",
        ),
        record(
            "verified",
            status="verified",
            language_codes=["ta"],
            title="Unrelated occupation",
            last_checked_at="2025-01-01",
        ),
    ]

    results = retrieve(
        records,
        "mobile_repair",
        language="en",
        query="mobile screen repair",
        today=TODAY,
    )

    assert [item["id"] for item in results] == [
        "verified",
        "unverified",
    ]


def test_language_match_ranks_before_keyword_overlap():
    records = [
        record(
            "no_language_match",
            language_codes=["ta"],
            title="Mobile screen repair",
        ),
        record(
            "language_match",
            language_codes=["en"],
            title="Different occupation",
        ),
    ]

    results = retrieve(
        records,
        "mobile_repair",
        language="en",
        query="mobile screen repair",
        today=TODAY,
    )

    assert [item["id"] for item in results] == [
        "language_match",
        "no_language_match",
    ]


def test_keyword_overlap_is_a_tie_breaker():
    records = [
        record(
            "low_overlap",
            title="Tailoring basics",
            description="Learn sewing",
        ),
        record(
            "high_overlap",
            title="Mobile screen repair",
            description="Repair a mobile phone screen",
        ),
    ]

    results = retrieve(
        records,
        "mobile_repair",
        query="mobile screen repair",
        today=TODAY,
    )

    assert [item["id"] for item in results] == [
        "high_overlap",
        "low_overlap",
    ]


def test_recency_breaks_remaining_ties():
    records = [
        record("older", last_checked_at="2026-01-01"),
        record("newer", last_checked_at="2026-10-10"),
    ]

    results = retrieve(
        records,
        "mobile_repair",
        language="en",
        query="mobile screen repair",
        today=TODAY,
    )

    assert [item["id"] for item in results] == ["newer", "older"]


def test_drops_expired_status_and_past_valid_until():
    records = [
        record("active"),
        record("expired_status", status="expired"),
        record("expired_date", valid_until="2026-10-15"),
        record("valid_today", valid_until=TODAY),
    ]

    results = retrieve(
        records,
        "mobile_repair",
        today=TODAY,
    )

    assert {item["id"] for item in results} == {
        "active",
        "valid_today",
    }


def test_drops_malformed_valid_until_fail_closed():
    records = [
        record("valid"),
        record("invalid_date", valid_until="not-a-date"),
    ]

    results = retrieve(
        records,
        "mobile_repair",
        today=TODAY,
    )

    assert [item["id"] for item in results] == ["valid"]


def test_filters_by_skill_family():
    records = [
        record("mobile", family="mobile_repair"),
        record("tailoring", family="tailoring"),
    ]

    results = retrieve(
        records,
        "tailoring",
        today=TODAY,
    )

    assert [item["id"] for item in results] == ["tailoring"]


def test_unrecognized_verification_status_ranks_after_unverified():
    records = [
        record("unknown", status="pending"),
        record("unverified", status="unverified"),
        record("verified", status="verified"),
    ]

    results = retrieve(records, "mobile_repair", today=TODAY)

    assert [item["id"] for item in results] == [
        "verified",
        "unverified",
        "unknown",
    ]


def test_limit_and_empty_results():
    records = [
        record("one"),
        record("two"),
        record("three"),
    ]

    assert len(retrieve(records, "mobile_repair", limit=2)) == 2
    assert retrieve(records, "mobile_repair", limit=0) == []
    assert retrieve(records, "mobile_repair", limit=-1) == []


def test_build_claims_drops_records_without_sources():
    records = [
        record("good"),
        record("missing_source", source_url=""),
        record("missing_date", last_checked_at=""),
        record("invalid_date", last_checked_at="yesterday"),
    ]

    claims = build_claims(records, today=TODAY)

    assert claims
    assert {claim["source_url"] for claim in claims} == {
        "https://example.invalid/official"
    }
    assert all(claim["last_checked_at"] == "2026-10-15" for claim in claims)


def test_build_claims_flags_dates_older_than_90_days():
    exactly_90_days_old = (
        date.fromisoformat(TODAY) - timedelta(days=90)
    ).isoformat()
    older_than_90_days = (
        date.fromisoformat(TODAY) - timedelta(days=91)
    ).isoformat()

    records = [
        record("fresh", title="fresh", last_checked_at=TODAY),
        record("boundary", title="boundary", last_checked_at=exactly_90_days_old),
        record("stale", title="stale", last_checked_at=older_than_90_days),
    ]

    claims = build_claims(records, today=TODAY)

    stale_by_record = {
        claim["claim"].split(" — ", 1)[0]: claim["stale"]
        for claim in claims
        if claim["claim"].endswith(" — description")
    }

    assert stale_by_record == {
        "fresh": False,
        "boundary": False,
        "stale": True,
    }


def test_claims_use_unknown_for_missing_eligibility_amount_and_deadline():
    claims = build_claims(
        [
            record(
                "unknown_values",
                title="Test record",
                description="Simulated test description",
                eligibility_json={},
                benefits_json={},
            )
        ],
        today=TODAY,
    )

    values_by_field = {
        claim["claim"].rsplit(" — ", 1)[-1]: claim["value"]
        for claim in claims
    }

    assert values_by_field["eligibility"] == "unknown"
    assert values_by_field["amount"] == "unknown"
    assert values_by_field["deadline"] == "unknown"


def test_claims_preserve_supplied_eligibility_and_benefits():
    claims = build_claims(
        [
            record(
                "known_values",
                title="Test course",
                eligibility_json={"minimum_age": 18},
                benefits_json={
                    "amount_minor": 125000,
                    "application_deadline": "2026-12-01",
                },
            )
        ],
        today=TODAY,
    )

    by_claim = {claim["claim"]: claim["value"] for claim in claims}

    assert by_claim["Test course — eligibility"] == {
        "minimum_age": 18
    }
    assert by_claim["Test course — benefit: amount_minor"] == 125000
    assert by_claim["Test course — amount"] == 125000
    assert by_claim["Test course — benefit: application_deadline"] == (
        "2026-12-01"
    )
    assert by_claim["Test course — deadline"] == "2026-12-01"


def test_unverified_records_remain_explicitly_unverified():
    claims = build_claims(
        [record("placeholder", status="unverified")],
        today=TODAY,
    )

    assert claims
    assert all(
        item["verification_status"] == "unverified"
        for item in claims
    )


def test_explain_unknown_has_exact_contract():
    assert explain_unknown() == {
        "message": "No verified information available",
        "claims": [],
    }


def test_retrieve_with_fallback_for_unmatched_skill():
    result = retrieve_with_fallback(
        [record("mobile")],
        "digital_services",
        today=TODAY,
    )

    assert result == explain_unknown()


def test_retrieve_with_fallback_returns_matches_when_present():
    records = [record("mobile")]

    result = retrieve_with_fallback(
        records,
        "mobile_repair",
        today=TODAY,
    )

    assert isinstance(result, list)
    assert [item["id"] for item in result] == ["mobile"]


def test_invalid_today_raises_clear_error():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        retrieve([], "mobile_repair", today="tomorrow")


def test_seed_file_has_source_backed_unverified_records():
    seed_path = BACKEND_ROOT / "seed" / "knowledge_records.json"
    records = json.loads(seed_path.read_text(encoding="utf-8"))

    assert len(records) >= 10

    expected_families = {
        "mobile_repair",
        "tailoring",
        "solar_maintenance",
        "food_service",
        "digital_services",
    }

    observed_families = {
        family
        for item in records
        for family in item["skill_family_ids"]
    }

    assert expected_families <= observed_families

    for item in records:
        assert item["source_url"].startswith("https://")
        assert "REPLACE-WITH-REAL-SOURCE" not in item["source_url"]
        assert item["verification_status"] == "unverified"
        assert item["last_checked_at"] == "2026-10-16"
        assert item["valid_until"] is None