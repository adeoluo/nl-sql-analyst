"""A dependency-free HTTP service exposing the natural-language-to-SQL analyst.

The service answers questions over the sample database, always through the
guardrails, and reports its accuracy and guardrail coverage. By default it uses the
offline translator, so it runs with no credentials; a real provider can be injected
in production. The routing logic is a pure function tested without a socket.

Endpoints
---------
``GET  /health``   liveness, the active provider, and the schema.
``GET  /ready``    readiness.
``GET  /metrics``  per-route request, error, and latency metrics (Prometheus text).
``POST /ask``      body ``{"question": str}``; the SQL and verified result rows.
``POST /check``    body ``{"sql": str}``; whether the SQL passes the guardrails.
``GET  /evaluate`` answer accuracy and guardrail block rate on the benchmark.
"""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from nl_sql_analyst.analyst import Analyst
from nl_sql_analyst.database import schema_text
from nl_sql_analyst.evaluation import evaluate
from nl_sql_analyst.guardrails import check_sql
from nl_sql_analyst.observability import ServiceMetrics
from nl_sql_analyst.provider import FakeProvider, Provider

JsonObject = dict[str, Any]
_MAX_QUESTION = 2000
_MAX_SQL = 5000


@dataclass(frozen=True)
class AnalystService:
    """Holds an analyst and answers question, check, and evaluation requests."""

    analyst: Analyst
    provider_name: str
    metrics: ServiceMetrics = field(default_factory=ServiceMetrics)

    @classmethod
    def with_provider(cls, provider: Provider | None = None) -> AnalystService:
        provider = provider or FakeProvider()
        return cls(analyst=Analyst(provider=provider), provider_name=type(provider).__name__)

    def ask(self, question: str) -> JsonObject:
        result = self.analyst.ask(question)
        return {
            "status": result.status,
            "sql": result.sql,
            "columns": list(result.columns),
            "rows": [list(row) for row in result.rows],
            "reasons": list(result.reasons),
        }

    def check(self, sql: str) -> JsonObject:
        guard = check_sql(sql)
        return {"safe": guard.safe, "reasons": list(guard.reasons), "sql": guard.sql}

    def evaluate(self) -> JsonObject:
        report = evaluate(self.analyst)
        return {
            "accuracy": round(report.accuracy, 6),
            "correct": report.correct,
            "total": report.total,
            "block_rate": round(report.block_rate, 6),
            "missed": list(report.wrong),
        }


def _route(
    method: str, path: str, body: Mapping[str, Any], service: AnalystService
) -> tuple[int, JsonObject]:
    if method == "GET" and path == "/health":
        return 200, {"status": "ok", "provider": service.provider_name, "schema": schema_text()}
    if method == "GET" and path == "/evaluate":
        return 200, service.evaluate()
    if method == "POST" and path == "/ask":
        question = body.get("question")
        if not isinstance(question, str) or not question or len(question) > _MAX_QUESTION:
            return 400, {
                "error": (
                    f"'question' must be a non-empty string of at most {_MAX_QUESTION} characters"
                )
            }
        return 200, service.ask(question)
    if method == "POST" and path == "/check":
        sql = body.get("sql")
        if not isinstance(sql, str) or not sql or len(sql) > _MAX_SQL:
            return 400, {
                "error": f"'sql' must be a non-empty string of at most {_MAX_SQL} characters"
            }
        return 200, service.check(sql)
    return 404, {"error": f"no route for {method} {path}"}


def handle(
    method: str, path: str, body: Mapping[str, Any], service: AnalystService
) -> tuple[int, JsonObject]:
    """Route a request, recording per-route metrics, and return status and payload."""

    if method == "GET" and path == "/ready":
        return 200, {"status": "ready"}
    start = time.perf_counter()
    status, payload = _route(method, path, body, service)
    service.metrics.observe(
        f"{method} {path}", (time.perf_counter() - start) * 1000.0, error=status >= 400
    )
    return status, payload


class _Handler(BaseHTTPRequestHandler):  # pragma: no cover - exercised over sockets
    service: AnalystService

    def _respond(self, status: int, payload: JsonObject) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        if self.path == "/metrics":
            body = self.service.metrics.render_prometheus().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        status, payload = handle("GET", self.path, {}, self.service)
        self._respond(status, payload)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self._respond(400, {"error": "request body is not valid JSON"})
            return
        status, payload = handle("POST", self.path, body, self.service)
        self._respond(status, payload)

    def log_message(self, *_: Any) -> None:
        return


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:  # pragma: no cover
    """Start the HTTP service (blocking)."""

    handler = type("_BoundHandler", (_Handler,), {"service": AnalystService.with_provider()})
    server = ThreadingHTTPServer((host, port), handler)
    print(f"nl-sql-analyst service listening on http://{host}:{port}")
    server.serve_forever()
