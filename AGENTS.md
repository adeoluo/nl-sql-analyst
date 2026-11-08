# AGENTS.md

Working notes for coding agents and contributors in **NL SQL Analyst**. The [README](README.md)
explains what the project does and why; this file explains how to change it safely.

## Project

A natural-language-to-SQL analyst powered by a plugged-in language model, with read-only guardrails and result verification. Questions become SQL that is validated before it runs and executed against a real SQLite database.

## Layout

- `benchmarks/`: benchmark scripts and recorded results
- `docker-compose.yml`: local container setup
- `docs/`: documentation, architecture diagram source and render, design records
- `scripts/`: maintenance scripts (release, assets, data)
- `src/`: library and service source
- `tests/`: test suite

Key modules:

- `src/nl_sql_analyst/__init__.py`: NL SQL Analyst - natural-language questions answered with guarded SQL.
- `src/nl_sql_analyst/analyst.py`: The analyst pipeline: question to SQL to guardrail to execution to verified result.
- `src/nl_sql_analyst/cli.py`: Command line interface for the natural-language-to-SQL analyst.
- `src/nl_sql_analyst/data.py`: A labeled benchmark of questions with a reference SQL for ground-truth answers.
- `src/nl_sql_analyst/database.py`: An in-memory SQLite database with a small analytics schema and sample data.
- `src/nl_sql_analyst/evaluation.py`: Evaluation: answer accuracy against reference SQL and guardrail block rate.
- `src/nl_sql_analyst/guardrails.py`: Guardrails that validate generated SQL before it is executed.
- `src/nl_sql_analyst/observability.py`: In-process request metrics for the HTTP service (Prometheus text exposition).
- `src/nl_sql_analyst/provider.py`: The language-model provider interface, a deterministic fake, and a real client.
- `src/nl_sql_analyst/service.py`: A standard-library HTTP service exposing the natural-language-to-SQL analyst.
- `src/nl_sql_analyst/translate.py`: A deterministic keyword-based natural-language-to-SQL translator.

## Commands

| Command | Purpose |
|---|---|
| `make help` | Show this help |
| `make setup` | Install dependencies and pre-commit hooks |
| `make format` | Format automatically |
| `make lint` | Lint (no fixes) |
| `make type` | Type-check |
| `make test` | Run tests |
| `make coverage` | Tests with coverage gate |
| `make evaluation` | Reproduce the results table |
| `make run` | Run the HTTP service |
| `make diagram` | Render architecture diagram to SVG |
| `make docker-build` | Build the image |
| `make docker-up` | Run via docker compose |
| `make clean` | Remove caches and artifacts |
| `make all` | Full local gate (mirror of continuous integration) |
| `make changelog` | Regenerate CHANGELOG.md from Conventional Commits (git-cliff) |
| `make cut-release` | Cut a release locally: version bump, changelog, tag, GitHub release (RELEASE_VERSION=vX.Y.Z optional) |

Run the full local gate (`make all`) before committing; CI runs the same checks.

## Conventions

- Commits follow Conventional Commits (`feat:`, `fix:`, `perf:`, `refactor:`, `docs:`, `test:`, `ci:`, `chore:`).
  The changelog and the next version number are derived from them.
- Every number quoted in the README is produced by a command in this repository. When behavior
  changes, rerun that command and update the number in the same commit.
- When a component is added, removed or renamed, update `docs/architecture/architecture.mmd`
  and re-render `architecture.svg` so the diagram matches the code.
- README sections keep their fixed order. Prose avoids em and en dashes and promotional wording.
- Tests accompany behavior changes; a bug fix comes with a test that fails without it.
- Releases are cut with `make cut-release`.

## Python notes

- Python is managed with `uv`; run commands through `uv run` so the locked environment is used.
- Lint and format with `ruff`; type-check with `mypy`; tests use `pytest`.
- Public functions carry type hints and a docstring that states the contract, not the steps.
