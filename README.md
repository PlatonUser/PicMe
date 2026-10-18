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
- Model: `kimi-k2.7-code`, chosen because it is the coding model
  supplied by the FHNW LiteLLM gateway for this project and using open-weight model for comparison with GPT-5.6 Luna. Kimi uses less credits, while keeping almost the same quality and time for task execution.
- Access is via the FHNW LiteLLM gateway; API keys are stored only in GitHub
  Codespaces secrets.
- MCP server: `baissue` (`https://gitmcp.io/AIaSDev/BAIssue`) gives the agent
  read-only access to the public BAIssue reference-architecture repository;
  no credentials are required.

## Status

Sprint 1 (foundation) is in progress.
