"""A deterministic keyword-based natural-language-to-SQL translator.

This stands in for a language model in offline mode. It recognizes a set of common
analytics question shapes over the sample schema and maps them to SQL. It is
intentionally simple: real translation is the job of the production model, but a
deterministic translator lets the guardrails, execution, verification, and the
accuracy benchmark run reproducibly.
"""

from __future__ import annotations

import re

_DEPARTMENTS = ("engineering", "sales", "marketing")


def _find_department(question: str) -> str | None:
    for dept in _DEPARTMENTS:
        if dept in question:
            return dept.capitalize()
    return None


def _find_year(question: str) -> str | None:
    match = re.search(r"\b(19|20)\d{2}\b", question)
    return match.group(0) if match else None


def translate(question: str) -> str:
    """Translate a natural-language ``question`` to SQL, or return an empty string."""

    q = question.lower().strip()
    dept = _find_department(q)
    year = _find_year(q)

    if "average" in q and "salary" in q:
        if dept:
            return f"SELECT AVG(salary) FROM employees WHERE department = '{dept}'"
        return "SELECT AVG(salary) FROM employees"
    if ("maximum" in q or "highest" in q) and "salary" in q:
        return "SELECT MAX(salary) FROM employees"
    if ("minimum" in q or "lowest" in q) and "salary" in q:
        return "SELECT MIN(salary) FROM employees"
    if "total" in q and "sales" in q:
        return "SELECT SUM(amount) FROM sales"
    if "highest budget" in q or (
        "department" in q and "budget" in q and ("highest" in q or "most" in q)
    ):
        return "SELECT name FROM departments ORDER BY budget DESC LIMIT 1"
    if "how many" in q and "employee" in q:
        if dept:
            return f"SELECT COUNT(*) FROM employees WHERE department = '{dept}'"
        return "SELECT COUNT(*) FROM employees"
    if ("list" in q or "names" in q or "who" in q) and "employee" in q:
        if dept:
            return f"SELECT name FROM employees WHERE department = '{dept}'"
        if year:
            return f"SELECT name FROM employees WHERE hired_year = {year}"
        return "SELECT name FROM employees"
    if "hired" in q and year:
        return f"SELECT name FROM employees WHERE hired_year = {year}"
    if "how many" in q and "department" in q:
        return "SELECT COUNT(*) FROM departments"
    return ""
