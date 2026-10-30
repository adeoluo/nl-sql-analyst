"""A large-workload scale benchmark for the natural-language-to-SQL analyst.

Where ``benchmark.py`` scores accuracy and guardrail coverage on the small
labeled benchmark and ``stress.py`` drives the HTTP service under concurrent
load, this script measures the core operation - :meth:`Analyst.ask`, which
translates a question to SQL, enforces the read-only guardrail, and executes it -
on progressively larger synthetic query streams. It reports wall-clock time,
throughput, peak memory (via the standard-library :mod:`tracemalloc`), answer
accuracy against reference SQL, and the guardrail block rate on unsafe queries.

The query stream is sampled deterministically from the labeled benchmark
(nothing is downloaded), so the run is reproducible, fully offline, and the model
call is the deterministic offline fake provider. Run with:

    uv run python benchmarks/scale.py
"""

from __future__ import annotations

import random
import time
import tracemalloc
from dataclasses import dataclass

from nl_sql_analyst.analyst import Analyst
from nl_sql_analyst.data import question_cases, reference_answer, unsafe_sql
from nl_sql_analyst.guardrails import check_sql

WORKLOAD_SIZES: tuple[int, ...] = (500, 1_000, 2_000, 4_000)

_MEMORY_PROBE = 200


@dataclass(frozen=True, slots=True)
class ScaleRow:
    """One measured row of the scale sweep."""

    size: int
    seconds: float
    throughput: float
    peak_mib: float
    accuracy: float
    block_rate: float


def run_workload(size: int, *, seed: int = 0) -> ScaleRow:
    """Answer ``size`` sampled questions and block ``size`` sampled unsafe queries.

    Timing and throughput cover the full :meth:`Analyst.ask` pipeline; peak
    memory is probed over a bounded batch of asks (each ask builds and tears down
    its own in-memory database, so the footprint is constant in ``size``).
    """
    analyst = Analyst()
    cases = question_cases()
    unsafe = unsafe_sql()
    references = {case.question: reference_answer(case.reference_sql) for case in cases}
    rng = random.Random(seed)
    questions = [cases[rng.randrange(len(cases))] for _ in range(size)]
    unsafe_stream = [unsafe[rng.randrange(len(unsafe))] for _ in range(size)]

    tracemalloc.start()
    for case in questions[: min(size, _MEMORY_PROBE)]:
        analyst.ask(case.question)
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    correct = 0
    start = time.perf_counter()
    for case in questions:
        result = analyst.ask(case.question)
        if result.status == "ok" and result.rows == references[case.question]:
            correct += 1
    elapsed = time.perf_counter() - start

    blocked = sum(1 for sql in unsafe_stream if not check_sql(sql).safe)
    throughput = size / elapsed if elapsed > 0 else float("inf")
    return ScaleRow(
        size,
        elapsed,
        throughput,
        peak / (1024 * 1024),
        correct / size if size else 0.0,
        blocked / size if size else 1.0,
    )


def main() -> None:
    print("NL-SQL Analyst scale benchmark")
    print("Data is SYNTHETIC: questions and unsafe SQL sampled from the labeled benchmark.")
    print("The model call uses the deterministic offline fake provider.\n")
    header = (
        f"{'queries':>8}  {'seconds':>8}  {'queries/sec':>12}  "
        f"{'peak MiB':>9}  {'accuracy':>9}  {'block rate':>11}"
    )
    print(header)
    print("-" * len(header))
    for size in WORKLOAD_SIZES:
        row = run_workload(size)
        print(
            f"{row.size:>8,}  {row.seconds:>8.3f}  {row.throughput:>12,.0f}  "
            f"{row.peak_mib:>9.3f}  {row.accuracy:>9.3f}  {row.block_rate:>11.3f}"
        )


if __name__ == "__main__":
    main()
