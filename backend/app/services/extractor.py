import json
import re
import sys
import unicodedata
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

_DATA = None
_NUMBER_MAPS = None

_TOKEN_EDGE_PUNCT = " \t\r\n.,;:!?।॥'\"“”‘’()[]{}<>"
_RANGE_SEPARATORS = {"to", "-", "–", "—", "से", "முதல்"}
_SLOT_VALUES = set(range(1, 21)) | {25, 30, 40, 50}
_ATTACHED_CURRENCY_PREFIXES = (
    "ரூபாய்",
    "rupees",
    "रुपये",
    "रुपए",
    "₹",
    "rs.",
    "rs",
    "ரூ",
    "रु",
)
_ATTACHED_CURRENCY_SUFFIXES = ("/-", "ரூபாய்", "ரூ", "रुपये", "रुपए", "रु")


def _normalize_text(text):
    value = unicodedata.normalize("NFC", str(text))
    value = value.lower()
    return value.replace("़", "").replace("ँ", "ं")


def _read_json(filename):
    with (DATA_DIR / filename).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_data():
    global _DATA
    if _DATA is None:
        _DATA = {
            "skill_aliases": _read_json("skill_aliases.json"),
            "locations": _read_json("locations.json"),
            "number_words": _read_json("number_words.json"),
            "lexicon": _read_json("lexicon.json"),
        }
    return _DATA


def _number_maps():
    global _NUMBER_MAPS
    if _NUMBER_MAPS is None:
        maps = {}
        for language, entries in _load_data()["number_words"].items():
            if not isinstance(entries, dict):
                continue
            numbers = {}
            multipliers = {}
            for word, value in entries.items():
                if not isinstance(value, int):
                    continue
                normalized_word = _normalize_text(word)
                if value in (100, 1000):
                    multipliers[normalized_word] = value
                else:
                    numbers[normalized_word] = value
            maps[language] = {"numbers": numbers, "multipliers": multipliers}
        _NUMBER_MAPS = maps
    return _NUMBER_MAPS


def _detect_language(text):
    for char in text:
        if "ऀ" <= char <= "ॿ":
            return "hi"
    for char in text:
        if "஀" <= char <= "௿":
            return "ta"
    return "en"


def _clean_token(token):
    return token.strip(_TOKEN_EDGE_PUNCT)


def _tokenize(text):
    tokens = []
    for match in re.finditer(r"\S+", text):
        raw = match.group(0)
        tokens.append(
            {
                "text": raw,
                "clean": _clean_token(raw),
                "start": match.start(),
                "end": match.end(),
            }
        )
    return tokens


def _alias_variants(alias, language):
    alias = _normalize_text(alias)
    variants = [alias]
    if language == "ta" and len(alias) > 1 and alias.endswith("ம்"):
        variants.append(alias[:-1])
    return variants


def _find_alias_spans(text, language, alias):
    alias = _normalize_text(alias)
    if not alias:
        return []
    if language == "en":
        pattern = r"(?<!\w)" + re.escape(alias) + r"(?!\w)"
        return [(match.start(), match.end()) for match in re.finditer(pattern, text)]

    spans = []
    for variant in _alias_variants(alias, language):
        start = text.find(variant)
        while start != -1:
            spans.append((start, start + len(variant)))
            start = text.find(variant, start + 1)
    return spans


def _contains_alias(text, language, alias):
    return bool(_find_alias_spans(text, language, alias))


def _token_matches_alias(token, language, alias):
    return bool(_find_alias_spans(token["clean"], language, alias))


def _contains_any_alias(text, aliases):
    for language, entries in aliases.items():
        for alias in entries:
            if _contains_alias(text, language, alias):
                return True
    return False


def _sequence_match_length(tokens, index, language, alias):
    parts = _normalize_text(alias).split()
    if index + len(parts) > len(tokens):
        return 0
    for offset, part in enumerate(parts):
        if not _token_matches_alias(tokens[index + offset], language, part):
            return 0
    return len(parts)


def _spans_intersect(start, end, spans):
    for span_start, span_end in spans:
        if start < span_end and end > span_start:
            return True
    return False


