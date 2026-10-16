"""Pure child-safety rules for enrolment and outcome recording."""

from __future__ import annotations


VALID_AGE_BANDS = frozenset({
    "under_14",
    "14_17",
    "18_plus",
    "unknown",
})

WORK_STAGES = frozenset({
    "trial_interview_offered",
    "started_work",
    "first_payment_verified",
})

TEACHER_REVIEW_STAGES = frozenset({
    "interest_recorded",
    "task_completed",
})

VALID_STAGES = frozenset({
    "trial_interview_offered",
    "started_work",
    "first_payment_verified",
    "interest_recorded",
    "task_completed",
    "employer_reviewed",
})

SUPERVISED_MODE = "supervised_practice"
WORK_TRIAL_MODE = "work_trial"

REASON_UNDER_14 = (
    "Facilitator must review age-appropriate participation."
)
REASON_MINOR_WORK = (
    "Under 18: supervised practice only; no work stages."
)
REASON_UNKNOWN_AGE = (
    "Age is unknown; enrolment is blocked."
)
REASON_UNKNOWN_AGE_OUTCOME = (
    "Age is unknown; outcome recording is blocked."
)
REASON_UNKNOWN_MODE = (
    "Pod mode is unknown; enrolment is blocked."
)
REASON_MINOR_MODE = (
    "Minors may enrol only in supervised practice."
)
REASON_SUPERVISED_ALLOWED = (
    "Supervised practice only."
)
REASON_ADULT_CHECKS = (
    "Adult eligibility checks still required."
)
REASON_MINOR_REVIEW = (
    "Minors are reviewed by teachers only."
)
REASON_TEACHER_CONFIRMATION = (
    "Teacher confirmation required for minors."
)
REASON_STAGE_UNKNOWN = (
    "Unknown stage; outcome recording is blocked."
)


def can_enrol(
    age_band: str,
    pod_mode: str | None,
) -> tuple[bool, str]:
    """Check enrolment using explicit age and pod-mode values.

    A missing or unrecognized mode is never defaulted to a permissive mode.
    """
    if age_band == "under_14":
        return False, REASON_UNDER_14

    if age_band == "unknown" or age_band not in VALID_AGE_BANDS:
        return False, REASON_UNKNOWN_AGE

    if pod_mode not in {SUPERVISED_MODE, WORK_TRIAL_MODE}:
        return False, REASON_UNKNOWN_MODE

    if age_band == "14_17":
        if pod_mode == SUPERVISED_MODE:
            return True, REASON_SUPERVISED_ALLOWED

        return False, REASON_MINOR_MODE

    if age_band == "18_plus":
        return True, REASON_ADULT_CHECKS

    return False, REASON_UNKNOWN_AGE


def can_record_outcome(
    age_band: str,
    stage: str,
) -> tuple[bool, str]:
    """Check whether a lifecycle outcome may be recorded.

    For minors, interest_recorded and task_completed are the only permitted
    outcome categories; the caller must ensure that the required teacher
    confirmation has actually occurred before recording them.
    """
    if stage not in VALID_STAGES:
        return False, REASON_STAGE_UNKNOWN

    if age_band == "18_plus":
        return True, REASON_ADULT_CHECKS

    if stage in WORK_STAGES:
        return False, REASON_MINOR_WORK

    if age_band not in VALID_AGE_BANDS or age_band == "unknown":
        return False, REASON_UNKNOWN_AGE_OUTCOME

    if stage == "employer_reviewed":
        return False, REASON_MINOR_REVIEW

    if stage in TEACHER_REVIEW_STAGES:
        return True, REASON_TEACHER_CONFIRMATION

    return False, REASON_STAGE_UNKNOWN