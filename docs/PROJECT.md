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

## Domain model

The domain is organized around the `Game` aggregate; `Round`, `Player`, `Photo`,
and `Vote` are game-owned records. `Prompt` is selected and recorded per game
so it cannot be reused in that game.

- **Game:** `id`, six-character `code`, secret `host_token`, `phase`, and
  accumulated player scores. It owns players and rounds, allows joins only in
  `lobby`, and controls the `lobby`, `uploading`, `voting`, `reveal`, and
  `scoreboard` transitions. A code identifies one game and state reads may
  trigger deadline-driven transitions.
- **Player:** `id`, `game_id`, display `name`, normalized name, and `score`.
  Names are trimmed, 1-20 characters, and unique within a game ignoring case
  and spaces. A player persists through refreshes and Play again.
- **Prompt:** `id`, game association, source/category, and prompt text. A
  selected or typed prompt is recorded as used and cannot repeat within a game;
  typed prompts must be non-empty.
- **Round:** `id`, `game_id`, number, prompt, `upload_deadline`, and current
  photo/order state. It accepts only 20, 40, or 60 second upload durations
  (default 40), closes on deadline, all-player completion, or host action, and
  moves to voting when it has photos or back to lobby when it does not.
- **Photo:** `id`, `round_id`, `player_id`, compressed JPEG bytes, size, and
  fixed display order. Each player has at most one current photo per round;
  replacement is allowed only during uploading, with JPEG bytes at most 2 MB.
  Photos are anonymous during voting and reveal their uploader afterward.
- **Vote:** `id`, `photo_id`, voter `player_id`, guessed `player_id`, and
  timestamp. Each eligible voter has only their latest guess per photo; the
  uploader cannot vote on their own photo, and the guessed player must be in
  the same game. Voting closes when the host ends it or all eligible voters
  have voted.

Application services and ports:

- `GameService` (UC-001) creates games, joins players, validates host access,
  and reads public game state.
- `RoundService` (UC-002) selects prompts, starts and closes rounds, enforces
  deadlines and upload rules, and stores/replaces photos.
- `VotingService` (UC-003) records latest guesses, reports private vote
  progress, closes voting, reveals uploaders, and advances photos.
- `ScoreService` (UC-004) awards points, applies competition ranking, ends a
  game, exposes the scoreboard, and resets a game for Play again.
- Repository ports: `GameRepository`, `PlayerRepository`, `PromptRepository`,
  `RoundRepository`, `PhotoRepository`, and `VoteRepository`, one interface
  per aggregate or persisted domain record. `PhotoStorage` stores and retrieves
  compressed JPEG bytes without coupling the domain to a storage technology.

HTTP endpoints required by the use cases:

- `POST /games` creates a game; `POST /games/{code}/players` joins it;
  `GET /games/{code}/state` reads state and applies deadline transitions.
- `POST /games/{code}/rounds` starts a round; `POST /games/{code}/rounds/{round_id}/photos`
  uploads or replaces a photo; `POST /games/{code}/rounds/{round_id}/extend`
  adds 10 seconds; `POST /games/{code}/rounds/{round_id}/close` ends uploads.
- `POST /games/{code}/photos/{photo_id}/votes` submits or replaces a guess;
  `GET /games/{code}/votes/progress` reads host-only progress;
  `POST /games/{code}/voting/close` closes voting; `POST /games/{code}/reveal/next`
  advances to the next photo; `POST /games/{code}/reveal/lobby` returns to lobby.
- `POST /games/{code}/end` ends the game; `GET /games/{code}/scoreboard` reads
  the final ranking; `POST /games/{code}/play-again` resets the game.

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
| Build/release | `docker build -t picme .` |

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
