"""An in-memory SQLite database with a small analytics schema and sample data.

Using the standard-library ``sqlite3`` module means generated SQL is executed for
real, so results are genuine and the guardrails are tested against an actual engine
rather than a mock. The schema and rows are fixed and seeded, so every query and
every benchmark answer is reproducible.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

_SCHEMA = """
CREATE TABLE departments (
    name   TEXT PRIMARY KEY,
    budget INTEGER NOT NULL,
    location TEXT NOT NULL
);
CREATE TABLE employees (
    id         INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    department TEXT NOT NULL,
    salary     INTEGER NOT NULL,
    hired_year INTEGER NOT NULL
);
CREATE TABLE sales (
    id          INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    amount      INTEGER NOT NULL,
    year        INTEGER NOT NULL
);
"""

_DEPARTMENTS = [
    ("Engineering", 2_000_000, "Austin"),
    ("Sales", 1_200_000, "Denver"),
    ("Marketing", 800_000, "Austin"),
]

_EMPLOYEES = [
    (1, "Ada", "Engineering", 165_000, 2021),
    (2, "Grace", "Engineering", 150_000, 2020),
    (3, "Alan", "Engineering", 140_000, 2022),
    (4, "Katherine", "Sales", 120_000, 2021),
    (5, "Edsger", "Sales", 110_000, 2019),
    (6, "Barbara", "Marketing", 95_000, 2021),
    (7, "John", "Marketing", 90_000, 2023),
]

_SALES = [
    (1, 4, 50_000, 2022),
    (2, 4, 70_000, 2023),
    (3, 5, 40_000, 2022),
    (4, 5, 60_000, 2023),
    (5, 1, 10_000, 2023),
]


@dataclass(frozen=True)
class Column:
    """A column name and its declared type."""

    name: str
    type: str


@dataclass(frozen=True)
class Table:
    """A table name and its columns."""

    name: str
    columns: tuple[Column, ...]


def build_database() -> sqlite3.Connection:
    """Return a fresh in-memory database populated with the sample data."""

    connection = sqlite3.connect(":memory:")
    connection.executescript(_SCHEMA)
    connection.executemany("INSERT INTO departments VALUES (?, ?, ?)", _DEPARTMENTS)
    connection.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?)", _EMPLOYEES)
    connection.executemany("INSERT INTO sales VALUES (?, ?, ?, ?)", _SALES)
    connection.commit()
    return connection


def schema() -> list[Table]:
    """Return the schema (tables and columns) for prompts and guardrails."""

    connection = build_database()
    tables: list[Table] = []
    names = [
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
    ]
    for table_name in names:
        columns = tuple(
            Column(name=row[1], type=row[2])
            for row in connection.execute(f"PRAGMA table_info({table_name})")
        )
        tables.append(Table(name=table_name, columns=columns))
    connection.close()
    return tables


def schema_text() -> str:
    """Return a compact textual schema description for a prompt."""

    lines = []
    for table in schema():
        cols = ", ".join(f"{c.name} {c.type}" for c in table.columns)
        lines.append(f"{table.name}({cols})")
    return "\n".join(lines)
