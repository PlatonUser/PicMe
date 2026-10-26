# TASKS.md

PHASE: 3
STATUS: in-progress

(0=Bootstrap | 1=Specify | 2=Design | 3=Develop | 4=Validate | 5=Deploy)

Sprint: 3 (finish use cases, deploy, UI)

## UC-001

OWNER: A
PHASE: 3
STATUS: done

## UC-002

OWNER: A
PHASE: 3
STATUS: done

Prompt catalog in `src/app/domain/prompt.py`; round persistence, photo upload,
clock port, round service, round API and round-aware game state implemented.
Unit and integration tests pass (97 passed).

## UC-003

OWNER: A
PHASE: 3
STATUS: done

Votes table, VotingService and votes API (vote, progress, close voting, next photo,
back to lobby); unit, integration and e2e tests pass.

## UC-004

OWNER: A
PHASE: 3
STATUS: done

Scoring and competition ranking, ScoreService and scoreboard API (end, scoreboard,
play again); unit, integration and e2e tests pass.

## Delivery (acceptance tests, deployment, UI)

OWNER: B
PHASE: 4
STATUS: in-progress

Acceptance tests for UC-001 to UC-004 in `tests/e2e/` merged; UC-001/002 pass
against the container, UC-003/004 marked xfail until implemented.