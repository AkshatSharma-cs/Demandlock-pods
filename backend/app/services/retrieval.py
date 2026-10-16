"""Pure, source-grounded retrieval and claim construction."""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any, Mapping


UNKNOWN = "unknown"
CLAIM_MAX_AGE_DAYS = 90

AMOUNT_KEYS = {
    "amount",
    "amount_minor",
    "benefit_amount",
    "benefit_amount_minor",
    "grant_amount",
    "grant_amount_minor",
    "pay",
    "pay_minor",
    "salary",
    "salary_minor",
    "stipend",
    "stipend_minor",
    "wage",
    "wage_minor",
    "monthly_amount",
    "monthly_pay",
    "daily_amount",
    "scholarship_amount",
}

DEADLINE_KEYS = {
    "deadline",
    "application_deadline",
    "application_end",
    "application_end_date",
    "closing_date",
    "closing_deadline",
    "last_date",
    "last_application_date",
}


def _parse_date(value: Any) -> date | None:
    """Parse a YYYY-MM-DD date, returning None when it is absent or invalid."""
    if not isinstance(value, str) or not value.strip():
        return None

    try:
        parsed = date.fromisoformat(value.strip())
    except ValueError:
        return None

    # Enforce the documented date representation.
    if parsed.isoformat() != value.strip():
        return None

    return parsed


def _today(value: str | None) -> date:
    if value is None:
        return date.today()

    parsed = _parse_date(value)
    if parsed is None:
        raise ValueError("today must be a valid YYYY-MM-DD date")

    return parsed


def _tokens(value: Any) -> set[str]:
    if not isinstance(value, str):
        return set()

    return {
        token.casefold()
        for token in re.findall(r"[^\W_]+", value, flags=re.UNICODE)
    }


def _normalized_string(value: Any) -> str:
    return value.strip().casefold() if isinstance(value, str) else ""


def _language_matches(record: Mapping[str, Any], language: str) -> bool:
    requested = _normalized_string(language)
    if not requested:
        return False

    language_codes = record.get("language_codes")
    if not isinstance(language_codes, (list, tuple, set)):
        return False

    return any(
        _normalized_string(code) == requested
        for code in language_codes
    )


def _eligible_for_retrieval(
    record: Mapping[str, Any],
    skill_family_id: str,
    today: date,
) -> bool:
    skill_family_ids = record.get("skill_family_ids")

    if not isinstance(skill_family_ids, (list, tuple, set)):
        return False

    if skill_family_id not in skill_family_ids:
        return False

    if _normalized_string(record.get("verification_status")) == "expired":
        return False

    valid_until = record.get("valid_until")

    if valid_until is not None and valid_until != "":
        parsed_valid_until = _parse_date(valid_until)

        # Fail closed for malformed validity dates.
        if parsed_valid_until is None or parsed_valid_until < today:
            return False

    return True


def retrieve(
    records: list[dict],
    skill_family_id: str,
    language: str = "en",
    limit: int = 5,
    today: str | None = None,
    query: str | None = None,
) -> list[dict]:
    """Filter and rank records using deterministic, source-grounded rules.

    Ranking priority:
      1. Verified records before unverified/other statuses.
      2. Requested language match.
      3. Token overlap with query, as a tie-breaker.
      4. Most recent valid last_checked_at.

    Records are not mutated. A non-positive limit returns an empty list.
    """
    if limit <= 0:
        return []

    current_date = _today(today)
    query_tokens = _tokens(query)
    ranked: list[tuple[tuple[Any, ...], int, dict]] = []

    for original_index, record in enumerate(records):
        if not isinstance(record, dict):
            continue

        if not _eligible_for_retrieval(
            record,
            skill_family_id,
            current_date,
        ):
            continue

        status = _normalized_string(record.get("verification_status"))

        if status == "verified":
            verification_rank = 0
        elif status == "unverified":
            verification_rank = 1
        else:
            verification_rank = 2

        language_rank = 0 if _language_matches(record, language) else 1

        searchable_text = " ".join(
            str(record.get(field) or "")
            for field in ("title", "description")
        )
        overlap = len(query_tokens & _tokens(searchable_text))

        checked_date = _parse_date(record.get("last_checked_at"))
        if checked_date is None:
            checked_date = date.min

        ranking_key = (
            verification_rank,
            language_rank,
            -overlap,
            -checked_date.toordinal(),
        )

        ranked.append((ranking_key, original_index, record))

    ranked.sort(key=lambda item: (item[0], item[1]))

    return [
        dict(item[2])
        for item in ranked[:limit]
    ]


