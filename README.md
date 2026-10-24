# PicMe

PicMe is a student teaching project that explores building software with
AI-assisted workflows. It is for the project team and anyone learning how to
apply the AI-SDLC in a small, practical codebase.

## How we work

We follow the AI-SDLC: `AGENTS.md` routes phases, `docs/TASKS.md` tracks state,
`docs/PROJECT.md` holds context and commands, `docs/specs/` contains use-case
specifications, and `skills/` provides phase-specific guidance. We write tests
before code and open pull requests for review before merging.

## AI tooling

- Coding agent: OpenCode
- Model: `GPT-5.6 Luna`, chosen because it is the coding model
  supplied by the FHNW LiteLLM gateway for this project and using open-weight model for comparison with other availiable models. GPT-5.6 Luna uses a little bit more credits, while offering better quality and speed for task execution.
- Access is via the FHNW LiteLLM gateway; API keys are stored only in GitHub
  Codespaces secrets.
- MCP server: `baissue` (`https://gitmcp.io/AIaSDev/BAIssue`) gives the agent
  read-only access to the public BAIssue reference-architecture repository;
  no credentials are required.

## Status

## Deployment

- **Live:** https://picme-latest.onrender.com (API docs at `/docs`)
- **Hosting:** Render free web service running the Docker image
  `ghcr.io/platonuser/picme`; database on Neon (serverless PostgreSQL, Frankfurt).
- **Pipeline:**
  1. `ci.yml` runs on every pull request and on `main`: structure check, unit and
     integration tests, Docker build plus E2E tests against the container.
  2. `release.yml` runs on a tag `v*`: builds the image, runs the E2E tests against it,
     pushes it to GHCR (`:<tag>` and `:latest`) and creates a GitHub Release.
  3. `cd.yml` runs after a successful Release: triggers the Render deploy hook, waits
     for `/health`, then runs the E2E tests against the live URL. It can also be started
     by hand (Actions → CD → Run workflow).
- **Release:** `git tag vX.Y.Z && git push origin vX.Y.Z`
- **Configuration:** `DATABASE_URL` is set only in Render; the deploy hook is the GitHub
  secret `RENDER_DEPLOY_HOOK_URL`, the URL the variable `RENDER_URL`. No credentials are
  stored in the repository.
- **Limits:** the free Render instance sleeps after 15 minutes without traffic (first
  request then takes about a minute); Neon scales to zero when idle. The health check
  after a deploy can briefly hit the previous version, so CD waits 90 seconds first.

Sprint 2 (use cases with TDD) in progress.