def _all_skill_spans(text, data):
    spans = []
    for family in data["skill_aliases"].values():
        for language, aliases in family.get("aliases", {}).items():
            for alias in aliases:
                spans.extend(_find_alias_spans(text, language, alias))
    return spans


def _extract_skill(text, data):
    matches = []
    for family_id, family in data["skill_aliases"].items():
        matched = False
        for language, aliases in family.get("aliases", {}).items():
            if any(_contains_alias(text, language, alias) for alias in aliases):
                matched = True
                break
        if matched:
            matches.append(family_id)

    if len(matches) == 1:
        return matches[0], [], "keyword_match"
    if len(matches) > 1:
        return None, matches, "keyword_match"
    return None, [], "keyword_match"


def _parse_single_digits(text):
    if re.fullmatch(r"\d+", text):
        return int(text)
    if re.fullmatch(r"\d{1,3}(?:,\d{2,3})+", text):
        return int(text.replace(",", ""))
    return None


def _parse_digit_amount(text):
    if not text:
        return None

    for prefix in _ATTACHED_CURRENCY_PREFIXES:
        if text.startswith(prefix) and len(text) > len(prefix):
            text = text[len(prefix) :]
            break
    for suffix in _ATTACHED_CURRENCY_SUFFIXES:
        if text.endswith(suffix) and len(text) > len(suffix):
            text = text[: -len(suffix)]
            break

    range_match = re.fullmatch(r"([0-9][0-9,]*)\s*[-–—]\s*([0-9][0-9,]*)", text)
    if range_match:
        first = _parse_single_digits(range_match.group(1))
        second = _parse_single_digits(range_match.group(2))
        if first is not None and second is not None:
            return first, second
        return None

    value = _parse_single_digits(text)
    if value is None:
        return None
    return value, value


def _basic_number_at(tokens, index, language, maps):
    numbers = maps.get(language, {"numbers": {}})["numbers"]
    clean = tokens[index]["clean"]
    if clean not in numbers:
        return None

    first = numbers[clean]
    value = first
    consumed = 1
    valid_values = set(numbers.values())

    if index + 1 < len(tokens):
        second = numbers.get(tokens[index + 1]["clean"])
        if (
            second is not None
            and first >= 20
            and 0 < second < 10
            and first + second in valid_values
        ):
            value = first + second
            consumed = 2

    return value, consumed


def _multiplier_at(tokens, index, language, maps):
    if index >= len(tokens):
        return None
    return maps.get(language, {"multipliers": {}})["multipliers"].get(
        tokens[index]["clean"]
    )


def _single_amount_at(tokens, index, language, maps):
    digit_amount = _parse_digit_amount(tokens[index]["clean"])
    if digit_amount is not None:
        low, high = digit_amount
        end = index
        indexes = [index]
        source = "regex"
        multiplier_index = None
        multiplier = _multiplier_at(tokens, index + 1, language, maps)
        if multiplier is not None:
            low *= multiplier
            high *= multiplier
            end = index + 1
            indexes.append(end)
            source = "number_word"
            multiplier_index = end
        return {
            "low": low,
            "high": high,
            "start": index,
            "end": end,
            "indexes": indexes,
            "source": source,
            "multiplier_index": multiplier_index,
        }

    word_amount = _basic_number_at(tokens, index, language, maps)
    if word_amount is not None:
        value, consumed = word_amount
        end = index + consumed - 1
        indexes = list(range(index, end + 1))
        multiplier_index = None
        multiplier = _multiplier_at(tokens, end + 1, language, maps)
        if multiplier is not None:
            value *= multiplier
            multiplier_index = end + 1
            end = multiplier_index
            indexes.append(end)
        return {
            "low": value,
            "high": value,
            "start": index,
            "end": end,
            "indexes": indexes,
            "source": "number_word",
            "multiplier_index": multiplier_index,
        }

    standalone_multiplier = maps.get(language, {"multipliers": {}})["multipliers"].get(
        tokens[index]["clean"]
    )
    if standalone_multiplier is not None:
        return {
            "low": standalone_multiplier,
            "high": standalone_multiplier,
            "start": index,
            "end": index,
            "indexes": [index],
            "source": "number_word",
            "multiplier_index": index,
        }
    return None


