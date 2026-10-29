"""Evaluation: answer accuracy against reference SQL and guardrail block rate."""

from __future__ import annotations

from dataclasses import dataclass

from nl_sql_analyst.analyst import Analyst
from nl_sql_analyst.data import question_cases, reference_answer, unsafe_sql
from nl_sql_analyst.guardrails import check_sql


@dataclass(frozen=True)
class AnalystReport:
    """Answer accuracy and guardrail block rate."""

    correct: int
    total: int
    unsafe_blocked: int
    unsafe_total: int
    wrong: tuple[str, ...]

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0

    @property
    def block_rate(self) -> float:
        return self.unsafe_blocked / self.unsafe_total if self.unsafe_total else 1.0

    def format(self) -> str:
        return (
            f"answer accuracy={self.accuracy:.3f} ({self.correct}/{self.total}); "
            f"guardrail block rate={self.block_rate:.3f} "
            f"({self.unsafe_blocked}/{self.unsafe_total})"
        )


def _answers_match(a: list[tuple[object, ...]], b: list[tuple[object, ...]]) -> bool:
    return a == b


def evaluate(analyst: Analyst | None = None) -> AnalystReport:
    """Score answer accuracy against reference SQL and guardrail coverage."""

    analyst = analyst or Analyst()
    correct = 0
    wrong: list[str] = []
    cases = question_cases()
    for case in cases:
        result = analyst.ask(case.question)
        expected = reference_answer(case.reference_sql)
        if result.status == "ok" and _answers_match(result.rows, expected):
            correct += 1
        else:
            wrong.append(case.question)

    unsafe = unsafe_sql()
    blocked = sum(1 for sql in unsafe if not check_sql(sql).safe)

    return AnalystReport(
        correct=correct,
        total=len(cases),
        unsafe_blocked=blocked,
        unsafe_total=len(unsafe),
        wrong=tuple(wrong),
    )
