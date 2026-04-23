from __future__ import annotations

import pytest


def test_resolve_openrouter_api_key_prefers_provider_specific_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "provider-key")
    monkeypatch.setenv("LLM_API_KEY", "generic-key")

    from src.harness.provider_auth import resolve_openrouter_api_key

    value, source = resolve_openrouter_api_key()

    assert value == "provider-key"
    assert source == "OPENROUTER_API_KEY"


def test_apply_openrouter_env_mirrors_key_into_both_common_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "provider-key")

    from src.harness.provider_auth import apply_openrouter_env

    env: dict[str, str] = {}
    apply_openrouter_env("openrouter", env)

    assert env["OPENROUTER_API_KEY"] == "provider-key"
    assert env["LLM_API_KEY"] == "provider-key"


def test_ensure_openrouter_api_key_raises_clear_error_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    from src.harness.provider_auth import ensure_openrouter_api_key

    with pytest.raises(RuntimeError, match="OpenRouter API key not configured"):
        ensure_openrouter_api_key("openrouter")
