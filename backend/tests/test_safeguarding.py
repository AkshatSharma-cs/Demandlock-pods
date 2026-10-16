import sys
from itertools import product
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import pytest

from app.services.safeguarding import (
    REASON_ADULT_CHECKS,
    REASON_MINOR_MODE,
    REASON_MINOR_REVIEW,
    REASON_MINOR_WORK,
    REASON_STAGE_UNKNOWN,
    REASON_SUPERVISED_ALLOWED,
    REASON_TEACHER_CONFIRMATION,
    REASON_UNKNOWN_AGE,
    REASON_UNKNOWN_AGE_OUTCOME,
    REASON_UNKNOWN_MODE,
    REASON_UNDER_14,
    VALID_AGE_BANDS,
    VALID_STAGES,
    WORK_STAGES,
    can_enrol,
    can_record_outcome,
)


AGE_BANDS = ("under_14", "14_17", "18_plus", "unknown")
POD_MODES = ("supervised_practice", "work_trial", None)
STAGES = (
    "trial_interview_offered",
    "started_work",
    "first_payment_verified",
    "interest_recorded",
    "task_completed",
    "employer_reviewed",
)


@pytest.mark.parametrize(
    ("age_band", "pod_mode"),
    list(product(AGE_BANDS, POD_MODES)),
)
def test_can_enrol_exhaustive_age_and_mode_matrix(age_band, pod_mode):
    result = can_enrol(age_band, pod_mode)

    if age_band == "under_14":
        expected = (False, REASON_UNDER_14)

    elif age_band == "unknown":
        expected = (False, REASON_UNKNOWN_AGE)

    elif pod_mode is None:
        expected = (False, REASON_UNKNOWN_MODE)

    elif age_band == "14_17" and pod_mode == "supervised_practice":
        expected = (True, REASON_SUPERVISED_ALLOWED)

    elif age_band == "14_17":
        expected = (False, REASON_MINOR_MODE)

    elif age_band == "18_plus":
        expected = (True, REASON_ADULT_CHECKS)

    else:
        expected = (False, REASON_UNKNOWN_AGE)

    assert result == expected


@pytest.mark.parametrize(
    ("age_band", "stage"),
    list(product(AGE_BANDS, STAGES)),
)
def test_can_record_outcome_exhaustive_age_and_stage_matrix(
    age_band,
    stage,
):
    result = can_record_outcome(age_band, stage)

    if age_band == "18_plus":
        expected = (True, REASON_ADULT_CHECKS)

    elif stage in WORK_STAGES:
        expected = (False, REASON_MINOR_WORK)

    elif age_band == "unknown":
        expected = (False, REASON_UNKNOWN_AGE_OUTCOME)

    elif stage == "employer_reviewed":
        expected = (False, REASON_MINOR_REVIEW)

    elif stage in {"interest_recorded", "task_completed"}:
        expected = (True, REASON_TEACHER_CONFIRMATION)

    else:
        expected = (False, REASON_STAGE_UNKNOWN)

    assert result == expected


@pytest.mark.parametrize("age_band", ["under_14", "14_17", "unknown"])
@pytest.mark.parametrize(
    "stage",
    [
        "trial_interview_offered",
        "started_work",
        "first_payment_verified",
    ],
)
def test_non_adults_cannot_record_work_stages(age_band, stage):
    allowed, reason = can_record_outcome(age_band, stage)

    assert allowed is False
    assert reason == REASON_MINOR_WORK


@pytest.mark.parametrize("age_band", ["under_14", "14_17"])
@pytest.mark.parametrize("stage", ["interest_recorded", "task_completed"])
def test_minor_practice_outcomes_require_teacher_confirmation(
    age_band,
    stage,
):
    allowed, reason = can_record_outcome(age_band, stage)

    assert allowed is True
    assert reason == REASON_TEACHER_CONFIRMATION


@pytest.mark.parametrize("age_band", ["under_14", "14_17", "unknown"])
def test_minors_and_unknown_age_cannot_be_reviewed_by_employers(age_band):
    allowed, reason = can_record_outcome(age_band, "employer_reviewed")

    assert allowed is False

    if age_band == "unknown":
        assert reason == REASON_UNKNOWN_AGE_OUTCOME
    else:
        assert reason == REASON_MINOR_REVIEW


@pytest.mark.parametrize("stage", STAGES)
def test_adults_can_record_all_defined_stages(stage):
    assert can_record_outcome("18_plus", stage) == (
        True,
        REASON_ADULT_CHECKS,
    )


@pytest.mark.parametrize("age_band", ["14_17", "18_plus"])
def test_missing_pod_mode_blocks_enrolment(age_band):
    allowed, reason = can_enrol(age_band, None)

    assert allowed is False
    assert reason == REASON_UNKNOWN_MODE


@pytest.mark.parametrize("bad_mode", ["", "unknown", "automatic", "work"])
def test_invalid_pod_mode_does_not_get_a_permissive_default(bad_mode):
    assert can_enrol("14_17", bad_mode)[0] is False
    assert can_enrol("18_plus", bad_mode)[0] is False


@pytest.mark.parametrize("bad_age", ["", "minor", "25", None])
def test_invalid_age_band_blocks_enrolment(bad_age):
    assert can_enrol(bad_age, "supervised_practice") == (
        False,
        REASON_UNKNOWN_AGE,
    )


def test_invalid_stage_is_blocked_even_for_adults():
    assert can_record_outcome("18_plus", "unrecognized_stage") == (
        False,
        REASON_STAGE_UNKNOWN,
    )


def test_valid_age_bands_and_stages_are_explicit():
    assert VALID_AGE_BANDS == {
        "under_14",
        "14_17",
        "18_plus",
        "unknown",
    }
    assert VALID_STAGES == set(STAGES)