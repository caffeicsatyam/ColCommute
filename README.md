# <div align="center">ColCommute</div>

<p align="center">
  <img src="static/WhatsApp%20Image%202026-04-08%20at%2001.49.23.jpeg" alt="ColCommute banner" width="720">
</p>

<p align="center">
  AI-assisted campus commute matching for student carpooling.
</p>

<p align="center">
  <a href="#goal"><strong>Goal</strong></a> |
  <a href="#key-features"><strong>Key Features</strong></a> |
  <a href="#getting-started"><strong>Getting Started</strong></a> |
  <a href="#running-colcommute"><strong>Running ColCommute</strong></a> |
  <a href="#project-structure"><strong>Project Structure</strong></a>
</p>

## Goal

ColCommute is built to make student commuting easier by combining route-aware ride matching, chat-driven coordination, and a modern web interface. The project centers on shared college commutes, where riders and drivers often overlap only partially and need flexible pickup points instead of exact start-to-end matches.

The platform uses Google ADK agents, FastAPI, PostgreSQL, and Google Maps services to support ride discovery, matching, trip tracking, and feedback flows.

---

## Key Features

1. JWT-based authentication with signup, login, and current-user endpoints
2. Commute offer and ride request posting
3. Route-aware matching, including middle-of-route pickup scenarios
4. Google Maps geocoding and routing integration
5. Search fallback from ride offers to nearby ride requests
6. Trip lifecycle tracking: `confirmed -> in_progress -> completed -> paid`
7. Persisted trip payments and ride feedback
8. Fare splitting helpers
9. ADK-powered orchestration for ride coordination and chat flows
10. Separate frontend and backend apps for product iteration

---

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Alembic, PostgreSQL
- AI layer: Google ADK, Gemini model configuration
- Maps and routing: Google Maps APIs
- Frontend: Next.js 16, React 19, AI SDK

---

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL
- Node.js 20+ and `pnpm`
- Google AI / Gemini API access
- Google Maps API key

### Backend Installation

```bash
cd backend
pip install -r requirements.txt
```

### Frontend Installation

```bash
cd frontend
pnpm install
```

---

## Environment Setup

Create environment files before running the app.

### Backend `.env`

You can start from [`backend/.env.example`](backend/.env.example):

```bash
GOOGLE_API_KEY=YOUR_GEMINI_API_KEY
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE_NAME
JWT_SECRET_KEY=CHANGE_ME
GOOGLE_MAPS_API_KEY=YOUR_GOOGLE_MAPS_API_KEY
```

Also supported:

- `GOOGLE_MAP_API_KEY` as an alternative to `GOOGLE_MAPS_API_KEY`
- `DB_CONNECT_TIMEOUT`
- `DB_SSLMODE`
- `COLCOMMUTE_MODEL`
- `COLCOMMUTE_FALLBACK_MODEL`

Default model behavior:

- Primary model: `gemini-2.5-flash-lite`
- Fallback model: `gemini-2.5-flash`

### Frontend `.env`

The frontend has its own `.env` file under `frontend/`. Configure it for the backend base URL and any frontend-specific secrets your deployment needs.

---

## Database Setup

Run migrations from the backend directory:

```bash
cd backend
python -m alembic -c alembic.ini upgrade head
```

To inspect the current revision:

```bash
python -m alembic -c alembic.ini current
```

---

## Running ColCommute

### Run the Backend

```bash
cd backend
uvicorn api.main:app --reload
```

Useful endpoints:

- `GET /health`
- `POST /auth/signup`
- `POST /auth/login`
- `GET /auth/me`
- `POST /chat`

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

### Run the ADK App

```bash
cd backend
adk web
```

Or run the root agent directly:

```bash
cd backend
adk run colcommute
```

### Run the Frontend

```bash
cd frontend
pnpm dev
```

Frontend default URL:

```text
http://127.0.0.1:3000
```

---

## Auth Flow

1. Sign up or log in
2. Save the returned bearer token
3. Call `GET /auth/me`
4. Use the returned `external_user_id` when a ride action requires user identity

---

## Matching Behavior

ColCommute matching currently uses:

- Destination compatibility by place ID or nearby coordinates
- Route corridor matching so riders can join in the middle of a driver route
- Broader location-text fallback so searches like `Ghaziabad` can match more specific places
- Time bucket compatibility
- Offer/request seat compatibility

If no ride offers are found for a route search, the system can return nearby ride requests as a fallback.

---

## Data Model

- `users`: authentication and user identity records
- `commute_posts`: open ride offers and ride requests
- `trips`: confirmed rides with lifecycle state
- `trip_payments`: persisted payment records
- `trip_feedback`: persisted rider and driver feedback
- `chat_sessions` and `chat_messages`: chat persistence for conversational flows

---

## Project Structure

```text
ColCommute/
|-- backend/
|   |-- agents/              # ADK agents for orchestration, pricing, routing, and matching
|   |-- alembic/             # Database migrations
|   |-- api/                 # FastAPI app, routers, schemas, dependencies
|   |-- colcommute/          # Root ADK agent package and database setup
|   |-- core/                # Shared graph, memory, and LLM configuration
|   |-- services/            # Business logic for auth, fares, and rides
|   |-- tests/               # Backend test suite
|   `-- tools/               # ADK tool wrappers
|-- frontend/                # Next.js chat and product UI
`-- static/                  # README/media assets
```

---

## Tests

Backend tests currently cover:

- Auth endpoints
- Chat history
- Pricing
- Ride posting and matching
- Trip lifecycle

Run them with:

```bash
cd backend
pytest
```

Frontend quality checks are available through:

```bash
cd frontend
pnpm check
```

---

## Notes

- Route quality depends on reliable geocoding data
- Obvious out-of-region geocoding results are rejected for India-based searches
- Existing bad rows in a local database may still require manual cleanup

---

Built with Google ADK, FastAPI, SQLAlchemy, PostgreSQL, Next.js, and Google Maps.
