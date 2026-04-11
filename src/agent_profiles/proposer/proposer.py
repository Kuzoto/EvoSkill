from __future__ import annotations

from typing import Any

from src.harness import build_claudecode_options, build_opencode_options, is_claude_sdk
from src.schemas import ProposerResponse
from src.agent_profiles.proposer.prompt import PROPOSER_SYSTEM_PROMPT


PROPOSER_TOOLS = [
    "Read",
    "Bash",
    "Glob",
    "Grep",
    "WebFetch",
    "WebSearch",
    "TodoWrite",
    "BashOutput",
]


def get_proposer_options(
    model: str | None = None,
    project_root: str | None = None,
) -> Any:
    if is_claude_sdk():
        return build_claudecode_options(
            system=PROPOSER_SYSTEM_PROMPT.strip(),
            schema=ProposerResponse.model_json_schema(),
            tools=PROPOSER_TOOLS,
            project_root=project_root,
            model=model,
        )
    return build_opencode_options(
        system=PROPOSER_SYSTEM_PROMPT.strip(),
        schema=ProposerResponse.model_json_schema(),
        tools=PROPOSER_TOOLS,
        project_root=project_root,
        model=model,
    )


proposer_options = get_proposer_options()
