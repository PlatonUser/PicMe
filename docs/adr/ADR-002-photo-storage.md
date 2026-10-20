# ADR-002: Photo Storage

- **Status:** Proposed
- **Date:** 2026-10-18

## Context

Each player submits one compressed JPEG per round, with replacement allowed
until uploads close. The application needs a storage boundary without tying the
domain and application services to a provider.

## Decision

Store compressed JPEG bytes in the database behind a `PhotoStorage` port. The
application enforces the JPEG and 2 MB limits before storage.

## Alternatives

- Render disk, which is wiped on every deploy.
- Supabase or S3 storage, which adds another service and credential keys.

## Consequences

Deployment remains self-contained and the storage adapter is easy to replace
later. Database size and backup requirements increase, and photo retrieval
must be handled efficiently enough for the intended small party games.
