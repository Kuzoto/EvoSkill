"""Continue an eval: keep the questions earlier runs answered, rerun the rest.

`evoskill eval` normally runs every question. With ``EVOSKILL_EVAL_CONTINUE`` set to
one or more earlier trace directories (os.pathsep-separated; each is an
``EVOSKILL_TRACE_DIR`` holding ``batch-*/<index>_<hash>.json`` files), a question is
reused when any of them holds an *answered* record for it (non-empty final answer,
no provider/API error) and rerun otherwise, whatever the reason it has no answer:
harness error, timeout, empty answer, or never reached because the job died.
Answered questions are never rerun, right or wrong.

Reused records are copied into the current batch directory (marked ``reused_from``)
so the new trace directory is a complete record of the split.

Every trace directory also gets a ``run_meta.json`` describing the setup. Reusing a
directory whose setup differs (model, skill delivery, skills, skill discovery, tools,
split, questions, timeout) is refused, so answers from different conditions are never
mixed. Directories written before run_meta.json existed are reused with a warning.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

CONTINUE_ENV = "EVOSKILL_EVAL_CONTINUE"
META_NAME = "run_meta.json"
# Setup fields that must match for answers to be reused.
COMPARED = ("model", "sdk", "skill_mode", "skills_sha", "skill_discovery", "disabled_tools",
            "split", "dataset_path", "questions_sha", "timeout_seconds")


def continue_dirs() -> list[Path]:
    """Earlier trace dirs named by EVOSKILL_EVAL_CONTINUE, oldest first."""
    raw = os.environ.get(CONTINUE_ENV, "").strip()
    if not raw:
        return []
    dirs = []
    for part in raw.split(os.pathsep):
        if not part.strip():
            continue
        p = Path(part.strip())
        if not p.is_dir():
            raise SystemExit(f"{CONTINUE_ENV}: {p} is not a directory")
        dirs.append(p)
    # Later runs win when several answered the same question.
    return sorted(dirs, key=lambda p: p.stat().st_mtime)


def _dir_sha(root: Path) -> str:
    h = hashlib.sha256()
    if root.is_dir():
        for p in sorted(root.rglob("*")):
            if p.is_file() and ".git" not in p.parts:
                h.update(str(p.relative_to(root)).encode())
                h.update(p.read_bytes())
    return h.hexdigest()[:16]


def run_meta(cfg: Any, split: str, questions: list[str]) -> dict[str, Any]:
    """What determines a question's outcome, apart from the question itself."""
    from src.harness.skill_mode import cache_tag

    if os.environ.get("OPENCODE_DISABLE_CLAUDE_CODE_SKILLS"):
        discovery = "none"
    elif os.environ.get("OPENCODE_TEST_HOME"):
        discovery = "project"
    else:
        discovery = "all"
    return {
        "model": str(cfg.harness.model),
        "sdk": str(cfg.harness.name),
        "skill_mode": cache_tag(cfg.project_root),
        "skills_sha": _dir_sha(Path(cfg.project_root) / ".claude" / "skills"),
        "skill_discovery": discovery,
        "disabled_tools": os.environ.get("EVOSKILL_DISABLE_TOOLS", ""),
        "split": split,
        "dataset_path": str(cfg.dataset_path),
        "questions_sha": hashlib.sha256("\n".join(questions).encode()).hexdigest()[:16],
        "n_questions": len(questions),
        "timeout_seconds": cfg.harness.timeout_seconds,
    }


def write_meta(meta: dict[str, Any]) -> None:
    from src.evaluation.trace_export import trace_dir

    d = trace_dir()
    if d is not None:
        d.mkdir(parents=True, exist_ok=True)
        (d / META_NAME).write_text(json.dumps(meta, indent=2) + "\n")


def is_answered(rec: dict[str, Any]) -> bool:
    if "answered" in rec:
        return bool(rec["answered"])
    return (not rec.get("failed") and bool(str(rec.get("final_answer") or "").strip())
            and not rec.get("api_error"))


def load_previous(dirs: list[Path], meta: dict[str, Any]) -> tuple[dict[str, tuple[dict, Path]], list[str]]:
    """question -> (answered record, its file), and warnings to print.

    Raises SystemExit if a directory was run with a different setup.
    """
    answered: dict[str, tuple[dict, Path]] = {}
    warnings: list[str] = []
    for d in dirs:
        m = d / META_NAME
        if m.is_file():
            old = json.loads(m.read_text())
            diff = [k for k in COMPARED if old.get(k) != meta.get(k)]
            if diff:
                lines = "\n".join(f"    {k}: {old.get(k)!r} (earlier) vs {meta.get(k)!r} (now)" for k in diff)
                raise SystemExit(f"{CONTINUE_ENV}: {d} was run with a different setup; "
                                 f"not reusing its answers:\n{lines}")
        else:
            warnings.append(f"{d} has no {META_NAME} (written before continue existed); "
                            "assuming the same setup")
        for f in sorted(d.glob("batch-*/*.json")):
            try:
                rec = json.loads(f.read_text())
            except Exception:
                continue
            if isinstance(rec, dict) and "question" in rec and is_answered(rec):
                answered[rec["question"]] = (rec, f)
    return answered, warnings


def copy_reused(reused: dict[int, tuple[dict, Path]]) -> None:
    """Write reused records into the current batch dir under their current index."""
    from src.evaluation.trace_export import current_batch_dir

    d = current_batch_dir()
    if d is None:
        return
    for index, (rec, src) in reused.items():
        rec = dict(rec, index=index, batch=d.name, reused_from=str(src))
        qhash = hashlib.sha256(rec["question"].encode("utf-8")).hexdigest()[:12]
        (d / f"{index:04d}_{qhash}.json").write_text(json.dumps(rec, indent=2, default=str))
