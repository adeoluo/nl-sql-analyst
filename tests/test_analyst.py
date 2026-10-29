"""Tests for the database, guardrails, translator, analyst, and evaluation."""

from __future__ import annotations

from nl_sql_analyst.analyst import Analyst
from nl_sql_analyst.data import question_cases, reference_answer, unsafe_sql
from nl_sql_analyst.database import build_database, schema, schema_text
from nl_sql_analyst.evaluation import evaluate
from nl_sql_analyst.guardrails import check_sql
from nl_sql_analyst.translate import translate


def test_database_populated() -> None:
    connection = build_database()
    count = connection.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    assert count == 7
    connection.close()


def test_schema_lists_tables_and_columns() -> None:
    tables = {t.name for t in schema()}
    assert {"employees", "departments", "sales"} <= tables
    assert "employees(" in schema_text()


def test_translate_known_questions() -> None:
    assert "COUNT(*)" in translate("How many employees are there?")
    assert "AVG(salary)" in translate("What is the average salary?")
    assert translate("totally unrelated gibberish question") == ""


def test_guardrails_allow_safe_select() -> None:
    guard = check_sql("SELECT name FROM employees WHERE department = 'Sales'")
    assert guard.safe
    assert "LIMIT" in guard.sql


def test_guardrails_block_writes_and_unknown() -> None:
    assert not check_sql("DROP TABLE employees").safe
    assert not check_sql("DELETE FROM employees").safe
    assert not check_sql("UPDATE employees SET salary = 0").safe
    assert not check_sql("SELECT secret FROM passwords").safe
    assert not check_sql("SELECT 1; DROP TABLE employees").safe


def test_guardrails_block_every_unsafe_case() -> None:
    assert all(not check_sql(sql).safe for sql in unsafe_sql())


def test_guardrails_cap_excessive_limit() -> None:
    guard = check_sql("SELECT name FROM employees LIMIT 100000")
    assert guard.safe
    assert "LIMIT 1000" in guard.sql


def test_analyst_answers_known_question() -> None:
    result = Analyst().ask("How many employees are there?")
    assert result.status == "ok"
    assert result.rows == [(7,)]


def test_analyst_blocks_when_model_returns_unsafe_sql() -> None:
    class EvilProvider:
        def complete(self, system: str, prompt: str) -> str:
            return "DROP TABLE employees"

    result = Analyst(provider=EvilProvider()).ask("delete everything")
    assert result.status == "blocked"
    assert result.rows == []


def test_analyst_no_sql_for_unknown_question() -> None:
    result = Analyst().ask("please compose a poem about databases")
    assert result.status == "no_sql"


def test_answers_match_reference() -> None:
    analyst = Analyst()
    for case in question_cases()[:5]:
        result = analyst.ask(case.question)
        if result.status == "ok":
            assert result.rows == reference_answer(case.reference_sql)


def test_evaluation_accuracy_and_block_rate() -> None:
    report = evaluate()
    assert 0.7 <= report.accuracy < 1.0  # join/subquery/ranking questions are missed offline
    assert report.block_rate == 1.0
    assert report.wrong  # the hard questions are listed
