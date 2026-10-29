# Threat Model - NL SQL Analyst

## Assets
- The database's integrity (it must never be modified), the service's availability, and any
  credentials used by a production provider.

## Trust boundaries
- The user's question and any model output are untrusted. The guardrails are the trust boundary in
  front of the database. In production the schema and question are sent to a third-party model.

## Entry points and mitigations

### `POST /ask`
- **Malformed JSON** is rejected with 400 before routing.
- **Validation:** the question must be a non-empty string within a size bound.
- **Guardrails:** the SQL the model returns is validated to be a single read-only, in-scope, bounded
  SELECT before execution; anything else is blocked and never run.

### `POST /check`
- Validates a SQL string without executing it, so callers can test the guardrails safely.

### `GET` routes
- `/health`, `/ready`, `/evaluate`, and `/metrics` take no user input and return fixed-shape
  payloads. `/metrics` exposes only aggregate counters.

## Provider and credentials
- The offline translator needs no secrets. The Anthropic provider reads its key from the
  environment, never from the request, and never logs it. CI uses only the offline translator.

## Data handling
- Only read-only queries run, so the database cannot be modified through the analyst. The row cap
  bounds the size of any result.

## Supply chain
- Zero third-party runtime dependencies; the database is the standard-library SQLite and the
  production provider uses the standard-library HTTP client. Development tooling is pinned via
  `uv.lock`. CodeQL and dependency scanning run in CI.

## Residual risk
- A legitimate but expensive query is allowed within the row limit; a deployment would add a query
  timeout and rate limiting behind a reverse proxy.
