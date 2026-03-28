# AETHERIUM-LM

AETHERIUM-LM is a platform for experimenting with asynchronous LLM integration and reasoning workflows.

## Core components

- **Backend services (`app/`)** for system configuration, database access, and LLM helpers.
- **Reasoning engine (`cogitator_x/`)** for thought-path generation and evaluation with MCTS + Process Reward Model.

## Key structure

- `app/config.py` — database URL, global LLM configs, API keys.
- `app/db.py` — SQLAlchemy async models and session factory.
- `app/services/llm_service.py` — LLM config validation, embeddings, and role-based model selection.
- `app/services/platform_work.py` — platform workstream planning and initiative/backlog persistence.
- `cogitator_x/` — reasoning runtime.
- `tests/` — unit tests for reasoning and service logic.

## Quick start

1. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```

2. Run tests

   ```bash
   pytest -q
   ```

## Platform update status

Implemented capabilities:

- Structured platform planning package generation (workstreams, options, risks, rollout/rollback, production DoD).
- Database persistence for `Initiative -> Epic -> Story -> Task` entities.

## Notes

- `GLOBAL_LLM_CONFIGS` in `app/config.py` are system defaults and use negative IDs to distinguish from DB records.
- Demo UI flow remains available in `main.py` (Flet).


## Mobile backend module

A production-oriented mobile backend reference implementation is included in `app/mobile_backend.py` with:

- JWT-based auth and device registration for iOS/Android push routing.
- Offline-friendly sync (`cursor`, `etag`, `version`) and optimistic conflict handling.
- Idempotent writes for duplicate/retry-safe commands.
- Baseline retry/timeout and user-level rate-limit enforcement.
- Push deduplication across APNs/FCM notification fanout.

See `docs/mobile_backend_api.md` for API contract and policies, and `scripts/simulate_duplicate_retry.py` for duplicate retry simulation.

## Documentation language sections

### English summary
- Architecture and module scope are documented in `docs/mobile_backend_api.md` and `docs/architecture_reports/`.
- Operational assumptions are aligned with tests in `tests/`.

### สรุปภาษาไทย
- สถาปัตยกรรมและขอบเขตโมดูลอธิบายใน `docs/mobile_backend_api.md` และ `docs/architecture_reports/`
- สมมติฐานการทำงานของระบบอ้างอิงตรงกับชุดทดสอบใน `tests/`

## Future roadmap (clear next steps)

| Area | Planned enhancement | Why it matters |
|---|---|---|
| Auth | Refresh token + token revocation list | ลดความเสี่ยงจาก access token ที่รั่วไหล |
| Sync | Tombstone retention policy + background compaction | ป้องกันข้อมูลโตเร็วจากรายการลบสะสม |
| Idempotency | TTL cleanup for key cache | ควบคุม memory growth ในงานเขียนจำนวนมาก |
| Push | Provider-level retry queue + DLQ | เพิ่มเสถียรภาพเมื่อ APNs/FCM ขัดข้องชั่วคราว |
| Observability | Structured metrics for rate-limit/conflict trends | ช่วยปรับ capacity และ policy ได้จากข้อมูลจริง |
