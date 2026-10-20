# ADR-001: Technology Stack

- **Status:** Approved
- **Date:** 2026-10-18

## Context

PicMe needs a small HTTP application with testable domain and application
logic. An earlier prototype used Next.js and Supabase, but the course reference
architecture favors explicit Clean Architecture boundaries and business logic
outside database functions. The application must run locally and in CI with
SQLite, while production uses PostgreSQL in a Docker deployment on Render.

## Decision

Use Python with FastAPI and SQLAlchemy, SQLite for development and CI, and
PostgreSQL in production. Package the application in Docker and deploy it on
Render. Replace the earlier Next.js + Supabase prototype rather than extending
it, and keep business logic in Python domain/application services rather than
database functions.

## Alternatives

- Keep the Next.js + Supabase prototype.
- Put business rules in PostgreSQL functions.

## Consequences

The stack matches the course reference architecture and keeps business rules
in Python services where they are straightforward to unit test. The project
must maintain database portability between SQLite and PostgreSQL and manage
the Docker/Render runtime configuration.
