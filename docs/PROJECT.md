# PROJECT.md - PicMe

## Purpose

- **Project name:** PicMe
- **Problem:** Party guests need a low-friction, shared photo-guessing game
  playable from phones with a host-operated projector.
- **Users:** A host and players at a party or informal gathering.
- **Scope:** Create and join a game, play prompt rounds, upload photos, vote,
  reveal uploaders, score correct guesses, show a scoreboard, and play again.
- **Out of scope:** Accounts, push notifications, slow mode, host approval of
  joins, reactions, written stories, and custom categories.

## Architecture

Dependencies point inward following Clean Architecture:

`domain <- application <- interfaces <- infrastructure`

- `src/app/domain` contains entities, value rules, and domain errors.
- `src/app/application` contains services and ports.
- `src/app/interfaces/api` contains HTTP adapters.
- `src/app/infrastructure` contains persistence, storage, clock, and web
  adapters.

The host projector and player clients poll the state endpoint. Business rules
remain in domain and application layers rather than database functions.

**Framework:** FastAPI on Python 3.12.
**ORM:** SQLAlchemy 2.  
**Database:** SQLite for development and CI; PostgreSQL in production.
**Runtime:** Docker deployed on Render.

## Domain model

The `Game` is the aggregate root. Its phases are `lobby`, `uploading`,
`voting`, `reveal`, and `scoreboard`.

- **Game:** `id`, unique six-character `code`, secret `host_token`, `phase`,
  current round/photo position, and lifecycle state. It owns players and
  rounds, permits joins only in `lobby`, authenticates host actions, and allows
  only valid phase transitions. State reads also apply deadline transitions.
- **Player:** `id`, `game_id`, display `name`, normalized name, and `score`.
  It belongs to one game, has a trimmed name of 1-20 characters, and names are
  unique within a game ignoring case and spaces. Players survive refresh and
  play-again reset.
- **Prompt:** `id`, game/round association, source/category, and text. A prompt
  is selected or entered for a round, must be non-empty, and cannot be reused
  within the same game, including typed prompts.
- **Round:** `id`, `game_id`, number, prompt, `upload_deadline`, upload duration,
  photo order, and current photo position. It accepts only 20, 40, or 60 seconds
  (default 40), closes at the deadline, when all players have uploaded, or by
  host action, and enters voting when photos exist or returns to lobby when none
  exist.
- **Photo:** `id`, `round_id`, `player_id`, compressed JPEG bytes, byte size, and
  fixed display order. Each player has at most one current photo per round and
  may replace it only during uploading. JPEGs are limited to 2 MB, remain
  anonymous while voting, and reveal their uploader afterward.
- **Vote:** `id`, `photo_id`, voter `player_id`, guessed `player_id`, and
  timestamp. A voter can keep only their latest guess for a photo, cannot vote
  on their own photo, and may guess only a player in the same game. Voting ends
  by host action or when all eligible voters have voted.

Application services:

- **GameService (UC-001):** create games, join players, validate host access,
  and read public state.
- **RoundService (UC-002):** select unused prompts, start and close rounds,
  enforce deadlines and upload rules, and store or replace photos.
- **VotingService (UC-003):** record latest guesses, report private progress,
  close voting, reveal uploaders, and advance photos.
- **ScoreService (UC-004):** award points, apply competition ranking, end a
  game, expose the scoreboard, and reset a game for play again.

Application ports:

- **GameRepository:** persist and retrieve games and players, including game
  lifecycle state.
- **RoundRepository:** persist rounds, prompts, photos' round relationships,
  deadlines, and display position.
- **VoteRepository:** persist latest guesses and query eligible vote progress.
- **PhotoStorage:** store and retrieve compressed JPEG bytes by photo id.
- **Clock:** provide server time for deadlines without coupling services to the
  system clock.

## API contract

Host actions send the `X-Host-Token` header. Player actions send `player_id` in
the request body or multipart form. JSON request fields are shown below unless
the endpoint is explicitly multipart.

