# TASKS.md

PHASE: 3
STATUS: done

(0=Bootstrap | 1=Specify | 2=Design | 3=Develop | 4=Validate | 5=Deploy)

Sprint: 2 (develop with TDD)

## UC-001

OWNER: A
PHASE: 2
STATUS: done

## UC-002

OWNER: A
PHASE: 3
STATUS: done

Phase 3 prompt slice: implemented in `src/app/domain/prompt.py`; unit and
integration tests pass (`17 passed`).

Phase 3 STEP 2: implemented round persistence, photo storage, clock ports,
round service, round API, and round-aware game state. Full test suite passes
(`97 passed, 1 skipped`).

UC-001 phase 3 STEP 1: added integration and unit tests for create/join/state,
domain rules, and `GameService`. RED run: `2` import errors during collection
because `app.domain.game` and `app.application.game_service` are not implemented.

## UC-003

OWNER: A
PHASE: 2
STATUS: done

## UC-004

OWNER: A
PHASE: 2
STATUS: done
