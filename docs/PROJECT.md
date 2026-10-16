# PROJECT.md — PicMe

## Purpose

- **Project name:** PicMe
- **User or organisational problem:** Party guests want a low-friction, shared
  photo-guessing game they can play together using only their phones and a
  projector.
- **Intended users:** Social groups at parties and informal gatherings; a host
  operates the projector and players use their phones.
- **In scope:** Create a game with a join code; players join by name; the host
  starts a round with a prompt; each player uploads one photo before the
  deadline; anonymous voting (one guess per player per photo, not on your own
  photo); reveal; scoreboard.
- **Out of scope:** Push notifications, slow mode, host approval of joins,
  reactions, written stories, custom categories, user accounts.

## Architecture

Dependencies point inward, following Clean Architecture:

`domain ← application ← interfaces ← infrastructure`

- `src/app/domain` — domain entities and rules (game, round, player, photo, vote,
  scoring).
- `src/app/application` — use cases and repository interfaces.
- `src/app/interfaces` — FastAPI HTTP routes and static HTML/JavaScript pages.
- `src/app/infrastructure` — configuration, persistence (SQLAlchemy 2), and web
  wiring.

The host projector view is served at `/host` and the phone view at `/play`. Both
refresh by polling the server every 2 seconds.

**Framework:** FastAPI (Python 3.12).  
**ORM:** SQLAlchemy 2.  
**Database:** SQLite for development and CI, PostgreSQL (Neon) in production.  
**Runtime:** Docker image deployed to Render.

## Structure

- `docs/specs/` — executable use-case specifications.
- `src/app/domain` — domain entities and rules.
- `src/app/application` — use cases and repository interfaces.
- `src/app/interfaces` — FastAPI routes and static pages.
- `src/app/infrastructure` — configuration, persistence, and web wiring.
- `tests/unit/` — domain and application tests.
- `tests/integration/` — API and persistence integration tests.
- `tests/e2e/` — container-based end-to-end tests.
- `.github/workflows/` — CI, release and manual deployment workflows.

## Commands

| Activity | Command |
|---|---|
| Install | `pip install -r requirements.txt` |
| Unit tests | `export PYTHONPATH=$PWD/src && pytest -q tests/unit` |
| Integration tests | `export PYTHONPATH=$PWD/src && pytest -q tests/integration` |
| Run locally | `export PYTHONPATH=$PWD/src && python -m uvicorn app.main:app --reload` |
| Build/release | Docker build (defined by teammate during setup) |

## Dependencies

Declared in `requirements.txt`. Key expected dependencies:

- FastAPI
- uvicorn[standard]
- SQLAlchemy 2
- psycopg2-binary (for PostgreSQL production)
- pytest, httpx (testing)

Runtime configuration is supplied through environment variables; never commit
`.env` files or credentials. Documented configuration variables:

- `DATABASE_URL` — SQLAlchemy database URL; defaults to SQLite for development.
