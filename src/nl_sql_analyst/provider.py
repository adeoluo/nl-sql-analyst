"""The language-model provider interface, a deterministic fake, and a real client.

The analyst depends only on the :class:`Provider` protocol, which turns a prompt
into a text completion. Two implementations are shipped:

* :class:`FakeProvider` is deterministic, offline, and rule-based. It is what the
  tests, benchmarks, and continuous integration use, so the pipeline is fully
  reproducible without network access or credentials.
* :class:`AnthropicProvider` calls the real Claude Messages API over HTTPS using
  only the standard library, so production has no third-party dependency. It reads
  its key from the environment and is never exercised by the test suite.

Keeping the two behind one protocol means the analyst's logic is identical in
tests and in production; only the model backend changes.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Protocol, runtime_checkable


@runtime_checkable
class Provider(Protocol):
    """Turns a prompt into a text completion."""

    def complete(self, system: str, prompt: str) -> str: ...


class FakeProvider:
    """A deterministic, offline provider that translates a question to SQL.

    It does not call a model. It extracts the question embedded in the prompt and
    maps it to SQL with keyword rules, so the whole pipeline (prompting, guardrail
    checks, execution, verification, scoring) runs reproducibly with no network
    access. Production swaps in the real model behind the same interface.
    """

    _START = "QUESTION:"
    _END = "<<END>>"

    def complete(self, system: str, prompt: str) -> str:
        from nl_sql_analyst.translate import translate

        start = prompt.find(self._START)
        end = prompt.find(self._END)
        if start == -1 or end == -1:
            return ""
        question = prompt[start + len(self._START) : end].strip()
        return translate(question)


class AnthropicProvider:  # pragma: no cover - requires network and credentials
    """Calls the Claude Messages API over HTTPS using only the standard library."""

    def __init__(
        self,
        *,
        model: str = "claude-3-5-sonnet-latest",
        api_key: str | None = None,
        timeout: float = 30.0,
        max_tokens: int = 1024,
    ) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.timeout = timeout
        self.max_tokens = max_tokens
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")

    def complete(self, system: str, prompt: str) -> str:
        body = json.dumps(
            {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "system": system,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "content-type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        parts = payload.get("content", [])
        return "".join(part.get("text", "") for part in parts if part.get("type") == "text")