def _amount_at(tokens, index, language, maps):
    left = _single_amount_at(tokens, index, language, maps)
    if left is None:
        return None

    low = left["low"]
    high = left["high"]
    end = left["end"]
    indexes = list(left["indexes"])
    source = left["source"]
    multiplier_index = left["multiplier_index"]

    separator_index = end + 1
    if (
        separator_index < len(tokens)
        and tokens[separator_index]["clean"] in _RANGE_SEPARATORS
    ):
        right = _single_amount_at(tokens, separator_index + 1, language, maps)
        if right is not None:
            if (
                multiplier_index is None
                and right["multiplier_index"] is not None
                and right["multiplier_index"] not in right["indexes"][:1]
            ):
                shared_multiplier = _multiplier_at(
                    tokens, right["multiplier_index"], language, maps
                )
                if shared_multiplier is not None:
                    low *= shared_multiplier
                    high *= shared_multiplier
            low = min(low, right["low"])
            high = max(high, right["high"])
            end = right["end"]
            indexes.extend(right["indexes"])
            if right["source"] == "number_word":
                source = "number_word"

    return {
        "low": low,
        "high": high,
        "start": index,
        "end": end,
        "indexes": indexes,
        "source": source,
    }


def _amount_expressions(tokens, language, maps):
    expressions = []
    blocked_indexes = set()
    for index in range(len(tokens)):
        expression = _amount_at(tokens, index, language, maps)
        if expression is None:
            continue
        if any(item in blocked_indexes for item in expression["indexes"]):
            continue
        expressions.append(expression)
        blocked_indexes.update(expression["indexes"])
    return expressions


def _duration_number_at(tokens, index, language, maps):
    digit_amount = _parse_digit_amount(tokens[index]["clean"])
    if digit_amount is not None and digit_amount[0] == digit_amount[1]:
        if digit_amount[0] > 0:
            return digit_amount[0], "regex"
        return None

    word_amount = _basic_number_at(tokens, index, language, maps)
    if word_amount is not None:
        return word_amount[0], "number_word"

    hundred = maps.get(language, {"multipliers": {}})["multipliers"].get(
        tokens[index]["clean"]
    )
    if hundred == 100:
        return 100, "number_word"
    return None


def _duration_unit_for_token(token, data, language):
    for unit, language_aliases in data["lexicon"]["duration_units"].items():
        for alias in language_aliases.get(language, []):
            if _token_matches_alias(token, language, alias):
                return unit
    return None


def _duration_guard_indexes(tokens, data, language, maps):
    guarded = set()
    for index in range(len(tokens) - 1):
        if _duration_number_at(tokens, index, language, maps) is None:
            continue
        if _duration_unit_for_token(tokens[index + 1], data, language) is not None:
            guarded.add(index)
            guarded.add(index + 1)
    return guarded


def _currency_guarded_indexes(tokens, data, language, maps):
    guarded = set()
    currency_aliases = data["lexicon"]["currency"].get(language, [])
    for index, token in enumerate(tokens):
        if not any(
            _token_matches_alias(token, language, alias) for alias in currency_aliases
        ):
            continue
        for nearby in range(max(0, index - 1), min(len(tokens), index + 2)):
            clean = tokens[nearby]["clean"]
            if (
                _parse_single_digits(clean) is not None
                or _basic_number_at(tokens, nearby, language, maps) is not None
                or maps.get(language, {"multipliers": {}})["multipliers"].get(clean)
                is not None
            ):
                guarded.add(nearby)
    return guarded


def _slot_number_at(tokens, index, language, maps):
    digit_amount = _parse_digit_amount(tokens[index]["clean"])
    if digit_amount is not None and digit_amount[0] == digit_amount[1]:
        value = digit_amount[0]
        if 1 <= value <= 200:
            return value, "regex"
        return None

    word_amount = _basic_number_at(tokens, index, language, maps)
    if word_amount is not None and word_amount[0] in _SLOT_VALUES:
        return word_amount[0], "number_word"
    return None


def _is_sentence_end(token):
    return token["text"].endswith((".", "।", "!", "?", "॥"))


def _people_noun_indexes(tokens, data, language):
    indexes = []
    aliases = data["lexicon"]["people_nouns"].get(language, [])
    for index, token in enumerate(tokens):
        if any(_token_matches_alias(token, language, alias) for alias in aliases):
            indexes.append(index)
    return indexes


