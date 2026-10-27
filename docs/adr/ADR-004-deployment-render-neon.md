# ADR-004: Deployment with Render and Neon

- **Status:** Approved
- **Date:** 2026-10-24

## Context

PicMe needs a repeatable production deployment that uses the same Docker image
validated by the release pipeline. The application needs persistent PostgreSQL
storage while keeping the deployment and database services within the project's
free-tier constraints.

## Decision

`release.yml` builds the Docker image on tags matching `v*` and pushes the tagged
image and `latest` to `ghcr.io/platonuser/picme`. The Render free web service
pulls `ghcr.io/platonuser/picme:latest`. Production uses Neon serverless
PostgreSQL in Frankfurt.

After a successful Release, `cd.yml` triggers the Render deploy hook, waits for
`/health`, and runs the E2E tests against production. The application creates
the schema at startup with SQLAlchemy `create_all`; migrations are not used.
Production tables are reset after model changes.

## Alternatives

- Let Render build from Git, which bypasses our release pipeline.
- Use Render Postgres, whose free tier expires.
- Use Alembic migrations, deferred for now.

## Consequences

The release artifact is built, tested, and published by GitHub Actions before
Render deploys it, and production deployment is followed by health and E2E
checks. Neon provides persistent PostgreSQL storage in the selected region.
Using `create_all` keeps startup simple but requires resetting production tables
when models change and therefore does not preserve production data across
schema changes.
