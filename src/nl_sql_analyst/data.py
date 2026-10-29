"""A labeled benchmark of questions with a reference SQL for ground-truth answers.

Each case pairs a natural-language question with a reference SQL query known to be
correct. The expected answer is computed by executing the reference against the
sample database, and the analyst is scored on whether its own generated SQL
produces the same answer. A separate set of unsafe SQL strings checks that the
guardrails block every one.
"""

from __future__ import annotations

from dataclasses import dataclass

from nl_sql_analyst.database import build_database


@dataclass(frozen=True)
class QuestionCase:
    """A question and the reference SQL that defines its correct answer."""

    question: str
    reference_sql: str


def question_cases() -> list[QuestionCase]:
    """Return the labeled natural-language-to-SQL benchmark."""

    return [
        QuestionCase("How many employees are there?", "SELECT COUNT(*) FROM employees"),
        QuestionCase("What is the average salary?", "SELECT AVG(salary) FROM employees"),
        QuestionCase(
            "What is the average salary in Engineering?",
            "SELECT AVG(salary) FROM employees WHERE department = 'Engineering'",
        ),
        QuestionCase(
            "List the names of employees in Sales",
            "SELECT name FROM employees WHERE department = 'Sales'",
        ),
        QuestionCase("What is the total sales amount?", "SELECT SUM(amount) FROM sales"),
        QuestionCase(
            "Which department has the highest budget?",
            "SELECT name FROM departments ORDER BY budget DESC LIMIT 1",
        ),
        QuestionCase(
            "How many employees are in Marketing?",
            "SELECT COUNT(*) FROM employees WHERE department = 'Marketing'",
        ),
        QuestionCase("What is the maximum salary?", "SELECT MAX(salary) FROM employees"),
        QuestionCase(
            "List employees hired in 2021",
            "SELECT name FROM employees WHERE hired_year = 2021",
        ),
        QuestionCase(
            "Who are the two highest paid employees?",
            "SELECT name FROM employees ORDER BY salary DESC LIMIT 2",
        ),
        QuestionCase(
            "What is the total sales amount for each salesperson?",
            "SELECT e.name, SUM(s.amount) FROM sales s "
            "JOIN employees e ON s.employee_id = e.id GROUP BY e.name",
        ),
        QuestionCase(
            "Which employees earn more than the average salary?",
            "SELECT name FROM employees WHERE salary > (SELECT AVG(salary) FROM employees)",
        ),
    ]


def unsafe_sql() -> list[str]:
    """Return SQL strings the guardrails must block."""

    return [
        "DROP TABLE employees",
        "DELETE FROM employees",
        "UPDATE employees SET salary = 0",
        "INSERT INTO employees VALUES (99, 'x', 'y', 0, 2020)",
        "SELECT * FROM employees; DELETE FROM employees",
        "SELECT password FROM secrets",
        "ALTER TABLE employees ADD COLUMN ssn TEXT",
        "PRAGMA table_info(employees)",
    ]


def reference_answer(reference_sql: str) -> list[tuple[object, ...]]:
    """Execute a reference SQL against the sample database and return the rows."""

    connection = build_database()
    try:
        return [tuple(row) for row in connection.execute(reference_sql).fetchall()]
    finally:
        connection.close()
