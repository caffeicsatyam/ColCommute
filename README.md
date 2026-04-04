<h1 align="center">ColCommute</h1>

<p align="center">
  A multi-agent system built with the Google Agent Development Kit (ADK) to coordinate collaborative commute planning.
</p>

---

## Overview

**ColCommute** uses an **orchestrator** agent (`root_agent` in `colcommute/agent.py`) that delegates to specialists. **Implemented today:**

- **Ride matching agent** — registers **commute posts** (offers or seat requests), finds compatible listings, and can record a **confirmed trip** after mutual agreement (see `agents/ride_matching.py` and `tools/ride_matching.py`).

**Planned / not wired yet:** routing, pricing, notification agents (stubs are commented in `colcommute/agent.py`).

## Project structure

```text
ColCommute/
├── agents/                 # ADK specialist agents (instructions + tool wiring)
│   └── ride_matching.py    # ride_matching_agent → tools from tools/
├── tools/                  # ADK function tools (thin wrappers → services/)
│   └── ride_matching.py    # register_commute_post, find_matches, list, confirm_trip
├── colcommute/             # ADK app entry: root_agent (orchestrator)
│   ├── agent.py
│   └── db/                 # SQLAlchemy models, session, Alembic metadata
├── services/               # Business logic + Postgres (e.g. ride_services.py)
├── alembic/                # Migrations
├── core/                   # Shared config (e.g. llm.py — model name, API key)
└── .env                    # Secrets (gitignored)
```

Local **ADK dev** data (chat session store, cache) lives under **`colcommute/.adk/`** (e.g. `session.db`) and is **gitignored** — it is not your Postgres app database.

## Getting started

### Prerequisites

- Python 3.10+
- `pip install -r requirements.txt` (includes `google-adk`, SQLAlchemy, Alembic, psycopg)

### Environment

Create `.env` at the repo root:

```bash
GOOGLE_API_KEY=YOUR_GEMINI_API_KEY
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE_NAME
```

Optional: `DB_CONNECT_TIMEOUT`, `DB_SSLMODE` (e.g. `require` for Cloud SQL). See `colcommute/db/session.py`.

### Run the app (ADK)

From the **repository root**:

```bash
adk web
```

Open the URL ADK prints (e.g. `http://127.0.0.1:8000`), select the **`colcommute`** app, and chat with **`root_agent`** (or the ride-matching sub-agent if exposed in the UI).

CLI run (alternative):

```bash
adk run colcommute
```

Use the **lowercase** package folder name `colcommute` that contains `agent.py` with `root_agent`.

### Database and migrations (PostgreSQL / Cloud SQL)

1. Install deps: `pip install -r requirements.txt`
2. Set `DATABASE_URL` in `.env`
3. From repo root:

   ```bash
   python -m alembic -c alembic.ini upgrade head
   python -m alembic -c alembic.ini current
   ```

4. New migration (review generated files before applying):

   ```bash
   python -m alembic -c alembic.ini revision --autogenerate -m "describe change"
   ```

`alembic/env.py` loads `.env`. For Cloud SQL from a laptop, use the [Auth Proxy](https://cloud.google.com/sql/docs/postgres/connect-auth-proxy) or authorized networks.

### Data model (short)

| Table | Purpose |
|-------|--------|
| **`users`** | Identity via `external_user_id` (optional `college_*` profile fields). |
| **`commute_posts`** | Open listings: destination place fields, `time_bucket`, `vacant_seats` / `seats_needed`, FK to `users`. |
| **`trips`** | Confirmed rides: links **offer** and **need** commute posts after agreement (`confirm_trip` tool / service). |

Matching uses **destination** (place id or normalized text), **time bucket**, and seat compatibility — not only profile fields on `users`.

### Production-oriented flow (later)

1. **Client UI**: Places Autocomplete → Place Details → structured `destination_place_id`, label, lat/lng.
2. **Your API** (e.g. `POST /commute-posts`): auth resolves `user_id`; persist **`commute_posts`**.
3. Optionally invoke ADK with structured args or session state.

`adk web` is a **chat** surface; a real app should use a proper map/places UI, not the dev chat alone.

### Manual testing

- Ensure **`users`** rows exist for each `external_user_id` you use in chat.
- Paste real **Place Details**–style fields so the agent can call **`register_commute_post`** with valid ids and coordinates.
- After two compatible posts exist, **`confirm_trip`** takes **offer** post UUID first, **need** post UUID second.

## Example prompts

You can ask for help posting a ride, finding matches, listing open posts, or confirming after both sides agree — the orchestrator should delegate ride tasks to the ride-matching specialist.

---

<p align="center">
  Built with Google ADK
</p>
