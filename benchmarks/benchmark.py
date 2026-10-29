"""A deterministic micro-benchmark for the natural-language-to-SQL analyst.

Reports answer accuracy against reference SQL and the guardrail block rate on unsafe
queries. Deterministic and offline; run with:

    uv run python benchmarks/benchmark.py
"""

from __future__ import annotations

import time

from nl_sql_analyst.evaluation import evaluate


def main() -> None:
    start = time.perf_counter()
    report = evaluate()
    elapsed = (time.perf_counter() - start) * 1000
    print(f"Analyst benchmark ({report.total} questions, {elapsed:.0f} ms):")
    print(f"  {report.format()}")
    if report.wrong:
        print(f"  missed offline (need joins, subqueries, or ranking): {len(report.wrong)}")


if __name__ == "__main__":
    main()
