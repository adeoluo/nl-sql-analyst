# Evaluation Report - NL SQL Analyst

> Reproduce with `python -m nl_sql_analyst evaluate` and `benchmarks/benchmark.py`. The database,
> benchmark, and offline translator are deterministic.

## Setup

- **Database:** a seeded in-memory SQLite database with employees, departments, and sales tables.
- **Benchmark:** 12 natural-language questions, each paired with a reference SQL query whose
  execution defines the correct answer.
- **Unsafe set:** 8 SQL strings (drop, delete, update, insert, multi-statement injection, unknown
  table, schema change, pragma) that the guardrails must block.
- **Provider:** the offline keyword translator, so results are reproducible with no credentials.
- **Metrics:** answer accuracy (generated SQL produces the reference answer) and guardrail block
  rate on the unsafe set.
- **Hardware / cost:** CPU only; the benchmark runs in tens of milliseconds. No external services.

## Results

| Metric | Value |
|---|---:|
| answer accuracy | 0.750 (9/12) |
| guardrail block rate | 1.000 (8/8) |

The offline translator answers nine of twelve questions correctly: counts, averages (overall and
filtered), list-by-filter, sum, maximum, and single-column ranking. It misses three that require a
join across tables, a subquery, or top-N ranking, which are exactly the cases the production model
handles. The guardrails block all eight unsafe queries, regardless of the model's output.

## What the guardrails enforce

A query must be a single statement that begins with ``SELECT``, contains no banned keyword
(insert, update, delete, drop, alter, create, replace, truncate, attach, pragma, vacuum), references
only known tables and columns (string literals excluded), and is bounded by a ``LIMIT`` (an
excessive limit is reduced to the cap). Each failing condition is reported as a named reason.

## Correctness of execution

Answers are produced by executing validated SQL against a real SQLite database, and a test confirms
the analyst's rows equal the reference answers for the questions it handles. A query that passes
validation but fails at execution is reported as blocked with the engine's error.

## Service performance

Each `/ask` request rebuilds the in-memory database for isolation, so throughput reflects that cost;
a stress benchmark sustains a few hundred requests per second with p50 near 18 ms. In production the
latency is dominated by the model call, and the database would be a persistent connection.

## Reproducibility

- Deterministic: the database, benchmark, and offline translator produce identical results every run.
- No network access, no credentials, no external data in CI.
- Regenerate every number with the CLI and `benchmarks/benchmark.py`.
