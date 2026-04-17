"""Provider-specific auth helpers for harness runtimes."""

from __future__ import annotations

import os


def resolve_openrouter_api_key() -> tuple[str | None, str | None]:
    """Return the first configured OpenRouter-compatible API key and its source env var."""
    for env_name in ("OPENROUTER_API_KEY", "LLM_API_KEY"):
        value = os.environ.get(env_name)
        if value:
            return value, env_name
    return None, None


def ensure_openrouter_api_key(provider: str | None) -> str | None:
    """Validate OpenRouter credentials when the selected provider is OpenRouter."""
    if str(provider or "").strip().lower() != "openrouter":
        return None

    value, _source = resolve_openrouter_api_key()
    if value:
        return value

    raise RuntimeError(
        "OpenRouter API key not configured. Set OPENROUTER_API_KEY or LLM_API_KEY."
    )


def apply_openrouter_env(provider: str | None, env: dict[str, str]) -> None:
    """Mirror the OpenRouter API key into both common env var names for child processes."""
    value = ensure_openrouter_api_key(provider)
    if not value:
        return

    env.setdefault("OPENROUTER_API_KEY", value)
    env.setdefault("LLM_API_KEY", value)
