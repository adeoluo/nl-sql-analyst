# Data Card - NL SQL Analyst

## Source
- **Synthetic, in-repository.** The database schema, rows, and the question benchmark are defined in
  code. There is no external dataset, download, or network access.

## Composition
- Three tables: employees (id, name, department, salary, hired_year), departments (name, budget,
  location), and sales (id, employee_id, amount, year), with a handful of rows each.
- A benchmark of 12 questions, each with a reference SQL query that defines its correct answer, and
  8 unsafe SQL strings the guardrails must block.

## Labels and supervision
- The labels are the reference SQL queries (for accuracy) and the unsafe set (for the block rate).
  There is no training.

## Provenance and licensing
- Authored for this repository under the MIT license. The names are historical computer scientists;
  the salaries and sales are invented.

## Filtering and contamination
- Not applicable: the database and benchmark are fixed and used only for evaluation.

## Known limitations
- The schema and data are small and synthetic so the benchmark is a clear, deterministic guard; they
  do not represent a production database.
