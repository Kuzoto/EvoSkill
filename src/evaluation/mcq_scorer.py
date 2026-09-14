"""Multiple-choice scorer that grades like SkillOpt's LiveMathematicianBench evaluator.

The question carries its options as "## Choices" followed by "A. text" lines (the format
SkillOpt's rollout shows the model), the ground truth is the correct label. The prediction
is parsed the same way SkillOpt does: last <answer>...</answer> block (else last line),
then an exact label, then an exact option text, then the first token.
"""
from __future__ import annotations

import re

_CHOICE_START = re.compile(r"^([A-G])\.\s+(.*)$")


def extract_answer(text: str) -> str:
    matches = re.findall(r"<answer>(.*?)</answer>", text, re.DOTALL | re.IGNORECASE)
    if matches:
        return matches[-1].strip()
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    if lines:
        return lines[-1]
    return text.strip()


def normalize_label(text: str) -> str:
    return str(text).strip().upper().rstrip(".):")


def choices_from_question(question: str) -> list[dict]:
    """Options listed after "## Choices"; a choice's text may span several lines."""
    _, sep, block = str(question).partition("## Choices")
    choices: list[dict] = []
    for line in (block if sep else question).splitlines():
        m = _CHOICE_START.match(line)
        if m:
            choices.append({"label": m.group(1), "text": m.group(2)})
        elif choices and line.strip():
            choices[-1]["text"] += "\n" + line
    for c in choices:
        c["text"] = c["text"].strip()
    return choices


def parse_choice_label(prediction_text: str, choices: list[dict]) -> str:
    answer = extract_answer(prediction_text)
    label = normalize_label(answer)
    valid_labels = {normalize_label(c.get("label", "")) for c in choices}
    if label in valid_labels:
        return label
    answer_lower = answer.lower()
    for c in choices:
        text = str(c.get("text", "")).strip()
        if text and text.lower() == answer_lower:
            return normalize_label(c.get("label", ""))
    first_token = normalize_label(answer.split()[0]) if answer.split() else ""
    if first_token in valid_labels:
        return first_token
    return label


def score_mcq(question: str, predicted: str, ground_truth: str) -> float:
    choices = choices_from_question(question)
    return float(parse_choice_label(str(predicted or ""), choices) == normalize_label(ground_truth))
