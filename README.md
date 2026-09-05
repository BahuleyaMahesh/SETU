# SETU — Smart Voice-Based Healthcare Monitoring for Rural India

Post-discharge patient monitoring that works over an ordinary phone call — no smartphone, no app, no internet connection required on the patient's end.

Built for **Smart Horizon 2026: 48-Hour International Hackathon** (New Horizon College of Engineering, Bengaluru — Problem Statement `SH-HLT-01`) by **Team Hack4Health**.

## The problem

Patients discharged from hospitals in rural India often lose all follow-up contact with their care team. Most remote-monitoring products assume a smartphone and a stable internet connection — exactly what a lot of rural patients, and the ASHA (community health) workers who serve them, don't reliably have. The result: complications go unnoticed until they become emergencies, and ASHA workers have no structured way to triage which of their many patients actually needs attention *today*.

## How SETU solves it

SETU calls the patient. A short phone call — answerable on any basic feature phone — walks them through a daily check-in using voice or keypad (DTMF) input. What they say gets turned into structured clinical data, a deterministic rule engine decides how urgent it is, and if it's serious, their ASHA worker and hospital are alerted immediately with the full context.

**Core principle: AI extracts. Rules decide. Humans act.**

The AI (Gemini) only ever converts messy human speech/text into structured symptoms, and phrases replies in plain language. It **never** decides how risky a patient's condition is — a transparent, auditable, keyword-based rule engine does that, every time, the same way. This isn't a compliance afterthought; it's enforced in the code path itself (see `backend/app/modules/risk/` and `backend/app/modules/clinical/service.py`).

## The care loop

```
Patient speaks/presses keys on a phone call, or checks in via the web app
                    │
                    ▼
   Sarvam AI transcribes speech (auto-detects the Indian language spoken)
                    │
                    ▼
     Gemini extracts structured symptoms — it does NOT judge severity
                    │
                    ▼
  Deterministic rule engine classifies risk: Normal / Warning / Critical
                    │
                    ▼
   Critical/Warning → real-time Alert created → ASHA worker + hospital notified
                    │
                    ▼
        Gemini phrases safe, tailored guidance back to the patient
     (spoken on the call, or shown in the app) — again, never re-deciding risk
```

Every input channel — the app's check-in form, the patient's own chat, an ASHA/hospital staff member reporting on a patient's behalf, and a real phone call — feeds the exact same clinical pipeline and produces the exact same kind of risk record. There is no separate "less real" code path for any of them.

## Who uses it

Three roles, kept strictly separate **at the backend query level**, not just hidden in the UI:

- **Patient** — a simple mobile-friendly web app: daily check-ins, medication reminders (auto-scheduled from an uploaded prescription photo, editable to whatever time suits them), an AI care-assistant chat, a "call me at this time every day" scheduler, and their own profile/risk history.
- **ASHA worker** — sees only their own assigned caseload: a patient roster with map view, an alerts queue, per-patient detail (call, message, registered location with directions, a full symptom/risk timeline, check-in call history with real transcripts), and an AI assistant that can answer questions about their *entire* caseload ("which of my patients are critical right now and why?") in addition to per-patient symptom reporting.
- **Hospital / Admin** — sees every patient in their hospital: dashboards, analytics, reports, the same alert/roster/chat tooling as ASHA workers but hospital-wide, plus patient registration and ASHA assignment.

## What's actually built and working right now

Not a mockup — every item below has been exercised against the real backend, a real PostgreSQL database, and (where noted) a real phone call:

