# Model / System Card - NL SQL Analyst

## Overview
- **What it is:** a natural-language-to-SQL analyst with read-only guardrails and result
  verification, executing against a real SQLite database. No third-party dependency.
- **Base model:** pluggable. Offline, a keyword translator is used for tests and CI; in production,
  Anthropic's Claude via the Messages API.
- **Version and date:** 0.1.0, 2026.

## Intended use
- **Primary use case:** answering analytics questions over a known schema in plain English, safely.
- **Primary users:** teams exposing a database to non-technical users through natural language.

## Out-of-scope / prohibited use
- Not a replacement for access control; the guardrails scope queries but do not authenticate users.
- The offline translator handles common shapes only; do not expect it to answer joins or subqueries.

## Performance
- Answer accuracy 0.750 and guardrail block rate 1.000 on the benchmark with the offline translator.
- Full method and tables: [`EVALUATION_REPORT.md`](EVALUATION_REPORT.md).

## Limitations and failure modes
- Joins, subqueries, and ranking need the production model.
- Guardrails validate structure and scope, not query cost.

## Ethical considerations
- In production the schema and question are sent to a third-party model; the data itself is not sent.
  The analyst only ever runs read-only queries, so it cannot modify the database.
