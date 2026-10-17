# Command Ready Training Academy — Independent Training Platform (v2.0 pilot)

**Brand:** Command Ready Training Academy  
**Tagline:** Knowledge. Judgment. Readiness.

This standalone FastAPI pilot preserves the seven-module Texas Arrest, Search & Seizure refresher, Chapter 14 visual reference content, scenarios, and 40-question examination from the previous course. It removes Andrews Police Department branding and names. The platform is **not affiliated with or endorsed by Andrews Police Department**.

## What works now
- Learner and administrator account sign-in with Argon2 password hashing
- Server-side module progress, randomized exam order and scoring
- Administrator learner provisioning, training overview, account disabling, CSV export
- Mobile-friendly independent branding and the existing training curriculum

## Important limits
- **Not yet multi-tenant.** All pilot learners are visible to the single platform administrator. Do not invite unrelated agencies until organization-level database isolation and authorization checks have been implemented and tested.
- Not yet production-hardened. No hosted URL, email invitations, payments, MFA, rate limiting, reliable backups, or certificate validation.
- No TCOLE provider approval or course-credit reporting is implied. Certificates, if later added, must clearly distinguish course completion from official TCOLE credit.
- Curriculum and legal references still require independent review for current Texas law, corrections and statutory effective dates.
- Do not upload protected investigative, CJIS, TCIC, NCIC, or real-case data.

## Local installation
1. Install Python 3.11+ and run `pip install -r requirements.txt` in a virtual environment.
2. Bootstrap the administrator with `python server.py bootstrap-admin`.
3. Run `COMMAND_READY_DEV_HTTP=1 uvicorn server:app --host 127.0.0.1 --port 8000` (PowerShell: `$env:COMMAND_READY_DEV_HTTP="1"; uvicorn server:app --host 127.0.0.1 --port 8000`).
4. Open `http://127.0.0.1:8000`. This is a local-only test. Never set `COMMAND_READY_DEV_HTTP=1` on a public server.

## Production roadmap
1. Independent Texas legal review of lessons, Chapter 14 reference and all answer keys.
2. Multi-agency organization model: agency membership, agency-admin roles, per-agency enrollment, and database-level authorization tests for every route.
3. Hosted PostgreSQL, backups, migrations, encrypted data transport, secret management, rate limits, MFA and account recovery.
4. Course authoring/versioning, assignments, completion certificates, validated reports and audit exports.
5. Accessibility, privacy/terms, retention and deletion, security testing, pilot agency onboarding, and TCOLE approval/reporting where applicable.

## Project layout
- `server.py`: FastAPI routes and database models
- `static/index.html`: learner/admin interface
- `data/course.json`: existing seven-module course, scenarios and exam
- `requirements.txt`: Python dependencies

Do not use the local SQLite pilot database as a production database.
