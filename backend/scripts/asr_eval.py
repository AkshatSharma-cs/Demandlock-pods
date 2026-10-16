#!/usr/bin/env python3
"""Evaluate faster-whisper ASR plus deterministic ticket extraction."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import os
import platform
import re
import sys
import time
from collections import defaultdict
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.asr import ASRDisabled, ASRUnavailable, transcribe_file  # noqa: E402


CSV_COLUMNS = {
    "file",
    "lang",
    "expected_skill",
    "expected_slots",
    "expected_pay_minor",
    "expected_location",
}

EXPECTED_TO_TICKET = {
    "expected_skill": "skill",
    "expected_slots": "slots",
    "expected_pay_minor": "pay_min_minor",
    "expected_location": "location_text",
}

NUMERIC_FIELDS = {"slots", "pay_min_minor"}
SUPPORTED_LANGUAGES = {"hi", "ta", "en", "te"}


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]

    if hasattr(value, "model_dump"):
        return _json_safe(value.model_dump())

    if hasattr(value, "dict") and callable(value.dict):
        return _json_safe(value.dict())

    return str(value)


def _ticket_mapping(ticket: Any) -> dict[str, Any]:
    if isinstance(ticket, Mapping):
        return dict(ticket)

    if hasattr(ticket, "model_dump") and callable(ticket.model_dump):
        dumped = ticket.model_dump()
        if isinstance(dumped, Mapping):
            return dict(dumped)

    if hasattr(ticket, "dict") and callable(ticket.dict):
        dumped = ticket.dict()
        if isinstance(dumped, Mapping):
            return dict(dumped)

    field_names = (
        "skill",
        "slots",
        "pay_min_minor",
        "location_text",
    )

    values = {
        name: getattr(ticket, name)
        for name in field_names
        if hasattr(ticket, name)
    }

    if values:
        return values

    if hasattr(ticket, "__dict__"):
        return dict(vars(ticket))

    raise TypeError(
        "extract_ticket() did not return a mapping or a ticket-like object"
    )


def _expected_values(row: dict[str, str]) -> dict[str, Any]:
    expected: dict[str, Any] = {}

    for column, field_name in EXPECTED_TO_TICKET.items():
        raw = (row.get(column) or "").strip()

        if not raw:
            continue

        if field_name in NUMERIC_FIELDS:
            try:
                numeric = raw.replace(",", "")

                if not re.fullmatch(r"[+-]?\d+(?:\.0+)?", numeric):
                    raise ValueError

                expected[field_name] = int(float(numeric))

            except ValueError as exc:
                raise ValueError(
                    f"{column} must be a whole number of slots/paise; "
                    f"got {raw!r} for file {row.get('file', '<unknown>')}"
                ) from exc

        else:
            expected[field_name] = raw

    return expected


def _normalize(value: Any, field_name: str) -> Any:
    if value is None:
        return None

    if field_name in NUMERIC_FIELDS:
        if isinstance(value, bool):
            return value

        if isinstance(value, int):
            return value

        if isinstance(value, float):
            return int(value) if value.is_integer() else value

        if isinstance(value, str):
            cleaned = value.strip().replace(",", "")

            if re.fullmatch(r"[+-]?\d+(?:\.0+)?", cleaned):
                return int(float(cleaned))

            return " ".join(value.casefold().split())

        return _json_safe(value)

    if field_name in {"skill", "location_text"} and isinstance(value, str):
        return " ".join(value.casefold().split())

    return _json_safe(value)


def _display(value: Any) -> str:
    if value is None or value == "":
        return "—"

    if isinstance(value, (dict, list, tuple)):
        result = json.dumps(
            _json_safe(value),
            ensure_ascii=False,
            sort_keys=True,
        )
    else:
        result = str(value)

    return " ".join(result.replace("|", "/").split())


def _load_refs(refs_path: Path) -> list[dict[str, str]]:
    if not refs_path.is_file():
        raise FileNotFoundError(
            f"Reference CSV does not exist: {refs_path}"
        )

    with refs_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = sorted(CSV_COLUMNS - columns)

        if missing:
            raise ValueError(
                "Reference CSV is missing columns: " + ", ".join(missing)
            )

        rows: list[dict[str, str]] = []

        for line_number, raw_row in enumerate(reader, start=2):
            row = {
                key: (raw_row.get(key) or "").strip()
                for key in CSV_COLUMNS
            }

            if not row["file"]:
                raise ValueError(
                    f"Reference CSV line {line_number} has a blank file name"
                )

            row["lang"] = row["lang"].lower()

            if row["lang"] not in SUPPORTED_LANGUAGES:
                raise ValueError(
                    f"Reference CSV line {line_number} has unsupported "
                    f"lang {row['lang']!r}; use one of "
                    f"{', '.join(sorted(SUPPORTED_LANGUAGES))}"
                )

            # Validate expected numeric values before starting ASR.
            _expected_values(row)
            rows.append(row)

    if not rows:
        raise ValueError(f"Reference CSV has no data rows: {refs_path}")

    return rows


def _base_result(
    row: dict[str, str],
    audio_path: Path,
) -> dict[str, Any]:
    return {
        "file": row["file"],
        "lang": row["lang"],
        "audio_path": str(audio_path),
        "expected": _expected_values(row),
        "transcript": "",
        "duration_s": None,
        "elapsed_s": None,
        "real_time_factor": None,
        "extracted": {
            "skill": None,
            "slots": None,
            "pay_min_minor": None,
            "location_text": None,
        },
        "checked_fields": {},
        "passed": False,
        "error": None,
    }


def _check_result(
    expected: dict[str, Any],
    extracted: dict[str, Any],
) -> dict[str, Any]:
    checked: dict[str, Any] = {}

    for field_name, expected_value in expected.items():
        actual_value = extracted.get(field_name)

        passed = (
            _normalize(expected_value, field_name)
            == _normalize(actual_value, field_name)
        )

        checked[field_name] = {
            "expected": _json_safe(expected_value),
            "actual": _json_safe(actual_value),
            "passed": passed,
        }

    return checked


def _print_clip_row(result: dict[str, Any]) -> None:
    transcript = _display(result.get("transcript"))
    extracted = result.get("extracted") or {}

    extracted_summary = "/".join(
        _display(extracted.get(field))
        for field in ("skill", "slots", "pay_min_minor")
    )

    status = "PASS" if result.get("passed") else "FAIL"

    rtf = result.get("real_time_factor")
    rtf_text = f"{rtf:.3f}x" if isinstance(rtf, (int, float)) else "n/a"

    print(
        f"{result.get('file', '')} | "
        f"{result.get('lang', '')} | "
        f"{transcript} | "
        f"{extracted_summary} | "
        f"{status} | "
        f"{rtf_text}"
    )


def _summarize_by_language(
    rows: list[dict[str, str]],
    results: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    pass_counts: dict[str, int] = defaultdict(int)
    total_counts: dict[str, int] = defaultdict(int)

    for row, result in zip(rows, results):
        lang = row["lang"]
        total_counts[lang] += 1

        if result.get("passed"):
            pass_counts[lang] += 1

    summary: dict[str, dict[str, Any]] = {}

    for lang in sorted(total_counts):
        total = total_counts[lang]
        passes = pass_counts[lang]

        # Four of five clips, or at least 80% for a different sample size.
        threshold = math.ceil(0.8 * total)
        go = total > 0 and passes >= threshold

        summary[lang] = {
            "passes": passes,
            "total": total,
            "required_passes": threshold,
            "go": go,
            "decision": (
                "GO" if go else "NO-GO: use typed input"
            ),
        }

    return summary


def _write_report(
    report_path: Path,
    report: dict[str, Any],
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report_path.write_text(
        json.dumps(
            _json_safe(report),
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )


def _print_summaries(
    summary: dict[str, dict[str, Any]],
) -> None:
    print("\nPer-language decision:")

    for lang, item in summary.items():
        print(
            f"{lang}: {item['passes']}/{item['total']} passed; "
            f"required {item['required_passes']} — {item['decision']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate faster-whisper ASR plus deterministic ticket extraction."
        )
    )

    parser.add_argument(
        "--audio_dir",
        required=True,
        help="Directory containing reference audio clips",
    )
    parser.add_argument(
        "--refs",
        required=True,
        help="Reference CSV with expected ticket fields",
    )
    parser.add_argument(
        "--model",
        default="small",
        help="faster-whisper model size (default: small)",
    )
    parser.add_argument(
        "--report",
        default="asr_report.json",
        help="JSON report path",
    )

    args = parser.parse_args()

    started_at = datetime.now(timezone.utc).isoformat()
    wall_started = time.perf_counter()
    cpu_info = platform.processor() or "unknown"

    audio_dir = Path(args.audio_dir)
    refs_path = Path(args.refs)
    report_path = Path(args.report)

    try:
        rows = _load_refs(refs_path)
    except (OSError, ValueError, csv.Error) as exc:
        print(f"Could not read reference CSV: {exc}", file=sys.stderr)
        return 2

    startup_error: str | None = None

    if os.environ.get("ENABLE_ASR", "").strip().lower() != "true":
        startup_error = (
            "ASR is disabled. Set ENABLE_ASR=true to enable it; "
            "use typed input otherwise."
        )

    elif importlib.util.find_spec("faster_whisper") is None:
        startup_error = (
            "faster-whisper is not installed. Install it with "
            "`python -m pip install faster-whisper`; use typed input meanwhile."
        )

    extract_ticket_fn = None

    if startup_error is None:
        try:
            from app.services.extractor import extract_ticket as extract_ticket_fn
        except Exception as exc:
            startup_error = (
                "Could not load app.services.extractor.extract_ticket: "
                f"{type(exc).__name__}: {exc}"
            )

    results: list[dict[str, Any]] = []
    fatal_asr_error: str | None = startup_error

    print(
        "file | lang | transcript | extracted skill/slots/pay | "
        "PASS/FAIL | real-time factor (elapsed/duration)"
    )

    for row in rows:
        audio_path = audio_dir / row["file"]
        result = _base_result(row, audio_path)

        if fatal_asr_error:
            result["error"] = fatal_asr_error
            results.append(result)
            _print_clip_row(result)
            continue

        if not audio_path.is_file():
            result["error"] = f"Audio file not found: {audio_path}"
            results.append(result)
            _print_clip_row(result)
            continue

        try:
            transcription = transcribe_file(
                str(audio_path),
                language=row["lang"],
                model_size=args.model,
            )

            result["transcript"] = transcription.get("text") or ""
            result["duration_s"] = transcription.get("duration_s")
            result["elapsed_s"] = transcription.get("elapsed_s")

            duration = result["duration_s"]
            elapsed = result["elapsed_s"]

            if (
                isinstance(duration, (int, float))
                and duration > 0
                and isinstance(elapsed, (int, float))
            ):
                result["real_time_factor"] = elapsed / duration

        except (ASRDisabled, ASRUnavailable) as exc:
            result["error"] = str(exc)
            fatal_asr_error = str(exc)
            results.append(result)
            _print_clip_row(result)
            continue

        except Exception as exc:
            result["error"] = (
                f"Transcription failed: {type(exc).__name__}: {exc}"
            )
            results.append(result)
            _print_clip_row(result)
            continue

        try:
            ticket = _ticket_mapping(
                extract_ticket_fn(result["transcript"], row["lang"])
            )

            result["extracted"] = {
                "skill": ticket.get("skill"),
                "slots": ticket.get("slots"),
                "pay_min_minor": ticket.get("pay_min_minor"),
                "location_text": ticket.get("location_text"),
            }

            result["checked_fields"] = _check_result(
                result["expected"],
                result["extracted"],
            )

            result["passed"] = (
                bool(result["checked_fields"])
                and all(
                    check["passed"]
                    for check in result["checked_fields"].values()
                )
            )

            if not result["checked_fields"]:
                result["error"] = (
                    "No non-blank expected fields were provided for comparison."
                )

        except Exception as exc:
            result["error"] = (
                f"Ticket extraction failed: {type(exc).__name__}: {exc}"
            )

        results.append(result)
        _print_clip_row(result)

    language_summary = _summarize_by_language(rows, results)
    total_time_s = time.perf_counter() - wall_started

    report = {
        "started_at_utc": started_at,
        "model": args.model,
        "cpu_info": cpu_info,
        "audio_dir": str(audio_dir),
        "refs": str(refs_path),
        "report_path": str(report_path),
        "enable_asr": os.environ.get("ENABLE_ASR", ""),
        "startup_error": startup_error,
        "total_time_s": total_time_s,
        "language_summary": language_summary,
        "overall_result_by_language": {
            lang: summary["decision"]
            for lang, summary in language_summary.items()
        },
        "clips": results,
    }

    _print_summaries(language_summary)

    print(f"\nModel: {args.model}")
    print(f"CPU: {cpu_info}")
    print(f"Total time: {total_time_s:.2f} s")

    try:
        _write_report(report_path, report)
        print(f"JSON report: {report_path}")
    except OSError as exc:
        print(f"Could not write JSON report: {exc}", file=sys.stderr)
        return 2

    if startup_error:
        print(f"\n{startup_error}", file=sys.stderr)
        return 2

    if any(
        result.get("error", "").startswith(
            "Could not load the faster-whisper"
        )
        for result in results
    ):
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())