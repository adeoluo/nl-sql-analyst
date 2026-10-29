# ADR-0002: Validate generated SQL before executing it

- **Status:** Accepted
- **Date:** 2026-01-01

## Context
A language model asked to write SQL can return a destructive statement (drop, delete, update), a
multi-statement injection, or a query that reads tables it should not. Executing model output
directly against a database is unsafe regardless of how good the model is.

## Decision
Validate every generated query with guardrails before execution. The SQL must be a single statement
beginning with ``SELECT``, must contain no banned keywords, must reference only known tables and
columns, and is capped with a ``LIMIT``. A query that fails any check is rejected and never run.

## Consequences
- The database cannot be modified through the analyst, because only read-only queries pass.
- Scope is enforced: a query referencing an unknown identifier is blocked, which also catches typos
  and hallucinated tables.
- Guardrails validate structure and scope, not semantic intent; a legitimate but expensive query is
  allowed within the row limit, which the documentation notes.
