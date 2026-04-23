from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from src.harness import Agent, set_sdk
from src.schemas import AgentResponse
from tests.test_openhands_runtime import _install_fake_openhands


@pytest.fixture(autouse=True)
def _reset_sdk() -> None:
    set_sdk("claude")
    yield
    set_sdk("claude")


def test_openhands_runtime_reads_openrouter_api_key_for_openrouter_models(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    set_sdk("openhands")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
    skills_dir = tmp_path / ".claude" / "skills" / "repo-skill"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text("---\nname: repo-skill\ndescription: Repo-local skill\n---\n")

    captured = _install_fake_openhands(
        monkeypatch,
        final_message='{"final_answer":"4","reasoning":"basic arithmetic"}',
    )

    agent = Agent(
        {
            "sdk": "openhands",
            "system": "Answer the question with the final answer only.",
            "format": {
                "type": "json_schema",
                "schema": AgentResponse.model_json_schema(),
            },
            "tools": ["Read", "Edit", "Bash", "TodoWrite", "Skill"],
            "provider_id": "openrouter",
            "model_id": "openai/gpt-5-mini",
            "model": "openrouter/openai/gpt-5-mini",
            "cwd": str(tmp_path),
            "skills_dir": str(tmp_path / ".claude" / "skills"),
            "add_dirs": [],
        },
        AgentResponse,
    )

    trace = asyncio.run(agent.run("What is 2 + 2?"))

    assert trace.output is not None
    assert trace.output.final_answer == "4"
    assert captured["llm_init"]["api_key"].get_secret_value() == "test-openrouter-key"
