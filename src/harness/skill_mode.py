"""How active skills reach the inference agent.

Two ways to put a skill in front of the model, mirroring the split in the
literature:

``tool``    The agent is given a ``Skill`` tool and must decide to call it.
            EvoSkill's original behaviour. Whether the model actually triggers
            the right skill is then part of what is being measured — and open
            models frequently do not.

``inject``  The full text of every active skill is placed in the system prompt,
            so it is unconditionally in context. This is what SkillOpt does with
            its single skill, and what WikiSkill does with its active skill set:
            "the full content of active skills is injected directly into the
            Inference Agent's system prompt … thereby eliminating skill
            triggering or retrieval failures as confounding variables". The
            ``Skill`` tool is withdrawn so retrieval cannot happen twice.

``both``    Inject the text *and* keep the tool. Useful only for diagnostics —
            it confounds the two mechanisms, so avoid it for headline numbers.

``tree``    SkillTree: the flat ``Skill`` tool is withdrawn and the agent gets a
            ``skilltree`` tool over a hierarchical library instead (embedding search
            over the top layers, model-driven traversal below). The tool itself is an
            opencode custom tool installed into the run by SkillTree's
            ``scripts/evoskill_new_run.sh``; the library is $SKILLTREE_PATH
            (default ``<project>/.skilltree``), not ``.claude/skills``.

Set globally (like ``set_sdk``) from the ``[harness] skill_mode`` config key, or
via the ``EVOSKILL_SKILL_MODE`` environment variable, which wins so a single run
can be flipped without editing config.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

SkillMode = Literal["tool", "inject", "both", "tree"]

_VALID_MODES = ("tool", "inject", "both", "tree")
_current_mode: SkillMode = "tool"

# Skills excluded from injection by default. skill-creator is a meta-skill for
# *authoring* skills (~4.4k tokens); putting it in the inference agent's prompt
# adds cost and distraction without helping it answer the question. Override
# with EVOSKILL_SKILL_INJECT_EXCLUDE (comma-separated, "" to exclude nothing).
_DEFAULT_EXCLUDE = ("skill-creator",)


def inject_exclusions() -> set[str]:
    raw = os.environ.get("EVOSKILL_SKILL_INJECT_EXCLUDE")
    if raw is None:
        return set(_DEFAULT_EXCLUDE)
    return {x.strip() for x in raw.split(",") if x.strip()}


def set_skill_mode(mode: str | None) -> None:
    """Set how skills are exposed. ``None``/empty keeps the default."""
    global _current_mode
    if mode is None or not str(mode).strip():
        return
    mode = str(mode).strip().lower()
    if mode not in _VALID_MODES:
        raise ValueError(
            f"Invalid skill_mode: {mode!r}. Must be one of: "
            f"{', '.join(repr(m) for m in _VALID_MODES)}"
        )
    _current_mode = mode  # type: ignore[assignment]


def get_skill_mode() -> SkillMode:
    """Current mode; EVOSKILL_SKILL_MODE overrides the configured value."""
    env = (os.environ.get("EVOSKILL_SKILL_MODE") or "").strip().lower()
    if env in _VALID_MODES:
        return env  # type: ignore[return-value]
    return _current_mode


def injects_skills() -> bool:
    return get_skill_mode() in ("inject", "both")


def exposes_skill_tool() -> bool:
    return get_skill_mode() in ("tool", "both")


def exposes_skilltree_tool() -> bool:
    return get_skill_mode() == "tree"


def skilltree_path(project_root: str | Path | None = None) -> Path:
    from .utils import resolve_project_root

    env = os.environ.get("SKILLTREE_PATH")
    return Path(env) if env else resolve_project_root(project_root) / ".skilltree"


def cache_tag(project_root: str | Path | None = None) -> str:
    """Part of the eval cache key that the git tree hash does not cover.

    Skill delivery changes the agent's prompt, not the files the tree hash covers,
    so "tool" and "inject" runs over the same skills would otherwise share cache
    entries. In tree mode the library lives outside .claude/skills entirely, so the
    key also carries a hash of the tree and the knobs that change what the tool returns.
    """
    mode = get_skill_mode()
    if mode != "tree":
        return f"skill_mode={mode}"
    import hashlib

    root = skilltree_path(project_root)
    h = hashlib.sha256()
    if root.is_dir():
        for p in sorted(root.rglob("*")):
            if p.is_file() and ".git" not in p.parts:
                h.update(str(p.relative_to(root)).encode())
                h.update(p.read_bytes())
    for knob in ("SKILLTREE_EMBED_DEPTH", "SKILLTREE_TOP_K", "SKILLTREE_EMBED_MODEL", "SKILLTREE_NAMES",
                 "SKILLTREE_MIN_SCORE"):
        h.update(f"{knob}={os.environ.get(knob, '')}".encode())
    # The rendered tool description is part of the prompt: a reworded description
    # must not reuse answers cached under the old one.
    from .utils import resolve_project_root

    desc = resolve_project_root(project_root) / ".opencode" / "skilltree-description.txt"
    if desc.is_file():
        h.update(desc.read_bytes())
    return f"skill_mode=tree:{h.hexdigest()[:16]}"


def load_active_skills(project_root: str | Path | None = None) -> list[tuple[str, str]]:
    """Read every active skill as (name, SKILL.md text), sorted by name.

    Active = present in .claude/skills/ on the checked-out program branch, the
    same definition the loop's _get_active_skills uses.
    """
    from .utils import resolve_project_root

    root = resolve_project_root(project_root)
    skills_dir = root / ".claude" / "skills"
    out: list[tuple[str, str]] = []
    if not skills_dir.is_dir():
        return out
    excluded = inject_exclusions()
    for d in sorted(skills_dir.iterdir()):
        if d.name in excluded:
            continue
        md = d / "SKILL.md"
        if d.is_dir() and md.is_file():
            try:
                text = md.read_text(encoding="utf-8").strip()
            except Exception:
                continue
            if text:
                out.append((d.name, text))
    return out


def build_skill_section(skills: list[tuple[str, str]]) -> str:
    """Render skills as a system-prompt section. Empty string if there are none."""
    if not skills:
        return ""
    parts = [
        "\n\n## Active Skills\n"
        "The following skills are ALREADY ACTIVE and their full instructions are "
        "reproduced below. Apply every skill relevant to the question directly — "
        "do not look them up, and do not call any tool to retrieve them.\n"
    ]
    for name, text in skills:
        parts.append(f"\n<skill name=\"{name}\">\n{text}\n</skill>\n")
    return "".join(parts)
