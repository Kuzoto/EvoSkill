from __future__ import annotations

import asyncio

import pytest


def test_opencode_runtime_requires_openrouter_api_key_for_openrouter_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    from src.harness.opencode.executor import execute_query

    with pytest.raises(RuntimeError, match="OpenRouter API key not configured"):
        asyncio.run(
            execute_query(
                {
                    "system": "Answer the question with the final answer only.",
                    "format": {"type": "json_schema", "schema": {"type": "object"}},
                    "tools": {"read": True},
                    "mode": "build",
                    "provider_id": "openrouter",
                    "model_id": "openai/gpt-5-mini",
                    "cwd": ".",
                },
                "What is 2 + 2?",
            )
        )
