"""OpenCode SDK option building and permission management.

All OpenCode-specific construction logic lives here:
    - Tool name mapping (Claude PascalCase → OpenCode lowercase)
    - Model string parsing ("anthropic/claude-sonnet-4-6" → provider + model)
    - Permission auto-config (opencode.json)
    - The build_opencode_options() function
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from ..model_aliases import DEFAULT_ANTHROPIC_MODEL, normalize_harness_model
from ..utils import resolve_project_root, resolve_data_dirs


DEFAULT_OPENCODE_MODEL = DEFAULT_ANTHROPIC_MODEL

CLAUDE_TO_OPENCODE_TOOL = {
    "Read": "read",
    "Write": "write",
    "Bash": "bash",
    "Glob": "glob",
    "Grep": "grep",
    "Edit": "edit",
    "WebFetch": "webfetch",
    "WebSearch": "websearch",
    "TodoWrite": "todowrite",
    "Skill": "skill",
    # OpenCode does not expose a separate BashOutput tool.
    "BashOutput": None,
}


def split_opencode_model(model: str | None) -> tuple[str, str]:
    """Parse 'provider/model' string into (provider_id, model_id)."""
    full = normalize_harness_model("opencode", model)
    if "/" in full:
        return full.split("/", 1)
    return "anthropic", full


def to_opencode_tools(tools: Iterable[str]) -> dict[str, bool]:
    """Map Claude tool names (PascalCase) to OpenCode names (lowercase)."""
    converted: dict[str, bool] = {}
    for tool in tools:
        normalized = CLAUDE_TO_OPENCODE_TOOL.get(tool, tool.lower())
        if normalized is not None:
            converted[normalized] = True
    return converted


def _normalize_permission_block(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, str):
        return {"*": value}
    if isinstance(value, dict):
        return dict(value)
    return {}


def ensure_opencode_project_permissions(
    project_root: str | Path | None,
    data_dirs: Iterable[str] | None = None,
) -> None:
    """Auto-create/update opencode.json to grant file access to data directories."""
    root = resolve_project_root(project_root)
    resolved_add_dirs = resolve_data_dirs(root, data_dirs)
    if not resolved_add_dirs:
        return

    jsonc_path = root / "opencode.jsonc"
    config_path = root / "opencode.json"
    if jsonc_path.exists() and not config_path.exists():
        return

    config: dict[str, Any] = {}
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
        except json.JSONDecodeError:
            return

    config.setdefault("$schema", "https://opencode.ai/config.json")
    permission = _normalize_permission_block(config.get("permission"))
    external_directory = _normalize_permission_block(
        permission.get("external_directory")
    )

    changed = False
    for raw_path in resolved_add_dirs:
        path = str(Path(raw_path).resolve())
        for pattern in (path, f"{path}/**"):
            if external_directory.get(pattern) != "allow":
                external_directory[pattern] = "allow"
                changed = True

    if not changed and config_path.exists():
        return

    permission["external_directory"] = external_directory
    config["permission"] = permission
    config_path.write_text(json.dumps(config, indent=2) + "\n")


def build_opencode_options(
    *,
    system: str,
    schema: dict[str, Any],
    tools: Iterable[str],
    project_root: str | Path | None = None,
    model: str | None = None,
    mode: str = "build",
    data_dirs: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Build an options dict for the OpenCode SDK."""
    root = resolve_project_root(project_root)
    provider_id, model_id = split_opencode_model(model)
    resolved_add_dirs = resolve_data_dirs(root, data_dirs)
    ensure_opencode_project_permissions(root, resolved_add_dirs)

    system_with_dirs = system
    if resolved_add_dirs:
        dirs_note = "\n".join(f"- {path}" for path in resolved_add_dirs)
        system_with_dirs = (
            f"{system.rstrip()}\n\n"
            "Additional accessible data directories are available outside the project root.\n"
            "Use absolute paths when you need to inspect them:\n"
            f"{dirs_note}"
        )

    system_with_dirs += (
        "\n\n"
        "Before answering, use the brainstorming skill to plan your approach."
        "\n\n"
        "## Using Skills\n"
        "You have access to skills via the Skill tool. Skills provide specialized "
        "methodologies and workflows. ALWAYS check available skills and use them "
        "when relevant — they significantly improve accuracy.\n\n"
        "### Example 1: Numeric / counting question\n"
        "User: How many volcanic eruptions in the 21st century have produced a "
        "plume height of at least 18 miles?\n"
        "Assistant thinking: This involves finding and counting items. "
        "Let me check for a numeric or quantitative skill.\n"
        "Assistant action: Skill({\"skill\": \"numeric-fact-answering\", "
        "\"args\": \"How many volcanic eruptions in the 21st century have produced a plume height of at least 18 miles?\"})\n"
        "Result: Skill provides an enumeration/verification methodology. "
        "The assistant systematically enumerates all candidates and cross-checks.\n\n"
        "### Example 2: Fact verification / historical question\n"
        "User: What Formula One car was driven in 1994 by the nephew of a racing "
        "driver from Italy who drove a Ferrari 312T?\n"
        "Assistant thinking: This requires verifying specific historical facts. "
        "Let me check for a fact-verification skill.\n"
        "Assistant action: Skill({\"skill\": \"historical_fact_verification\", "
        "\"args\": \"What Formula One car was driven in 1994 by the nephew of a racing driver from Italy who drove a Ferrari 312T?\"})\n"
        "Result: Skill provides a systematic fact-checking workflow. "
        "The assistant decomposes claims and verifies each one.\n\n"
        "### Example 3: General research question\n"
        "User: Which non-American agency has the most followers on X?\n"
        "Assistant thinking: This requires web research to find current data. "
        "Let me use brainstorming to plan my approach, then search.\n"
        "Assistant action: Skill({\"skill\": \"brainstorming\", "
        "\"args\": \"Which non-American agency has the most followers on X?\"})\n"
        "Result: Skill helps decompose the problem into search steps. "
        "The assistant then executes the research plan.\n\n"
        "### Example 4: Coding question\n"
        "User: [programming problem]\n"
        "Assistant thinking: This requires writing and testing code. "
        "Let me check for a code-testing or stdin-test skill.\n"
        "Assistant action: Skill({\"skill\": \"stdin-test-output\"})\n"
        "Result: Skill provides a test harness workflow. "
        "The assistant writes code, creates tests, and validates before submitting.\n\n"
        "Key pattern: ALWAYS check available skills and invoke the most relevant one "
        "BEFORE starting your work. Match the skill to the question type — "
        "numeric skills for counting/quantities, fact-verification for claims, "
        "brainstorming for research, testing skills for code.\n"
        "\n\n"
        "Web search: Use the built-in websearch tool first. "
        "If it returns a rate limit or 429 error, fall back to the backup search via bash:\n"
        "  python3 scripts/websearch.py \"your query\"\n"
        "This returns a JSON array of {title, url, snippet} results. "
        "Use these URLs with webfetch to get full page content."
    )

    return {
        "system": system_with_dirs,
        "format": {
            "type": "json_schema",
            "schema": schema,
        },
        "tools": to_opencode_tools(tools),
        "mode": mode,
        "provider_id": provider_id,
        "model_id": model_id,
        "cwd": str(root),
        "add_dirs": resolved_add_dirs,
    }
