from __future__ import annotations

import sys
import tomllib
import types
from pathlib import Path

import pytest


def _write_project(tmp_path: Path, config_text: str) -> Path:
    project_root = tmp_path / "project"
    evoskill_dir = project_root / ".evoskill"
    evoskill_dir.mkdir(parents=True)
    (evoskill_dir / "config.toml").write_text(config_text)
    (evoskill_dir / "task.md").write_text("# Task\n\nAnswer questions.\n\n---\n\n# Constraints\n\n- no web\n")
    return project_root


@pytest.mark.parametrize(
    ("harness", "expected"),
    [
        ("claude", "anthropic/claude-sonnet-4-6"),
        ("opencode", "anthropic/claude-sonnet-4-6"),
        ("goose", "anthropic/claude-sonnet-4-6"),
        ("openhands", "anthropic/claude-sonnet-4-6"),
        ("codex", "codex-mini-latest"),
    ],
)
def test_default_model_for_harness(harness: str, expected: str) -> None:
    from src.harness.model_aliases import default_model_for_harness

    assert default_model_for_harness(harness) == expected


@pytest.mark.parametrize("harness", ["claude", "opencode", "goose", "openhands"])
def test_load_config_normalizes_legacy_sonnet_model(tmp_path: Path, harness: str) -> None:
    from src.cli.config import load_config

    project_root = _write_project(
        tmp_path,
        f'[harness]\nname = "{harness}"\nmodel = "sonnet"\n',
    )

    cfg = load_config(project_root)

    assert cfg.harness.model == "anthropic/claude-sonnet-4-6"


@pytest.mark.parametrize(
    ("harness", "expected"),
    [
        ("claude", "anthropic/claude-sonnet-4-6"),
        ("goose", "anthropic/claude-sonnet-4-6"),
        ("codex", "codex-mini-latest"),
    ],
)
def test_load_config_applies_harness_default_when_model_missing(
    tmp_path: Path,
    harness: str,
    expected: str,
) -> None:
    from src.cli.config import load_config

    project_root = _write_project(
        tmp_path,
        f'[harness]\nname = "{harness}"\n',
    )

    cfg = load_config(project_root)

    assert cfg.harness.model == expected


def test_load_config_reads_timeout_and_retry_settings(tmp_path: Path) -> None:
    from src.cli.config import load_config

    project_root = _write_project(
        tmp_path,
        (
            '[harness]\n'
            'name = "codex"\n'
            'timeout_seconds = 42\n'
            'max_retries = 1\n'
        ),
    )

    cfg = load_config(project_root)

    assert cfg.harness.timeout_seconds == 42
    assert cfg.harness.max_retries == 1


def test_load_config_applies_timeout_and_retry_defaults(tmp_path: Path) -> None:
    from src.cli.config import load_config

    project_root = _write_project(
        tmp_path,
        '[harness]\nname = "claude"\n',
    )

    cfg = load_config(project_root)

    assert cfg.harness.timeout_seconds == 1200
    assert cfg.harness.max_retries == 3


def test_init_write_config_uses_harness_default_model(tmp_path: Path) -> None:
    from src.cli.commands.init import _write_config

    config_path = tmp_path / "config.toml"
    _write_config(
        config_path,
        {
            "harness": "codex",
            "dataset_path": "./data/questions.csv",
            "question_col": "question",
            "gt_col": "answer",
            "category_col": "difficulty",
            "data_dirs": ["./docs"],
        },
    )

    rendered = config_path.read_text()
    with open(config_path, "rb") as f:
        raw = tomllib.load(f)

    assert raw["harness"]["name"] == "codex"
    assert raw["harness"]["model"] == "codex-mini-latest"
    assert raw["harness"]["data_dirs"] == ["./docs"]
    assert raw["harness"]["timeout_seconds"] == 1200
    assert raw["harness"]["max_retries"] == 3
    assert raw["evolution"]["mode"] == "skill_only"
    assert raw["dataset"]["ground_truth_column"] == "answer"
    assert raw["dataset"]["category_column"] == "difficulty"
    assert "# Agent runtime used to execute EvoSkill runs." in rendered
    assert "# Additional folders the agent can interact with during runs." in rendered
    assert "# What EvoSkill is allowed to optimize: skills or the base prompt." in rendered
    assert "# CSV column containing the expected answer." in rendered
    assert "# Scoring rule used to compare predictions against ground truth." in rendered


def test_init_prompt_defaults_keep_existing_category_column(tmp_path: Path) -> None:
    from src.cli.commands.init import _load_prompt_defaults

    config_path = tmp_path / "config.toml"
    config_path.write_text(
        (
            "[harness]\n"
            'name = "goose"\n'
            'data_dirs = ["docs"]\n'
            "\n"
            "[dataset]\n"
            'path = "./data/input.csv"\n'
            'question_column = "prompt"\n'
            'ground_truth_column = "answer"\n'
            'category_column = "difficulty"\n'
        )
    )

    defaults = _load_prompt_defaults(config_path)

    assert defaults["harness"] == "goose"
    assert defaults["dataset_path"] == "./data/input.csv"
    assert defaults["question_col"] == "prompt"
    assert defaults["gt_col"] == "answer"
    assert defaults["category_col"] == "difficulty"
    assert defaults["data_dirs_raw"] == "docs"


def test_build_claudecode_options_strips_anthropic_prefix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.harness.claude.options import build_claudecode_options

    class FakeClaudeAgentOptions:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.model = None

    fake_module = types.SimpleNamespace(ClaudeAgentOptions=FakeClaudeAgentOptions)
    monkeypatch.setitem(sys.modules, "claude_agent_sdk", fake_module)

    options = build_claudecode_options(
        system="system",
        schema={"type": "object"},
        tools=["Read"],
        project_root=tmp_path,
        model="anthropic/claude-sonnet-4-6",
    )

    assert options.model == "claude-sonnet-4-6"
