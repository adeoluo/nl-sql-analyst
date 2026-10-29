"""The analyst pipeline: question to SQL to guardrail to execution to verified result."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from nl_sql_analyst.database import build_database, schema_text
from nl_sql_analyst.guardrails import check_sql
from nl_sql_analyst.provider import FakeProvider, Provider

_SYSTEM = (
    "You translate a question into a single read-only SQLite SELECT over the given schema. "
    "Return only SQL, no explanation. Never modify data."
)


@dataclass(frozen=True)
class AnalystResult:
    """The outcome of answering a question."""

    status: str  # "ok", "blocked", or "no_sql"
    sql: str
    columns: tuple[str, ...]
    rows: list[tuple[object, ...]]
    reasons: tuple[str, ...]


def build_prompt(question: str) -> str:
    """Return the prompt that embeds the schema and the question."""

    return (
        f"Schema:\n{schema_text()}\n\nQUESTION:{question}<<END>>\nReturn a single read-only SELECT."
    )


@dataclass
class Analyst:
    """Answers natural-language questions over the sample database."""

    provider: Provider = None  # type: ignore[assignment]
    max_limit: int = 1000

    def __post_init__(self) -> None:
        if self.provider is None:
            self.provider = FakeProvider()

    def ask(self, question: str) -> AnalystResult:
        """Translate, validate, execute, and verify an answer to ``question``."""

        candidate = self.provider.complete(_SYSTEM, build_prompt(question)).strip()
        if not candidate:
            return AnalystResult("no_sql", "", (), [], ("no_sql_generated",))

        guard = check_sql(candidate, max_limit=self.max_limit)
        if not guard.safe:
            return AnalystResult("blocked", candidate, (), [], guard.reasons)

        connection = build_database()
        try:
            cursor = connection.execute(guard.sql)
            columns = tuple(desc[0] for desc in cursor.description or ())
            rows = [tuple(row) for row in cursor.fetchall()]
        except sqlite3.Error as exc:
            return AnalystResult("blocked", guard.sql, (), [], (f"execution_error:{exc}",))
        finally:
            connection.close()
        return AnalystResult("ok", guard.sql, columns, rows, ())
