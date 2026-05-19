# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
make run       # Start FastAPI dev server (localhost:8000)
make test      # Run all pytest tests
make format    # black + ruff fix
make lint      # ruff check only
make seed      # Run seed script manually
```

To run a single test file: `PYTHONPATH=. pytest -q backend/tests/test_notes.py`

Pre-commit hooks (black, ruff, end-of-file-fixer, trailing-whitespace) are configured. Install with `pre-commit install`.

## Architecture

**Stack**: FastAPI backend with SQLite via SQLAlchemy ORM. Static vanilla-JS frontend served directly by FastAPI — no Node.js toolchain.

**Layers**:
- `backend/app/models.py` — SQLAlchemy ORM models. A `TimestampMixin` adds `created_at`/`updated_at` to every model. Currently two tables: `notes` and `action_items`.
- `backend/app/schemas.py` — Pydantic models for request/response serialization. Each resource has `<Resource>Create`, `<Resource>Read` (orm_mode enabled), and `<Resource>Patch` schemas.
- `backend/app/routers/` — FastAPI routers. Both routers support pagination (`skip`/`limit`), sorting (`sort=<field>`, prefix with `-` for descending), and PATCH endpoints for partial updates. Notes has a text search filter (`q`); action items has a `completed` boolean filter.
- `backend/app/db.py` — DB setup. Engine creates `data/app.db` (SQLite). `get_db()` is the FastAPI dependency; `get_session()` is a standalone context manager. On first startup, `apply_seed_if_needed()` runs `data/seed.sql` if the DB file doesn't exist.
- `backend/app/services/extract.py` — Pure function that parses action items from text (lines starting with `TODO:`/`ACTION:` or ending with `!`).

**Tests** (`backend/tests/`): pytest with FastAPI `TestClient`. `conftest.py` provides a `client` fixture that creates a temp SQLite DB per test run, overriding the `get_db` dependency.

**Frontend** (`frontend/`): Single HTML page with vanilla JS that calls the REST API. Static files mounted at `/static`; root `/` serves `index.html`. Swagger UI at `/docs`.

**Config**: Copy `.env.example` to `.env` to override defaults like `DATABASE_PATH`.
