from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import db as db_module
from app.main import app
from app.models import Pod, Student, User
from seed import seed_demo


@pytest.fixture()
def api(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    monkeypatch.setattr(db_module, "engine", engine)
    monkeypatch.setattr(db_module, "SessionLocal", sessions)
    monkeypatch.setattr(seed_demo, "SessionLocal", sessions)
    seed_demo.seed()
    with TestClient(app) as client:
        users = sessions().query(User).all()
        yield client, {user.name: user.id for user in users}, sessions
    engine.dispose()


def headers(user_id: str) -> dict[str, str]:
    return {"X-Demo-User-Id": user_id}


def make_ticket(client: TestClient, employer_id: str, **overrides):
    payload = {
        "employer_name": "Offline Shop",
        "employer_contact": "demo",
        "source_type": "text",
        "transcript_original": "We need two mobile repair workers, pay 10000 per month.",
        "transcript_language": "en",
        **overrides,
    }
    return client.post("/api/v1/demand-tickets", headers=headers(employer_id), json=payload)


def test_ticket_flow_and_extraction_does_not_confirm(api):
    client, users, _ = api
    created = make_ticket(client, users["Shop A"])
    assert created.status_code == 200
    ticket_id = created.json()["id"]
    extracted = client.post(
        f"/api/v1/demand-tickets/{ticket_id}/extract",
        headers=headers(users["Shop A"]),
    )
    assert extracted.status_code == 200
    assert extracted.json()["status"] != "confirmed"
    confirmed = client.post(
        f"/api/v1/demand-tickets/{ticket_id}/confirm",
        headers=headers(users["Shop A"]),
        json={
            "confirmed_skill_id": "mobile_repair",
            "slots_confirmed": 2,
            "block_code": "test-block",
            "demand_type": "employment",
            "pay_min_minor": 10000,
            "pay_max_minor": 10000,
            "pay_period": "month",
        },
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"


def test_confirm_requires_block_code(api):
    client, users, _ = api
    ticket_id = make_ticket(client, users["Shop A"]).json()["id"]
    response = client.post(
        f"/api/v1/demand-tickets/{ticket_id}/confirm",
        headers=headers(users["Shop A"]),
        json={
            "confirmed_skill_id": "mobile_repair",
            "slots_confirmed": 2,
            "block_code": "",
            "demand_type": "employment",
        },
    )
    assert response.status_code == 422


def test_pod_threshold_ignores_training_slots(api):
    client, users, _ = api
    response = client.post(
        "/api/v1/pods/evaluate",
        headers=headers(users["Teacher Meena"]),
        json={"block_code": "demo-block-01", "skill_family_id": "mobile_repair", "pod_mode": "work_trial"},
    )
    assert response.status_code == 200
    assert response.json()["result"] == "pod_proposed"
    assert response.json()["confirmed_slots"] == 6
    training = client.post(
        "/api/v1/pods/evaluate",
        headers=headers(users["Teacher Meena"]),
        json={"block_code": "demo-block-01", "skill_family_id": "tailoring", "pod_mode": "work_trial"},
    )
    assert training.json()["result"] == "below_threshold"


def test_kavya_safeguarding_and_minor_outcomes(api):
    client, users, sessions = api
    evaluation = client.post(
        "/api/v1/pods/evaluate",
        headers=headers(users["Teacher Meena"]),
        json={"block_code": "demo-block-01", "skill_family_id": "mobile_repair", "pod_mode": "work_trial"},
    ).json()
    work_pod_id = evaluation["pod_id"]
    kavya = sessions().query(Student).filter_by(user_id=users["Kavya"]).first()
    blocked_enrolment = client.post(
        f"/api/v1/pods/{work_pod_id}/enrolments",
        headers=headers(users["Kavya"]),
        json={"student_id": kavya.id},
    )
    assert blocked_enrolment.status_code == 403
    supervised = sessions().query(Pod).filter_by(pod_mode="supervised_practice").first()
    allowed_enrolment = client.post(
        f"/api/v1/pods/{supervised.id}/enrolments",
        headers=headers(users["Kavya"]),
        json={"student_id": kavya.id},
    )
    assert allowed_enrolment.status_code == 200
    for stage in ("started_work",):
        blocked = client.post(
            "/api/v1/outcomes",
            headers=headers(users["Kavya"]),
            json={"student_id": kavya.id, "pod_id": supervised.id, "stage": stage, "verification_level": "self_reported"},
        )
        assert blocked.status_code == 403
    for stage in ("interest_recorded", "task_completed"):
        allowed = client.post(
            "/api/v1/outcomes",
            headers=headers(users["Kavya"]),
            json={"student_id": kavya.id, "pod_id": supervised.id, "stage": stage, "verification_level": "self_reported"},
        )
        assert allowed.status_code == 200


def test_first_payment_and_dashboard_keep_self_reported_separate(api):
    client, users, sessions = api
    ravi = sessions().query(Student).filter_by(user_id=users["Ravi"]).first()
    pod = sessions().query(Pod).filter_by(pod_mode="supervised_practice").first()
    response = client.post(
        "/api/v1/outcomes",
        headers=headers(users["Ravi"]),
        json={"student_id": ravi.id, "pod_id": pod.id, "stage": "first_payment_verified", "verification_level": "self_reported"},
    )
    assert response.status_code == 422
    for level in ("self_reported", "verified"):
        assert client.post(
            "/api/v1/outcomes",
            headers=headers(users["Ravi"]),
            json={"student_id": ravi.id, "pod_id": pod.id, "stage": "interest_recorded", "verification_level": level},
        ).status_code == 200
    dashboard = client.get("/api/v1/dashboard/impact", headers=headers(users["Ravi"])).json()
    assert dashboard["outcomes"]["interest_recorded"]["self_reported"] == 1
    assert dashboard["outcomes"]["interest_recorded"]["verified"] == 1


def test_sync_duplicate_stale_and_minor_rejection(api):
    client, users, sessions = api
    operation = {
        "client_op_id": "ticket-create-1",
        "entity_type": "demand_ticket",
        "action": "create",
        "entity_id": "client-ticket-1",
        "payload": {
            "employer_name": "Offline Employer",
            "source_type": "text",
            "transcript_original": "Need mobile repair",
        },
    }
    first = client.post("/api/v1/sync/push", headers=headers(users["Shop A"]), json={"ops": [operation]})
    assert first.json()["results"][0]["status"] == "applied"
    duplicate = client.post("/api/v1/sync/push", headers=headers(users["Shop A"]), json={"ops": [operation]})
    assert duplicate.json()["results"][0]["status"] == "duplicate"
    stale = client.post(
        "/api/v1/sync/push",
        headers=headers(users["Shop A"]),
        json={
            "ops": [{
                "client_op_id": "ticket-update-stale",
                "entity_type": "demand_ticket",
                "action": "update_draft",
                "entity_id": "client-ticket-1",
                "base_version": 99,
                "payload": {"transcript_original": "changed"},
            }],
        },
    )
    assert stale.json()["results"][0]["status"] == "conflict"
    kavya = sessions().query(Student).filter_by(user_id=users["Kavya"]).first()
    pod = sessions().query(Pod).filter_by(pod_mode="supervised_practice").first()
    rejected = client.post(
        "/api/v1/sync/push",
        headers=headers(users["Kavya"]),
        json={"ops": [{
            "client_op_id": "minor-outcome-1",
            "entity_type": "outcome",
            "action": "create",
            "entity_id": "client-outcome-1",
            "payload": {"student_id": kavya.id, "pod_id": pod.id, "stage": "started_work", "verification_level": "self_reported"},
        }]},
    )
    assert rejected.json()["results"][0]["status"] == "rejected"


def test_module_publish_requires_human_review(api):
    client, users, _ = api
    module = client.post(
        "/api/v1/modules",
        headers=headers(users["Teacher Meena"]),
        json={"title": "Practice", "skill_family_id": "mobile_repair", "language": "en"},
    )
    assert module.status_code == 200
    response = client.post(
        f"/api/v1/modules/{module.json()['id']}/publish",
        headers=headers(users["Teacher Meena"]),
        json={"human_reviewed": False},
    )
    assert response.status_code == 422


def test_live_auth_register_login_and_demo_header_rejection(api, monkeypatch):
    client, _, _ = api
    from app.config import settings

    monkeypatch.setattr(settings, "demo_mode", False)
    monkeypatch.setattr(settings, "secret_key", "test-secret")
    payload = {
        "name": "Live Student",
        "phone": "9999999999",
        "pin": "1234",
        "role": "student",
        "age_band": "18_plus",
        "language": "en",
    }
    registered = client.post("/api/v1/auth/register", json=payload)
    assert registered.status_code == 201
    assert registered.json()["user"]["student_id"]
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409
    login = client.post("/api/v1/auth/login", json={"phone": payload["phone"], "pin": payload["pin"]})
    assert login.status_code == 200
    token = login.json()["token"]
    assert client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    assert client.get("/api/v1/me", headers={"Authorization": "Bearer invalid"}).status_code == 401
    assert client.get("/api/v1/me", headers={"X-Demo-User-Id": registered.json()["user"]["id"]}).status_code == 401