| Method and path | Purpose | UC | Request fields | Success |
|---|---|---|---|---|
| `POST /games` | Create a game in lobby | UC-001 | none | `201` with `code`, `host_token`, and phase |
| `POST /games/{code}/players` | Join a game | UC-001 | `name` | `201` with `player_id` and player name |
| `GET /games/{code}/state` | Read public state and apply deadline transitions | UC-001/002/003/004 | none | `200` with phase and permitted current state |
| `GET /prompts/categories` | List selectable prompt categories | UC-002 | none | `200` with categories |
| `POST /games/{code}/rounds` | Start a prompt round | UC-002 | `category` or `Shuffle` or `prompt`; optional `duration` | `201` with round, prompt, deadline, and uploading phase |
| `POST /games/{code}/rounds/current/photos` | Upload or replace the player's JPEG | UC-002 | multipart `player_id`, `photo` | `201` with photo metadata |
| `POST /games/{code}/rounds/current/extend` | Add 10 seconds to upload deadline | UC-002 | none | `200` with new deadline |
| `POST /games/{code}/rounds/current/close` | Close uploads early | UC-002 | none | `200` with next phase |
| `GET /photos/{photo_id}/image` | Retrieve a stored photo image | UC-002/003 | none | `200` JPEG bytes |
| `POST /games/{code}/votes` | Submit or replace a guess for current photo | UC-003 | `player_id`, `guessed_player_id` | `201` with vote accepted |
| `GET /games/{code}/votes/progress` | Read aggregate voting progress | UC-003 | none | `200` with voted and eligible counts |
| `POST /games/{code}/voting/close` | Close voting and reveal current uploader | UC-003 | none | `200` with reveal state |
| `POST /games/{code}/photos/next` | Advance to the next photo during reveal | UC-003/004 | none | `200` with next phase/photo |
| `POST /games/{code}/lobby` | Return to lobby after a round | UC-004 | none | `200` with lobby phase |
| `POST /games/{code}/end` | End the game and calculate scoreboard | UC-004 | none | `200` with scoreboard phase |
| `GET /games/{code}/scoreboard?player_id=` | Read final ranked scoreboard | UC-004 | query `player_id` | `200` with full ranking and requesting player's rank/points |
| `POST /games/{code}/play-again` | Reset rounds and scores while retaining players | UC-004 | none | `200` with lobby phase |

## Module layout

```text
src/app/
  domain/
    errors.py
    game.py
    prompt.py
    round.py
    vote.py
    scoring.py
  application/
    ports/
      game_repository.py
      round_repository.py
      vote_repository.py
      photo_storage.py
      clock.py
    game_service.py
    round_service.py
    voting_service.py
    score_service.py
  interfaces/
    api/
      games.py
      rounds.py
      votes.py
      scoreboard.py
  infrastructure/
    persistence/
      game_models.py
      round_models.py
      vote_models.py
      sqlalchemy_game_repository.py
      sqlalchemy_round_repository.py
      sqlalchemy_vote_repository.py
    web/
      errors.py
    system_clock.py
```

## Errors

Exceptions are defined in `src/app/domain/errors.py` and mapped by the web
adapter to a JSON body of the form `{"detail": "<message>"}`:

| Exception | HTTP status |
|---|---:|
| `NotFound` | `404` |
| `Conflict` | `409` |
| `InvalidInput` | `422` |
| `Forbidden` | `403` |
| `PayloadTooLarge` | `413` |

## Dependencies

`requirements.txt` is the dependency source of truth:

- `fastapi`
- `uvicorn[standard]`
- `SQLAlchemy>=2.0`
- `psycopg[binary]`
- `python-dotenv`
- `python-multipart`
- `pytest`
- `httpx`

Runtime configuration comes from environment variables. `DATABASE_URL` selects
the SQLAlchemy database URL and defaults to SQLite for development. Credentials
and `.env` files are never committed.

## Commands

| Activity | Command |
|---|---|
| Install | `pip install -r requirements.txt` |
| Unit tests | `export PYTHONPATH=$PWD/src && pytest -q tests/unit` |
| Integration tests | `export PYTHONPATH=$PWD/src && pytest -q tests/integration` |
| Run locally | `export PYTHONPATH=$PWD/src && python -m uvicorn app.main:app --reload` |
| Build/release | `docker build -t picme .` |
