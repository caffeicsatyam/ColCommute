# Copilot Chat Instructions — ColCommute

Purpose: short guidance for AI assistants working on ColCommute (multi-agent commute orchestration built with Google ADK). Keep suggestions focused, safe, and linked to existing docs.

## Quick Links
- Project overview: [README.md](../README.md)
- Main agent entry: [colCommute/agent.py](../colCommute/agent.py)
- Orchestrator: [agents/orchestrator.py](../agents/orchestrator.py)
- Shared LLM config: [core/llm.py](../core/llm.py)
- Tools: [tools/](../tools/)

## Environment & Key Commands
- Python: 3.10+
- Install ADK: `pip install google-adk`
- Add your API key to `.env`: `GOOGLE_API_KEY=YOUR_GEMINI_API_KEY`
- Run the agent: `adk run colCommute`
- Launch web UI: `adk web`

## What AI assistants MAY do
- Implement and improve agent logic inside `agents/` following existing Agent/TypedDict patterns.
- Add or extend tools under `tools/` (wrap functions as ADK FunctionTools where applicable).
- Suggest and implement unit tests in a `tests/` folder (choose pytest or other—document chosen framework).
- Improve `core/llm.py` and memory handling for safer prompts and schemas.
- Propose docs or README additions; prefer linking to existing docs rather than duplicating content.

## NOT Allowed / Anti-Patterns
- Do not commit secrets or `.env` with API keys.
- Do not bypass ADK abstractions (avoid importing private ADK internals).
- Avoid large structural refactors without tests and maintainer approval.
- Don’t change deployment or infra settings in CI without an explicit PR and owner approval.
 - Do not add content to empty files. If functionality already exists in the codebase, prefer reusing or extending those files and APIs rather than creating new files or populating placeholders without maintainer approval.

## Apply-To Globs (recommended)
```
agents/**
colCommute/**
core/**
services/**
tools/**
```

## Code Patterns & Conventions
- Follow the ADK Agent pattern: typed input/output schemas (TypedDict/Annotated) and explicit `response_schema`.
- Use `tools/*.py` for side-effects (payments, logging) and wrap them for agent use.
- Centralize LLM model and key config in `core/llm.py`.

## Example Prompts (for maintainers / reviewers)
- "Implement route selection in `agents/routing.py` using distances and travel time; write unit tests for expected outputs." 
- "Add a `demand_prediction` stub under `agents/` and document its input-output contract in `core/memory.py`."
- "Create integration tests for the orchestrator flow that mock Gemini responses." 
- "Refactor `tools/payment_processing.py` to return deterministic typed results and add tests for edge cases."

## Notes & Next Steps
- This file is a minimal bootstrap. Please confirm:
  1) preferred testing framework (pytest recommended),
  2) exact dependency pinning (create `requirements.txt` or `pyproject.toml`), and
  3) team owners or CODEOWNERS for agent areas.

---
_Generated and scoped for quick agent onboarding. Keep it short and link-first._