- Full patient / ASHA / hospital web apps, dark mode, JWT auth with role-based access control enforced on every backend query.
- Deterministic clinical risk pipeline with real-time alert generation, acknowledgement, resolution, and escalation workflows.
- **Real outbound phone check-in calls** via Telnyx's Call Control API: a keypad menu (fine / report symptoms / emergency), a recorded spoken response transcribed by Sarvam AI, fed into the same deterministic risk engine as every other channel, with Gemini-generated spoken safety guidance read back to the patient — verified end-to-end against a live phone call, including a critical-risk escalation triggered entirely by what the patient said out loud.
- Prescription photo upload → Gemini vision reads the medications, dosage, and frequency (handles handwritten prescriptions, skips illegible entries instead of failing the whole upload) → medication reminders auto-scheduled at the right times of day, editable per reminder.
- A "schedule a daily check-in call at a time that suits me" scheduler, usable by the patient themselves or by their ASHA/hospital on their behalf.
- Email-based reminder and notification delivery (SMS providers for Twilio/Telnyx/MSG91 are fully built and pluggable behind one config switch, currently pending India's DLT sender-ID registration — a regulatory process, not a code gap).
- An AI chat assistant for ASHA/hospital staff that can answer free-text questions across their *whole* authorized patient roster ("who's in Whitefield?", "when did Ramesh last check in?"), in addition to structured per-patient symptom reporting.
- Interactive maps (nearest-hospital distance, patient location) using free OpenFreeMap tiles and Nominatim geocoding — no paid mapping API.

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | React + Vite + TypeScript + Tailwind CSS |
| Backend | FastAPI + SQLAlchemy (async) + PostgreSQL — modular monolith, not microservices |
| AI (extraction & chat) | Google Gemini — extracts structured data and phrases replies; never decides clinical risk |
| Speech-to-text | Sarvam AI (auto-detects the spoken Indian language) |
| Telephony | Telnyx (Call Control API) — pluggable provider abstraction also supports Twilio or a safe mock, selected by one environment variable |
| Notifications | Pluggable: Email (SMTP), Twilio, Telnyx, or MSG91, behind the same provider-abstraction pattern |
| Maps | MapLibre GL + OpenFreeMap tiles + Nominatim geocoding (all free, no API key required) |

Every external integration above has a **safe simulated fallback** when its API key isn't configured — the whole app is explorable with zero setup beyond a database and installed dependencies, and no code path ever silently pretends a real call/message succeeded when it didn't.

## Repository layout

```
backend/
  app/
    core/            # config, DB session, JWT auth, RBAC helper, provider-neutral utils
    db/models/       # SQLAlchemy models
    modules/         # one folder per domain: router.py + service.py + schemas.py (+ providers/)
      risk/          # the deterministic rule engine — the one place risk level is ever decided
      clinical/      # unifies patient + ASHA reported symptoms into one profile, feeds risk/
      calls/         # telephony providers + the Telnyx Call Control webhook state machine
      chat/          # patient chat, staff per-patient chat, staff whole-roster chat
      prescriptions/ # Gemini vision extraction from an uploaded prescription photo
      reminders/     # scheduling, frequency-text parsing, IST-aware timing
      ...
  scripts/           # seed_data.py (demo accounts + patients), create_admin.py
frontend/
  src/
    features/<role>/ # patient/, asha/, hospital/, auth/ — pages per role
    shared/components/ # cross-role UI shared via composition (contact panel, medication
                        # reminders panel, risk timeline, call history, maps, etc.)
docs/                # architecture/API/security notes (in progress)
```

## Getting started

### Prerequisites
- Python 3.11
- Node.js 18+
- PostgreSQL 14+

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows — use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
cp .env.example .env          # then fill in at least DATABASE_URL and SECRET_KEY
python scripts/seed_data.py   # optional — creates demo accounts + sample patients
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`. The dev server proxies `/api` to the backend automatically — no extra configuration needed.

### Demo accounts

After seeding: `patient@setu.com`, `asha@setu.com`, `hospital@setu.com` — any password works for these demo accounts (an intentional, explicitly-flagged shortcut for fast hackathon demoing, not a production auth model). New accounts can also self-register from the login screen for any of the three roles.

## Configuration

Nothing is required to explore the app in demo mode — every AI/speech/telephony/notification/maps integration falls back to safe simulated behavior when its key is missing. See `backend/.env.example` and `frontend/.env.example` for the full list. To turn on real behavior:

- `GEMINI_API_KEY` — real AI symptom extraction, chat replies, and prescription-photo reading
- `SARVAM_API_KEY` — real speech-to-text on phone check-in calls
- `TELNYX_API_KEY` / `TELNYX_PHONE` / `TELNYX_CONNECTION_ID` + `PUBLIC_BASE_URL` — real outbound phone calls
- `SMTP_USER` / `SMTP_PASSWORD` — real reminder/notification emails

## Design principles

- **AI extracts, rules decide, humans act.** The LLM never sets a patient's risk level — a deterministic engine does, from structured symptoms the AI (or a keypad press) produced. This is enforced in the code, not just policy.
- **Provider abstraction everywhere.** Telephony, notifications, speech-to-text, extraction, and maps are each a swappable provider behind a factory, chosen by one environment variable. Switching Telnyx → Twilio, or wiring up a new SMS vendor, never touches the clinical workflow.
- **Fail loud, not quiet.** A transcription failure, a rejected phone number, or an unreachable notification provider always surfaces as a real alert or a clear error to a human — never as a silent, misleadingly reassuring "everything's fine."
- **RBAC at the query level.** A patient only ever gets their own record; an ASHA only their assigned patients; a hospital only its own patients — checked on every backend request, not merely hidden by the frontend.

## Roadmap

- Production SMS, once India's DLT sender-ID registration (a multi-day regulatory process, not a code task) is complete.
- Multilingual spoken *replies* — Sarvam already auto-detects the patient's spoken language for transcription; the AI's guidance back to the patient is currently generated in English only.
- A curated medical knowledge base for RAG-grounded guidance — the retrieval pipeline (chunking, embeddings, semantic search) is already built and wired into staff chat, just not yet populated with real curated content.
- Deeper analytics and trend detection for hospitals (a baseline risk-distribution dashboard already exists).
- Native mobile packaging and offline-first support for ASHA field workers in low-connectivity areas.

## Team — Hack4Health

- Suhani Madan — Team Lead
- Bahuleya Mahesh
- Ghanashyam D Raj
- Shivani Srinivasan

R V College of Engineering · Smart Horizon 2026, New Horizon College of Engineering, Bengaluru

## License

Submitted for Smart Horizon 2026 under the hackathon's own rules. No open-source license has been chosen yet for this repository — add one (see [`LICENSE`](LICENSE)) before treating it as reusable outside the competition.
