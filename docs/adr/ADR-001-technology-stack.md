# ADR-001: Technology Stack

- **Status:** Proposed
- **Date:** 2026-10-18

## Context

PicMe needs a small HTTP application with testable domain and application
logic. An earlier prototype used Next.js and Supabase, but the course reference
architecture favors explicit Clean Architecture boundaries and business logic
outside database functions.

## Decision

Use Python with FastAPI, SQLAlchemy, and SQLite for development and CI with
PostgreSQL in production. Package the application in Docker and deploy it on
Render. Replace the earlier Next.js + Supabase prototype rather than extending
it.

## Alternatives

- Keep the Next.js + Supabase prototype.

## Consequences

The stack matches the course reference architecture and keeps business rules
in Python services where they are straightforward to unit test. The project
must maintain database portability between SQLite and PostgreSQL and manage
the Docker/Render runtime configuration.
