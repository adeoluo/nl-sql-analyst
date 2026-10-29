"""Guardrails that validate generated SQL before it is executed.

A natural-language-to-SQL system must never run a destructive or out-of-scope
query, no matter what the model returns. These guardrails enforce that the SQL is a
single read-only ``SELECT`` statement, references only known tables and columns,
contains no banned keywords, and is capped by a ``LIMIT``. Validation happens before
execution, so an unsafe query is rejected rather than run.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from nl_sql_analyst.database import schema

_BANNED = (
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "replace",
    "truncate",
    "attach",
    "pragma",
    "vacuum",
)

_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


@dataclass(frozen=True)
class GuardrailResult:
    """Whether the SQL is safe and, if not, why, plus the SQL that will run."""

    safe: bool
    reasons: tuple[str, ...]
    sql: str


def _known_identifiers() -> set[str]:
    identifiers: set[str] = set()
    for table in schema():
        identifiers.add(table.name.lower())
        for column in table.columns:
            identifiers.add(column.name.lower())
    return identifiers


# SQL keywords and functions that are allowed to appear as bare identifiers.
_ALLOWED_WORDS = frozenset(
    """select from where group by order limit asc desc and or not in is null as count
    sum avg min max distinct having on join inner left outer between like true false
    offset""".split()
)


def check_sql(sql: str, *, max_limit: int = 1000) -> GuardrailResult:
    """Validate ``sql`` as a single read-only, in-scope SELECT and apply a LIMIT."""

    reasons: list[str] = []
    cleaned = sql.strip().rstrip(";").strip()

    if not cleaned:
        return GuardrailResult(safe=False, reasons=("empty",), sql="")
    if ";" in cleaned:
        reasons.append("multiple_statements")
    if not re.match(r"(?is)^\s*select\b", cleaned):
        reasons.append("not_a_select")

    lowered = cleaned.lower()
    for word in _BANNED:
        if re.search(rf"\b{word}\b", lowered):
            reasons.append(f"banned_keyword:{word}")

    known = _known_identifiers() | _ALLOWED_WORDS
    unknown = {
        token.lower()
        for token in _IDENTIFIER.findall(cleaned)
        if not token.isdigit() and token.lower() not in known
    }
    # Allow quoted string literals; strip them before the identifier check.
    literal_free = re.sub(r"'[^']*'", "", cleaned)
    unknown = {
        token.lower() for token in _IDENTIFIER.findall(literal_free) if token.lower() not in known
    }
    if unknown:
        reasons.append(f"unknown_identifiers:{','.join(sorted(unknown))}")

    if reasons:
        return GuardrailResult(safe=False, reasons=tuple(reasons), sql="")

    final_sql = _apply_limit(cleaned, max_limit)
    return GuardrailResult(safe=True, reasons=(), sql=final_sql)


def _apply_limit(sql: str, max_limit: int) -> str:
    match = re.search(r"(?is)\blimit\s+(\d+)\b", sql)
    if match:
        current = int(match.group(1))
        if current > max_limit:
            return re.sub(r"(?is)\blimit\s+\d+\b", f"LIMIT {max_limit}", sql)
        return sql
    return f"{sql} LIMIT {max_limit}"
