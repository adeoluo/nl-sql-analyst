"""Tests for the HTTP service routing and the CLI."""

from __future__ import annotations

from nl_sql_analyst.cli import main
from nl_sql_analyst.service import AnalystService, handle

_SERVICE = AnalystService.with_provider()


def test_health_and_ready() -> None:
    status, payload = handle("GET", "/health", {}, _SERVICE)
    assert status == 200 and payload["provider"] == "FakeProvider"
    assert "employees(" in payload["schema"]
    status, payload = handle("GET", "/ready", {}, _SERVICE)
    assert status == 200 and payload["status"] == "ready"


def test_ask_route() -> None:
    status, payload = handle("POST", "/ask", {"question": "What is the maximum salary?"}, _SERVICE)
    assert status == 200 and payload["status"] == "ok"
    assert payload["rows"] == [[165000]]


def test_ask_blocked_when_unsafe() -> None:
    class EvilProvider:
        def complete(self, system: str, prompt: str) -> str:
            return "DELETE FROM employees"

    service = AnalystService.with_provider(EvilProvider())
    status, payload = handle("POST", "/ask", {"question": "wipe the table"}, service)
    assert status == 200 and payload["status"] == "blocked"


def test_check_route() -> None:
    status, payload = handle("POST", "/check", {"sql": "SELECT name FROM employees"}, _SERVICE)
    assert status == 200 and payload["safe"] is True
    status, payload = handle("POST", "/check", {"sql": "DROP TABLE employees"}, _SERVICE)
    assert status == 200 and payload["safe"] is False


def test_validation() -> None:
    status, _ = handle("POST", "/ask", {"question": ""}, _SERVICE)
    assert status == 400
    status, _ = handle("POST", "/check", {"sql": 5}, _SERVICE)
    assert status == 400


def test_evaluate_route() -> None:
    status, payload = handle("GET", "/evaluate", {}, _SERVICE)
    assert status == 200
    assert 0.7 <= payload["accuracy"] < 1.0
    assert payload["block_rate"] == 1.0


def test_unknown_route_and_metrics() -> None:
    status, _ = handle("GET", "/nope", {}, _SERVICE)
    assert status == 404
    handle("POST", "/ask", {"question": "How many employees are there?"}, _SERVICE)
    assert "service_requests_total" in _SERVICE.metrics.render_prometheus()


def test_cli_commands(capsys) -> None:  # type: ignore[no-untyped-def]
    main(["evaluate"])
    main(["schema"])
    main(["ask", "What is the total sales amount?"])
    main(["check", "SELECT name FROM employees"])
    out = capsys.readouterr().out
    assert "answer accuracy" in out
    assert "employees(" in out
    assert "status:" in out
    assert "safe:" in out
