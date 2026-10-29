# ADR-0003: Execute against a real SQLite database

- **Status:** Accepted
- **Date:** 2026-01-01

## Context
The analyst could mock query execution, but then the guardrails would be tested against a fiction
and the returned answers would not be real. The project should demonstrate genuine end-to-end
behavior without adding a dependency.

## Decision
Use the standard-library ``sqlite3`` module with a seeded in-memory database. Generated and
validated SQL is executed for real, and the result rows are returned and compared against reference
answers in the benchmark.

## Consequences
- Answers are genuine query results, and the guardrails face an actual SQL engine, so a query that
  passes validation but is still invalid fails at execution and is reported.
- There is no third-party dependency, because SQLite ships with Python.
- The database is rebuilt per request for isolation, which costs a few milliseconds; a real
  deployment would use a persistent connection pool.
