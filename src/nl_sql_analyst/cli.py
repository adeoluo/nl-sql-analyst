"""Command line interface for the natural-language-to-SQL analyst."""

from __future__ import annotations

import argparse

from nl_sql_analyst.analyst import Analyst
from nl_sql_analyst.database import schema_text
from nl_sql_analyst.evaluation import evaluate
from nl_sql_analyst.guardrails import check_sql


def _cmd_evaluate(_: argparse.Namespace) -> None:
    report = evaluate()
    print("Natural-language-to-SQL evaluation:")
    print(f"  {report.format()}")
    if report.wrong:
        print(
            f"  missed (need joins, subqueries, or ranking): {len(report.wrong)} of {report.total}"
        )


def _cmd_ask(args: argparse.Namespace) -> None:
    result = Analyst().ask(args.question)
    print(f"status: {result.status}")
    if result.sql:
        print(f"sql:    {result.sql}")
    if result.reasons:
        print(f"reasons: {', '.join(result.reasons)}")
    for row in result.rows[:10]:
        print(f"  {row}")


def _cmd_check(args: argparse.Namespace) -> None:
    guard = check_sql(args.sql)
    print(f"safe: {guard.safe}")
    if guard.reasons:
        print(f"reasons: {', '.join(guard.reasons)}")
    if guard.sql:
        print(f"sql: {guard.sql}")


def _cmd_schema(_: argparse.Namespace) -> None:
    print(schema_text())


def _cmd_serve(args: argparse.Namespace) -> None:
    from nl_sql_analyst.service import serve

    serve(host=args.host, port=args.port)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="nl-sql-analyst", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("evaluate", help="answer accuracy and guardrail block rate on the benchmark")
    sub.add_parser("schema", help="print the database schema")

    ask = sub.add_parser("ask", help="answer a natural-language question")
    ask.add_argument("question")

    check = sub.add_parser("check", help="check whether a SQL string passes the guardrails")
    check.add_argument("sql")

    serve = sub.add_parser("serve", help="start the HTTP service")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)

    handlers = {
        "evaluate": _cmd_evaluate,
        "schema": _cmd_schema,
        "ask": _cmd_ask,
        "check": _cmd_check,
        "serve": _cmd_serve,
    }
    args = parser.parse_args(argv)
    handlers[args.command](args)


if __name__ == "__main__":
    main()