def _replace_missing_values(value: Any) -> Any:
    """Represent missing structured values explicitly without inventing facts."""
    if value is None:
        return UNKNOWN

    if isinstance(value, str):
        return value if value.strip() else UNKNOWN

    if isinstance(value, Mapping):
        if not value:
            return UNKNOWN

        return {
            str(key): _replace_missing_values(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [_replace_missing_values(item) for item in value]

    if isinstance(value, tuple):
        return [_replace_missing_values(item) for item in value]

    return value


def _find_value(
    mappings: list[Mapping[str, Any]],
    accepted_keys: set[str],
) -> Any:
    for mapping in mappings:
        for key, value in mapping.items():
            normalized_key = str(key).strip().casefold()

            if normalized_key not in accepted_keys:
                continue

            if value is None or (
                isinstance(value, str) and not value.strip()
            ):
                return UNKNOWN

            return _replace_missing_values(value)

    return UNKNOWN


def _claim(
    title: str,
    field: str,
    value: Any,
    source_url: str,
    last_checked_at: str,
    verification_status: str,
    stale: bool,
) -> dict[str, Any]:
    return {
        "claim": f"{title} — {field}",
        "value": _replace_missing_values(value),
        "source_url": source_url,
        "last_checked_at": last_checked_at,
        "verification_status": verification_status,
        "stale": stale,
    }


def build_claims(
    records: list[dict],
    today: str | None = None,
) -> list[dict]:
    """Convert usable records into claims with source and freshness metadata.

    A record lacking a non-empty source_url or valid last_checked_at is
    discarded entirely. Missing eligibility, amount, and deadline values
    are represented as the literal string "unknown".
    """
    current_date = _today(today)
    claims: list[dict[str, Any]] = []

    for record in records:
        if not isinstance(record, dict):
            continue

        source_url = record.get("source_url")
        checked_raw = record.get("last_checked_at")

        if not isinstance(source_url, str) or not source_url.strip():
            continue

        checked_date = _parse_date(checked_raw)
        if checked_date is None:
            continue

        last_checked_at = checked_date.isoformat()
        stale = current_date - checked_date > timedelta(
            days=CLAIM_MAX_AGE_DAYS
        )

        title_value = record.get("title")
        title = (
            title_value.strip()
            if isinstance(title_value, str) and title_value.strip()
            else UNKNOWN
        )

        status_value = record.get("verification_status")
        verification_status = (
            status_value.strip()
            if isinstance(status_value, str) and status_value.strip()
            else UNKNOWN
        )

        eligibility = record.get("eligibility_json")
        if not isinstance(eligibility, Mapping):
            eligibility = {}

        benefits = record.get("benefits_json")
        if not isinstance(benefits, Mapping):
            benefits = {}

        description = record.get("description")
        claims.append(
            _claim(
                title,
                "description",
                description,
                source_url,
                last_checked_at,
                verification_status,
                stale,
            )
        )

        claims.append(
            _claim(
                title,
                "eligibility",
                eligibility if eligibility else UNKNOWN,
                source_url,
                last_checked_at,
                verification_status,
                stale,
            )
        )

        # Preserve every supplied benefit field in addition to emitting
        # explicit amount/deadline claims, including when those are unknown.
        for key, value in benefits.items():
            claims.append(
                _claim(
                    title,
                    f"benefit: {key}",
                    value,
                    source_url,
                    last_checked_at,
                    verification_status,
                    stale,
                )
            )

        claims.append(
            _claim(
                title,
                "amount",
                _find_value([benefits], AMOUNT_KEYS),
                source_url,
                last_checked_at,
                verification_status,
                stale,
            )
        )

        claims.append(
            _claim(
                title,
                "deadline",
                _find_value([eligibility, benefits], DEADLINE_KEYS),
                source_url,
                last_checked_at,
                verification_status,
                stale,
            )
        )

    return claims


def explain_unknown() -> dict[str, Any]:
    return {
        "message": "No verified information available",
        "claims": [],
    }


def retrieve_with_fallback(
    records: list[dict],
    skill_family_id: str,
    language: str = "en",
    limit: int = 5,
    today: str | None = None,
    query: str | None = None,
) -> list[dict] | dict[str, Any]:
    """Return matching records, or an explicit unknown response if none match."""
    matches = retrieve(
        records=records,
        skill_family_id=skill_family_id,
        language=language,
        limit=limit,
        today=today,
        query=query,
    )

    if not matches:
        return explain_unknown()

    return matches