def _extract_slots(tokens, skill_spans, data, language, maps, excluded_indexes):
    candidates = []
    candidate_indexes = []

    for noun_index in _people_noun_indexes(tokens, data, language):
        eligible = []
        for index in range(noun_index - 1, max(-1, noun_index - 12), -1):
            if _is_sentence_end(tokens[index]):
                break
            if _spans_intersect(
                tokens[index]["start"], tokens[index]["end"], skill_spans
            ):
                continue
            eligible.append(index)
            if len(eligible) == 3:
                break

        for index in eligible:
            if index in excluded_indexes:
                continue
            parsed = _slot_number_at(tokens, index, language, maps)
            if parsed is None:
                continue
            value, source = parsed
            candidates.append((value, source, index))
            candidate_indexes.append(index)

    if not candidates:
        return {"value": None, "source": None, "candidate_indexes": []}

    values = [candidate[0] for candidate in candidates]
    if len(set(values)) != 1:
        return {
            "value": None,
            "source": None,
            "candidate_indexes": candidate_indexes,
        }

    return {
        "value": values[0],
        "source": candidates[0][1],
        "candidate_indexes": candidate_indexes,
    }


def _expression_near_pay_cue(tokens, expression, data, language):
    start = max(0, expression["start"] - 3)
    end = min(len(tokens) - 1, expression["end"] + 3)
    cue_groups = (data["lexicon"]["currency"], data["lexicon"]["pay_words"])

    for index in range(start, end + 1):
        if index in expression["indexes"]:
            continue
        for group in cue_groups:
            for alias in group.get(language, []):
                if _token_matches_alias(tokens[index], language, alias):
                    return True
    return False


def _period_for_amount(tokens, expression, data, language):
    best = None
    start = max(0, expression["start"] - 4)
    end = min(len(tokens) - 1, expression["end"] + 4)

    for index in range(start, end + 1):
        for period, language_aliases in data["lexicon"]["pay_periods"].items():
            for alias in language_aliases.get(language, []):
                length = _sequence_match_length(tokens, index, language, alias)
                if length == 0:
                    continue
                distance = min(abs(index - item) for item in expression["indexes"])
                candidate = (
                    distance,
                    index,
                    period,
                    list(range(index, index + length)),
                )
                if best is None or candidate[:2] < best[:2]:
                    best = candidate

    if best is None:
        return "unknown", []
    return best[2], best[3]


def _extract_pay(tokens, data, language, maps, slot_result, duration_guard):
    expressions = _amount_expressions(tokens, language, maps)
    slot_indexes = set(slot_result["candidate_indexes"])
    valid = []

    for expression in expressions:
        if slot_indexes.intersection(expression["indexes"]):
            continue
        if duration_guard.intersection(expression["indexes"]):
            continue
        if _expression_near_pay_cue(tokens, expression, data, language):
            valid.append(expression)

    if not valid:
        return None

    chosen = valid[0]
    period, period_indexes = _period_for_amount(tokens, chosen, data, language)
    low = min(chosen["low"], chosen["high"])
    high = max(chosen["low"], chosen["high"])
    return {
        "pay_min_minor": low * 100,
        "pay_max_minor": high * 100,
        "pay_period": period,
        "source": chosen["source"],
        "amount_indexes": chosen["indexes"],
        "period_indexes": period_indexes,
    }


def _extract_duration(
    tokens,
    data,
    language,
    maps,
    pay_amount_indexes,
    pay_period_indexes,
):
    multipliers = {"day": 1, "week": 7, "month": 30}

    for index in range(len(tokens) - 1):
        if index in pay_amount_indexes:
            continue
        parsed = _duration_number_at(tokens, index, language, maps)
        if parsed is None:
            continue
        unit = _duration_unit_for_token(tokens[index + 1], data, language)
        if unit is None or (index + 1) in pay_period_indexes:
            continue
        value, source = parsed
        return {
            "duration_days": value * multipliers[unit],
            "source": source,
        }

    return {"duration_days": None, "source": None}


def _extract_location(text, data):
    for entry in data["locations"]:
        for language, aliases in entry.get("aliases", {}).items():
            if any(_contains_alias(text, language, alias) for alias in aliases):
                return entry["canonical"]
    return None


