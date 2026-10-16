"""Deterministic, human-reviewable learning module drafts."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


DISCLAIMER = (
    "Practice only. No promise of jobs, income, certification or accreditation."
)


def _task(title: str, instructions: str, criterion: str) -> dict[str, Any]:
    return {
        "title": title,
        "instructions": instructions,
        "submission_types": ["photo", "short_text"],
        "rubric": [
            {
                "criterion": criterion,
                "levels": {
                    1: "Needs step-by-step support and has not yet shown the task safely.",
                    2: "Completes the task with some prompts and explains the main checks.",
                    3: "Completes the task safely and explains the observable result clearly.",
                },
            }
        ],
    }


_TEMPLATES: dict[str, dict[str, Any]] = {
    "mobile_repair": {
        "title": "Mobile Repair Practice",
        "objectives": [
            "Identify common phone parts and visible damage without guessing a fault.",
            "Practise a safe, documented screen-repair workflow on a demonstration device.",
            "Test basic functions and record what was observed before handing back a device.",
        ],
        "tasks": [
            _task(
                "Inspect and document a device",
                "On an unpowered demonstration phone, photograph the exterior, list visible damage, and label the parts you can identify. Do not open a customer device.",
                "Observation and documentation are complete and factual.",
            ),
            _task(
                "Practise a screen replacement workflow",
                "With teacher supervision and an unpowered demonstration device, arrange tools, follow the device-specific practice steps, and keep screws and parts labelled.",
                "The work area, parts, and handling sequence are organised safely.",
            ),
            _task(
                "Run a post-repair check",
                "With supervision, power only the demonstration device, check the agreed functions, and record pass, fail, or not tested for each one.",
                "Checks are performed in order and results are recorded without assumptions.",
            ),
        ],
        "equipment": ["Unpowered demonstration phone", "Screwdriver set", "Tray for parts", "Eye protection"],
        "safety": ["Disconnect power before opening a device.", "Use eye protection and keep small parts away from children.", "Stop and ask a teacher when a battery is swollen or damaged."],
        "estimated_duration_hours": 6,
        "evidence_needed": ["Annotated inspection photo", "Tool and parts layout photo", "Completed test checklist"],
    },
    "tailoring": {
        "title": "Tailoring Practice",
        "objectives": [
            "Take simple measurements and mark fabric using a clear measurement record.",
            "Practise straight seams, hems, and joining pieces with consistent allowance.",
            "Inspect finished stitching and identify one improvement without making a quality promise.",
        ],
        "tasks": [
            _task("Measure and mark fabric", "Measure a practice fabric piece, write the measurements, mark a seam allowance, and cut only after checking the marks.", "Measurements and markings are readable and consistent."),
            _task("Sew a practice sample", "With teacher guidance, sew a straight seam and a hem on scrap fabric. Keep fingers clear of the needle and pause before changing settings.", "The sample has an even seam and secure start and finish."),
            _task("Inspect and improve stitching", "Turn the sample inside out, inspect alignment and loose threads, and make one supervised correction.", "The learner identifies a real defect and makes a controlled correction."),
        ],
        "equipment": ["Scrap fabric", "Measuring tape", "Fabric chalk", "Scissors", "Sewing machine or hand needle"],
        "safety": ["Carry scissors closed and cut away from the body.", "Keep fingers clear of needles and switch off before adjustments.", "Use teacher supervision for unfamiliar machines."],
        "estimated_duration_hours": 5,
        "evidence_needed": ["Measurement record", "Stitching sample photo", "Inspection notes"],
    },
    "solar_maintenance": {
        "title": "Solar Maintenance Practice",
        "objectives": [
            "Identify visible solar-system components and record their condition without guessing.",
            "Practise a supervised, unpowered inspection and cleaning sequence.",
            "Use a checklist to report observations and escalate unsafe conditions.",
        ],
        "tasks": [
            _task("Map a demonstration system", "On an unpowered demonstration setup, label the panel, mounting, cable, controller, and battery positions. Do not touch live wiring.", "Components are labelled from direct observation."),
            _task("Practise a safe visual inspection", "With a teacher and the system isolated, inspect for dirt, cracks, loose mounts, and visible cable damage. Record only what is seen.", "The inspection follows the checklist and avoids electrical work."),
            _task("Prepare a maintenance report", "Write a short report with observations, photos, items needing teacher attention, and a clear statement of what was not tested.", "The report distinguishes observed, not tested, and escalated items."),
        ],
        "equipment": ["Unpowered demonstration solar kit", "Cleaning cloth", "Inspection checklist", "Non-contact visual aid"],
        "safety": ["Solar and electrical work must be supervised by a qualified teacher.", "Use only isolated, unpowered demonstration equipment.", "Do not climb, disconnect wiring, or work in rain or near exposed conductors."],
        "estimated_duration_hours": 4,
        "evidence_needed": ["Labelled system photo", "Completed inspection checklist", "Maintenance report"],
    },
    "food_service": {
        "title": "Food Service Practice",
        "objectives": [
            "Set up a clean, organised workstation using a simple checklist.",
            "Practise basic preparation and service steps while preventing cross-contamination.",
            "Record quantities, cleaning steps, and customer-facing observations.",
        ],
        "tasks": [
            _task("Set up a clean workstation", "Wash hands, clean the work surface, arrange tools, and complete the setup checklist before handling practice ingredients.", "The station is clean, organised, and checklist entries are complete."),
            _task("Prepare a simple practice item", "Follow a teacher-provided recipe or procedure, measure ingredients, separate raw and ready-to-eat items, and record what you did.", "Steps and quantities are followed and recorded."),
            _task("Practise safe service and close-down", "Serve the practice item using clean utensils, communicate clearly, then clean, store, and report any waste or issue.", "Service and close-down are hygienic and orderly."),
        ],
        "equipment": ["Hand-washing supplies", "Clean work surface", "Food-safe utensils", "Practice ingredients", "Labels"],
        "safety": ["Wash hands and prevent raw-to-ready cross-contamination.", "Use heat, knives, and allergens only with supervision.", "Do not serve food when storage or cleanliness is uncertain."],
        "estimated_duration_hours": 4,
        "evidence_needed": ["Setup checklist photo", "Preparation record", "Close-down checklist"],
    },
    "digital_services": {
        "title": "Digital Services Practice",
        "objectives": [
            "Organise files and basic information using a repeatable naming system.",
            "Practise a simple data-entry or document task with an accuracy check.",
            "Communicate completion, uncertainty, and privacy concerns clearly.",
        ],
        "tasks": [
            _task("Organise practice files", "Create folders and rename supplied practice files using the agreed naming convention. Do not use personal or confidential data.", "Files are organised and names are consistent."),
            _task("Complete a data-entry sample", "Enter supplied practice information into a template, compare it with the source, and mark any uncertain value as needing review.", "Entries match the supplied source and unknowns are not guessed."),
            _task("Send a completion note", "Write a short note describing completed work, items not completed, and any privacy or access concern.", "The note is concise, factual, and flags uncertainty."),
        ],
        "equipment": ["Computer or phone", "Practice files", "Template", "Access checklist"],
        "safety": ["Use simulated data only and never copy personal information into practice files.", "Do not share passwords or bypass access controls.", "Pause and ask a teacher when a file or request is unclear."],
        "estimated_duration_hours": 3,
        "evidence_needed": ["Folder listing screenshot", "Checked practice template", "Completion note"],
    },
}


def generate_module_draft(
    skill_family_id: str,
    language: str = "en",
    knowledge_records: list[dict] | None = None,
) -> dict[str, Any]:
    """Return a deterministic draft suitable for storing as ``content_json``."""
    template = deepcopy(_TEMPLATES.get(skill_family_id))
    flags: list[str] = []
    if template is None:
        template = {
            "title": "Practical Skills Practice",
            "objectives": [
                "Observe a teacher-demonstrated workflow and name its steps.",
                "Complete a supervised practice task using a checklist.",
                "Record evidence, uncertainty, and safety concerns for review.",
            ],
            "tasks": [
                _task("Observe and map the workflow", "Watch a teacher demonstration and write the observable steps without claiming independent competence.", "Steps are recorded from observation."),
                _task("Complete supervised practice", "Use only teacher-provided practice materials and stop whenever a step or hazard is unclear.", "The task is completed with safe supervision."),
                _task("Report the result", "Submit a checklist, evidence photo, and notes on what was not tested.", "The report distinguishes evidence from assumptions."),
            ],
            "equipment": ["Teacher-provided demonstration materials", "Checklist"],
            "safety": ["Use demonstration materials only and follow teacher instructions.", "Stop when equipment, instructions, or conditions are unclear.", "Do not handle hazards without direct supervision."],
            "estimated_duration_hours": 3,
            "evidence_needed": ["Practice checklist", "Evidence photo", "Teacher notes"],
        }
        flags.append("needs_teacher_authoring")

    references = []
    for record in knowledge_records or []:
        if not isinstance(record, dict):
            continue
        if not record.get("source_url") or not record.get("title"):
            continue
        references.append(
            {
                "title": record["title"],
                "source_url": record["source_url"],
                "last_checked_at": record.get("last_checked_at"),
            }
        )

    result = {
        **template,
        "source_references": references,
        "ai_generated": False,
        "human_reviewed": False,
        "language": language,
        "disclaimer": DISCLAIMER,
    }
    if language != "en":
        result["needs_translation"] = True
    if flags:
        result["flags"] = flags
    return result
