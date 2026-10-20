# ADR-003: Live Updates by Polling

- **Status:** Proposed
- **Date:** 2026-10-18

## Context

The host projector and player phones need current game state during uploads,
voting, reveals, and the scoreboard. The application should remain simple to
operate and test on Render's free tier.

## Decision

Clients poll `GET /games/{code}/state` every 2 seconds. The server evaluates
the upload deadline on every state read. No background jobs are used for
deadline transitions.

## Alternatives

- WebSockets.
- Supabase realtime.

## Consequences

Polling is simple, works on the Render free tier, and is easy to test with
ordinary HTTP requests. It avoids background-job infrastructure, but creates
regular request traffic and updates may be delayed by up to the polling
interval, which is acceptable for this game. Deadline transitions occur only
when a read or other request checks the game state.