def _join_pattern(words):
    return "|".join(re.escape(word) for word in sorted(words, key=len, reverse=True))


def _age_value(first, second, source):
    if not 0 < first <= 120 or (second is not None and not 0 < second <= 120):
        return None
    if second is not None and first > second:
        first, second = second, first
    return {"age_min": first, "age_max": second, "source": source}


def _extract_age(text, data, language, maps):
    lexicon = data["lexicon"]
    numbers = maps.get(language, {"numbers": {}})["numbers"]
    number_words = [word for word in numbers if numbers[word] not in (100, 1000)]
    if not number_words:
        return None

    number_pattern = _join_pattern(number_words)
    markers = [_normalize_text(word) for word in lexicon["age_markers"].get(language, [])]
    units = [_normalize_text(word) for word in lexicon["age_units"].get(language, [])]
    if not markers or not units:
        return None

    marker_pattern = _join_pattern(markers)
    unit_pattern = _join_pattern(units)
    range_separator = r"(?:to|-|–|—|से|முதல்)"

    digit_marker = re.search(
        r"(?<!\w)(?:"
        + marker_pattern
        + r")(?!\w)\s*[:.]?\s*(\d{1,3})(?:\s*"
        + range_separator
        + r"\s*(\d{1,3}))?(?!\w)",
        text,
    )
    if digit_marker:
        return _age_value(
            int(digit_marker.group(1)),
            int(digit_marker.group(2)) if digit_marker.group(2) else None,
            "regex",
        )

    digit_years = re.search(
        r"(?<!\w)(\d{1,3})\s*"
        + range_separator
        + r"\s*(\d{1,3})\s*(?:"
        + unit_pattern
        + r")(?!\w)",
        text,
    )
    if digit_years:
        return _age_value(
            int(digit_years.group(1)),
            int(digit_years.group(2)),
            "regex",
        )

    above = re.search(
        r"(?<!\w)(?:above|over)\s+(\d{1,3})(?!\w)"
        r"|(?<!\w)(\d{1,3})\s*(?:से\s*ऊपर|மேல்)(?!\w)",
        text,
    )
    if above:
        value = int(above.group(1) or above.group(2))
        return _age_value(value, None, "regex")

    plus = re.search(r"(?<!\w)(\d{1,3})\s*\+(?!\w)", text)
    if plus:
        return _age_value(int(plus.group(1)), None, "regex")

    word_marker = re.search(
        r"(?<!\w)(?:"
        + marker_pattern
        + r")(?!\w)\s*("
        + number_pattern
        + r")(?:\s*"
        + range_separator
        + r"\s*("
        + number_pattern
        + r"))?(?!\w)",
        text,
    )
    if word_marker:
        first = numbers[_normalize_text(word_marker.group(1))]
        second_word = word_marker.group(2)
        second = numbers[_normalize_text(second_word)] if second_word else None
        return _age_value(first, second, "number_word")

    word_years = re.search(
        r"(?<!\w)("
        + number_pattern
        + r")\s*"
        + range_separator
        + r"\s*("
        + number_pattern
        + r")\s*(?:"
        + unit_pattern
        + r")(?!\w)",
        text,
    )
    if word_years:
        first = numbers[_normalize_text(word_years.group(1))]
        second = numbers[_normalize_text(word_years.group(2))]
        return _age_value(first, second, "number_word")

    return None


def _extract_demand_type(text, data):
    training = _contains_any_alias(text, data["lexicon"]["training_cues"])
    contract = _contains_any_alias(text, data["lexicon"]["service_contract_cues"])
    if training:
        return "training"
    if contract:
        return "service_contract"
    return "employment"


def _extract_requirements(text, data):
    if _contains_any_alias(text, data["lexicon"]["experience_negated_cues"]):
        return ["no_experience_needed"]
    if _contains_any_alias(text, data["lexicon"]["experience_required_cues"]):
        return ["experience_required"]
    return []


def _extract_flags(text, data):
    flags = []
    if _contains_any_alias(text, data["lexicon"]["training_free_cues"]):
        flags.append("training_free")
    if _contains_any_alias(text, data["lexicon"]["pay_undecided_cues"]):
        flags.append("pay_undecided")

    location_undecided = _contains_any_alias(
        text, data["lexicon"]["location_undecided_cues"]
    )
    if not location_undecided and re.search(
        r"(?<!\w)location\b[^.।\n]{0,50}\bto\s+be\s+decided\b", text
    ):
        location_undecided = True
    if location_undecided:
        flags.append("location_undecided")
    return flags


