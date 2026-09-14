"""Opt-in per-question trace export.

Set ``EVOSKILL_TRACE_DIR`` and every evaluated question writes one JSON file
containing the question, ground truth, final answer, metrics and — most
importantly for skill research — which tools the agent actually invoked and
whether any of them was the ``Skill`` tool.

Nothing is written when the variable is unset, so normal runs are unaffected.

Env:
  EVOSKILL_TRACE_DIR       directory to write into (enables the export)
  EVOSKILL_TRACE_MESSAGES  "0" to omit the raw message payload (default: include)
  EVOSKILL_TRACE_MAX_MB    per-file cap for the raw payload (default: 8)

The message payload differs per harness (opencode nests
``[{"messages": [{"info":…, "parts":[…]}]}]``; the Claude SDK yields content
blocks with ``type="tool_use"``; Codex its own events), so tool detection walks
the structure generically rather than assuming one schema.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from pathlib import Path
from typing import Any

# Keys that hold a tool name, in priority order.
_NAME_KEYS = ("tool", "toolName", "tool_name", "name", "function")
# dict["type"] values that mark a tool invocation.
_TOOL_TYPES = {"tool", "tool_use", "tool_call", "tool-call", "function_call", "toolInvocation"}
# Textual fallback: `Skill({"skill": "x"})`, `[Calling tool: Skill]`, <skill>x</skill>
# Argument keys naming the requested skill (opencode uses "name", others "skill").
_SKILL_NAME_KEYS = ("skill", "name", "skill_name")
_TEXT_SKILL_RE = re.compile(
    r"""Skill\s*\(|\[Calling\s+tool:\s*Skill\]|<skill>|"skill"\s*:""",
    re.IGNORECASE | re.VERBOSE,
)


def trace_dir() -> Path | None:
    raw = os.environ.get("EVOSKILL_TRACE_DIR", "").strip()
    return Path(raw) if raw else None


# Each call to evaluate_agent_parallel is one eval batch (the baseline eval, then
# one per loop iteration). Every batch re-asks the SAME questions, so writing
# <index>_<question hash>.json into a single directory made each batch overwrite
# the previous one and only the last survived. Batches therefore get their own
# subdirectory: batch-000 is the baseline, batch-001.. the iterations.
_BATCH_LOCK = threading.Lock()
_BATCH = {"n": -1, "dir": None}


def begin_batch(label: str | None = None) -> Path | None:
    """Start a new eval batch; later dump_trace() calls write into it."""
    d = trace_dir()
    if d is None:
        return None
    with _BATCH_LOCK:
        _BATCH["n"] += 1
        name = f"batch-{_BATCH['n']:03d}" + (f"_{label}" if label else "")
        path = d / name
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception:
            return None
        _BATCH["dir"] = path
        return path


def current_batch_dir() -> Path | None:
    """The active batch dir, creating an implicit first batch if needed."""
    if _BATCH["dir"] is None:
        return begin_batch()
    return _BATCH["dir"]


def _walk(node: Any, depth: int = 0):
    """Yield every dict nested anywhere in the structure."""
    if depth > 25:
        return
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v, depth + 1)
    elif isinstance(node, (list, tuple)):
        for v in node:
            yield from _walk(v, depth + 1)


def _tool_name(d: dict) -> str | None:
    for k in _NAME_KEYS:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
        # OpenAI style: {"function": {"name": ...}}
        if isinstance(v, dict):
            n = v.get("name")
            if isinstance(n, str) and n.strip():
                return n.strip()
    return None


def _skill_arg(d: dict) -> str | None:
    """Best-effort extraction of which skill was requested."""
    # OpenAI style nests the payload one level down: {"function": {"arguments": "..."}}
    fn = d.get("function")
    if isinstance(fn, dict):
        nested = _skill_arg(fn)
        if nested:
            return nested
    for key in ("input", "args", "arguments", "parameters", "state"):
        v = d.get(key)
        if isinstance(v, str):
            try:
                v = json.loads(v)
            except Exception:
                continue
        if isinstance(v, dict):
            for sk in _SKILL_NAME_KEYS:
                s = v.get(sk)
                if isinstance(s, str) and s.strip():
                    return s.strip()
            # opencode wraps it once more: state.input.name
            for nest_key in ("input", "arguments", "args", "parameters"):
                nested = v.get(nest_key)
                if isinstance(nested, str):
                    try:
                        nested = json.loads(nested)
                    except Exception:
                        continue
                if isinstance(nested, dict):
                    for sk in _SKILL_NAME_KEYS:
                        s = nested.get(sk)
                        if isinstance(s, str) and s.strip():
                            return s.strip()
    return None


def _tool_status(d: dict) -> tuple[str | None, str]:
    """(status, message) for a tool invocation, across harness shapes.

    opencode puts it in state.status/state.output; other shapes use a top-level
    status, or an is_error flag on the result block.
    """
    for key in ("state", "result", "toolResult"):
        v = d.get(key)
        if isinstance(v, dict):
            st = v.get("status")
            if isinstance(st, str):
                return st.lower(), str(v.get("output") or v.get("error") or "")[:400]
            if v.get("is_error") is True:
                return "error", str(v.get("content") or v.get("output") or "")[:400]
    st = d.get("status")
    if isinstance(st, str):
        return st.lower(), str(d.get("output") or d.get("error") or "")[:400]
    if d.get("is_error") is True:
        return "error", str(d.get("content") or "")[:400]
    return None, ""


def detect_api_error(messages: Any) -> str | None:
    """Provider/transport error that stopped the question from being answered.

    A rate limit or 400 still yields a trace object, so without this a failed
    question looks 'completed' with an empty answer and silently drags scores
    and skill-invocation rates down. opencode records it as info.error.
    """
    for d in _walk(messages):
        err = d.get("error")
        if isinstance(err, dict) and (err.get("name") or err.get("message")):
            data = err.get("data") if isinstance(err.get("data"), dict) else {}
            msg = str(data.get("message") or err.get("message") or "")[:400]
            return f"{err.get('name') or 'Error'}: {msg}".strip(": ")
    return None


def analyze_tools(messages: Any) -> dict[str, Any]:
    """Extract tool invocations and skill usage from any harness's message payload."""
    tools: list[str] = []
    skill_calls: list[dict[str, Any]] = []
    text_chunks: list[str] = []

    for d in _walk(messages):
        dtype = d.get("type")
        is_tool = (isinstance(dtype, str) and dtype in _TOOL_TYPES) or "toolInvocations" in d
        if is_tool:
            name = _tool_name(d)
            if name:
                tools.append(name)
                if name.lower() == "skill":
                    st, msg = _tool_status(d)
                    skill_calls.append({"tool": name, "skill": _skill_arg(d),
                                        "status": st, "error": msg if st == "error" else ""})
        # OpenAI-style tool_calls list
        for tc in d.get("tool_calls") or []:
            if isinstance(tc, dict):
                name = _tool_name(tc)
                if name:
                    tools.append(name)
                    if name.lower() == "skill":
                        st, msg = _tool_status(tc)
                        skill_calls.append({"tool": name, "skill": _skill_arg(tc),
                                            "status": st, "error": msg if st == "error" else ""})
        if isinstance(dtype, str) and dtype == "text":
            t = d.get("text")
            if isinstance(t, str):
                text_chunks.append(t)

    text_hint = any(_TEXT_SKILL_RE.search(t) for t in text_chunks)
    counts: dict[str, int] = {}
    for t in tools:
        counts[t] = counts.get(t, 0) + 1

    ok_calls = [c for c in skill_calls if c.get("status") != "error"]
    bad_calls = [c for c in skill_calls if c.get("status") == "error"]
    return {
        # attempted: the model tried to call Skill (successfully or not)
        "invoked": bool(skill_calls) or text_hint,
        "via_tool_call": bool(skill_calls),
        "via_text_only": text_hint and not skill_calls,
        # succeeded: the Skill tool actually returned skill content. A call for a
        # skill that does not exist errors out, and must not count as usage.
        "invoked_ok": bool(ok_calls),
        "invoked_failed_only": bool(bad_calls) and not ok_calls,
        "skill_calls": skill_calls,
        "skills_requested": sorted({c["skill"] for c in skill_calls if c.get("skill")}),
        "skills_succeeded": sorted({c["skill"] for c in ok_calls if c.get("skill")}),
        "skills_failed": sorted({c["skill"] for c in bad_calls if c.get("skill")}),
        "tool_counts": counts,
        "total_tool_calls": len(tools),
    }


def _final_answer(trace: Any) -> str:
    out = getattr(trace, "output", None)
    if out is not None:
        for attr in ("final_answer", "answer", "response"):
            v = getattr(out, attr, None)
            if isinstance(v, str):
                return v
    return str(getattr(trace, "result", "") or "")


def dump_trace(
    question: str,
    ground_truth: str,
    trace: Any,
    *,
    index: int | None = None,
    extra: dict[str, Any] | None = None,
) -> Path | None:
    """Write one JSON per evaluated question. No-op unless EVOSKILL_TRACE_DIR is set."""
    d = current_batch_dir()
    if d is None:
        return None

    try:
        d.mkdir(parents=True, exist_ok=True)
        qhash = hashlib.sha256(question.encode("utf-8")).hexdigest()[:12]
        stem = f"{index:04d}_{qhash}" if index is not None else qhash
        path = d / f"{stem}.json"

        messages = getattr(trace, "messages", None) if trace is not None else None
        record: dict[str, Any] = {
            "batch": d.name,
            "index": index,
            "question": question,
            "ground_truth": ground_truth,
            "failed": trace is None,
        }
        if trace is not None:
            record.update({
                "final_answer": _final_answer(trace),
                "model": getattr(trace, "model", ""),
                "session_id": getattr(trace, "session_id", ""),
                "tools_available": list(getattr(trace, "tools", []) or []),
                "num_turns": getattr(trace, "num_turns", 0),
                "duration_ms": getattr(trace, "duration_ms", 0),
                "total_cost_usd": getattr(trace, "total_cost_usd", 0.0),
                "is_error": getattr(trace, "is_error", False),
                "parse_error": getattr(trace, "parse_error", None),
                "skill_usage": analyze_tools(messages),
                "api_error": detect_api_error(messages),
            })
            record["answered"] = bool(record.get("final_answer", "").strip()) and not record["api_error"]
        if extra:
            record.update(extra)

        if messages is not None and os.environ.get("EVOSKILL_TRACE_MESSAGES", "1") != "0":
            try:
                blob = json.dumps(messages, default=str)
                cap = float(os.environ.get("EVOSKILL_TRACE_MAX_MB", "8")) * 1024 * 1024
                record["messages"] = (
                    json.loads(blob) if len(blob) <= cap
                    else {"_truncated": True, "bytes": len(blob), "head": blob[:200_000]}
                )
            except Exception as e:  # never let trace export break an eval
                record["messages_error"] = f"{type(e).__name__}: {e}"

        path.write_text(json.dumps(record, indent=2, default=str))
        return path
    except Exception:
        return None
