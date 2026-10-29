"""NL SQL Analyst - natural-language questions answered with guarded SQL."""

from __future__ import annotations

from nl_sql_analyst.analyst import Analyst, AnalystResult, build_prompt
from nl_sql_analyst.data import QuestionCase, question_cases, reference_answer, unsafe_sql
from nl_sql_analyst.database import build_database, schema, schema_text
from nl_sql_analyst.evaluation import AnalystReport, evaluate
from nl_sql_analyst.guardrails import GuardrailResult, check_sql
from nl_sql_analyst.provider import AnthropicProvider, FakeProvider, Provider
from nl_sql_analyst.translate import translate

__version__ = "0.1.0"

__all__ = [
    "Analyst",
    "AnalystReport",
    "AnalystResult",
    "AnthropicProvider",
    "FakeProvider",
    "GuardrailResult",
    "Provider",
    "QuestionCase",
    "__version__",
    "build_database",
    "build_prompt",
    "check_sql",
    "evaluate",
    "question_cases",
    "reference_answer",
    "schema",
    "schema_text",
    "translate",
    "unsafe_sql",
]