def extract_ticket(transcript: str, language: str = "unknown") -> dict:
    original = transcript if isinstance(transcript, str) else str(transcript or "")
    normalized = _normalize_text(original)
    requested_language = str(language or "unknown").lower()
    used_language = (
        _detect_language(normalized)
        if requested_language == "unknown"
        else requested_language
    )
    if used_language not in ("en", "hi", "ta"):
        used_language = _detect_language(normalized)

    data = _load_data()
    maps = _number_maps()
    tokens = _tokenize(normalized)

    demand_type = _extract_demand_type(normalized, data)
    skill_family_id, skill_candidates, skill_source = _extract_skill(normalized, data)
    skill_spans = _all_skill_spans(normalized, data)
    currency_guard = _currency_guarded_indexes(tokens, data, used_language, maps)
    duration_guard = _duration_guard_indexes(tokens, data, used_language, maps)
    slot_result = _extract_slots(
        tokens, skill_spans, data, used_language, maps, currency_guard
    )
    pay_result = _extract_pay(
        tokens, data, used_language, maps, slot_result, duration_guard
    )

    if pay_result is None:
        pay_min_minor = None
        pay_max_minor = None
        pay_period = "unknown"
        pay_source = None
        pay_amount_indexes = []
        pay_period_indexes = []
    else:
        pay_min_minor = pay_result["pay_min_minor"]
        pay_max_minor = pay_result["pay_max_minor"]
        pay_period = pay_result["pay_period"]
        pay_source = pay_result["source"]
        pay_amount_indexes = pay_result["amount_indexes"]
        pay_period_indexes = pay_result["period_indexes"]

    duration_result = _extract_duration(
        tokens,
        data,
        used_language,
        maps,
        set(pay_amount_indexes),
        set(pay_period_indexes),
    )
    location_text = _extract_location(normalized, data)
    age_result = _extract_age(normalized, data, used_language, maps)
    requirements = _extract_requirements(normalized, data)
    flags = _extract_flags(normalized, data)

    field_sources = {}
    if skill_family_id is not None:
        field_sources["skill"] = skill_source
    if slot_result["value"] is not None:
        field_sources["slots"] = slot_result["source"]
    if pay_min_minor is not None:
        field_sources["pay"] = pay_source
    if location_text is not None:
        field_sources["location"] = "location_alias"
    if duration_result["duration_days"] is not None:
        field_sources["duration"] = duration_result["source"]
    if age_result is not None:
        field_sources["age_eligibility"] = age_result["source"]

    age_min = age_result["age_min"] if age_result is not None else None
    age_max = age_result["age_max"] if age_result is not None else None

    missing_fields = []
    if skill_family_id is None:
        missing_fields.append("skill")
    if slot_result["value"] is None:
        missing_fields.append("slots")
    if pay_min_minor is None:
        missing_fields.append("pay")
    if location_text is None:
        missing_fields.append("location")
    if duration_result["duration_days"] is None:
        missing_fields.append("duration")
    if age_result is None:
        missing_fields.append("age_eligibility")

    return {
        "demand_type": demand_type,
        "skill_family_id": skill_family_id,
        "skill_candidates": skill_candidates,
        "slots_requested": slot_result["value"],
        "pay_min_minor": pay_min_minor,
        "pay_max_minor": pay_max_minor,
        "pay_period": pay_period,
        "location_text": location_text,
        "duration_days": duration_result["duration_days"],
        "age_min": age_min,
        "age_max": age_max,
        "requirements": requirements,
        "flags": flags,
        "missing_fields": missing_fields,
        "field_sources": field_sources,
        "verification_status": "unverified",
        "needs_confirmation": True,
        "language": used_language,
    }


def _main():
    if len(sys.argv) < 2:
        result = extract_ticket("")
    else:
        selected_language = sys.argv[2] if len(sys.argv) > 2 else "unknown"
        result = extract_ticket(sys.argv[1], selected_language)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _main()