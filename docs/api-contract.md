# DemandLock API Contract

The API is served by FastAPI at `http://127.0.0.1:8000`. Demo requests use
the `X-Demo-User-Id` header.

## Seeded demo ids

Run `cd backend; python seed/seed_demo.py` to seed or refresh the demo data.
The current seeded user IDs are:

| User | ID |
|---|---|
| Teacher Meena | `ea32d2f8-2db0-4030-a14d-5af0bee45620` |
| Shop A | `e78c0157-3f59-4b5d-bc62-bba4de2bf1dd` |
| Shop B | `702b42de-103b-4ac5-bc1d-b4f6812dfb84` |
| Shop C | `4fe35dfd-545d-4a42-b046-64a76839d118` |
| Ravi | `04efe61d-9349-45b8-b544-fe598c6b6fd2` |
| Kavya | `ada748a0-864f-4775-93d9-7ac1512f27be` |

Student IDs printed by the seed script:

| Student | ID |
|---|---|
| Ravi | `3a3b8e6f-9758-4508-bf52-ff54d6de0d6e` |
| Kavya | `802a7b71-bb56-43ab-9e68-cf15e15d5fea` |

IDs are deterministic for an existing database and are printed again by every
seed run. If the database is recreated, use the newly printed values.

The frontend can discover the current IDs and roles with:

```bash
curl http://127.0.0.1:8000/api/v1/demo/users
```

## Demo flow

Start the service from `backend`:

```bash
uvicorn app.main:app
```

Create a demand ticket:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/demand-tickets \
  -H "Content-Type: application/json" \
  -H "X-Demo-User-Id: e78c0157-3f59-4b5d-bc62-bba4de2bf1dd" \
  -d '{"employer_name":"Demo Shop","employer_contact":"demo","source_type":"text","transcript_original":"We need two mobile repair workers, pay 10000 per month.","transcript_language":"en"}'
```

Extract proposed fields. Replace `<ticket-id>` with the returned ticket ID.
Extraction never confirms the ticket:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/demand-tickets/<ticket-id>/extract \
  -H "X-Demo-User-Id: e78c0157-3f59-4b5d-bc62-bba4de2bf1dd"
```

Confirm the ticket:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/demand-tickets/<ticket-id>/confirm \
  -H "Content-Type: application/json" \
  -H "X-Demo-User-Id: e78c0157-3f59-4b5d-bc62-bba4de2bf1dd" \
  -d '{"confirmed_skill_id":"mobile_repair","slots_confirmed":2,"block_code":"demo-block-01","demand_type":"employment","pay_min_minor":10000,"pay_max_minor":10000,"pay_period":"month"}'
```

Evaluate the seeded six employment slots. Training tickets are excluded from
employment pod counting:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/pods/evaluate \
  -H "Content-Type: application/json" \
  -H "X-Demo-User-Id: ea32d2f8-2db0-4030-a14d-5af0bee45620" \
  -d '{"block_code":"demo-block-01","skill_family_id":"mobile_repair","pod_mode":"work_trial"}'
```

The response is `pod_proposed` or `pod_updated` with `confirmed_slots: 6`.
The returned `pod_id` can be used for enrolment:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/pods/<pod-id>/enrolments \
  -H "Content-Type: application/json" \
  -H "X-Demo-User-Id: 04efe61d-9349-45b8-b544-fe598c6b6fd2" \
  -d '{"student_id":"04efe61d-9349-45b8-b544-fe598c6b6fd2"}'
```

Push an offline operation. Operations are applied independently and can be
retried safely with the same `client_op_id`:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/sync/push \
  -H "Content-Type: application/json" \
  -H "X-Demo-User-Id: e78c0157-3f59-4b5d-bc62-bba4de2bf1dd" \
  -d '{"ops":[{"client_op_id":"demo-ticket-1","entity_type":"demand_ticket","action":"create","entity_id":"client-ticket-1","payload":{"employer_name":"Offline Shop","source_type":"text","transcript_original":"Need mobile repair"}}]}'
```

The first request returns `status: "applied"`; repeating it returns the stored
result with `status: "duplicate"`. Draft updates include `base_version` and
return `status: "conflict"` when the local version is stale or the ticket has
already been confirmed.
