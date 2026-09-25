"""OfficeQA scorer that grades like SkillOpt's OfficeQA evaluator (its "hard" score).

SkillOpt (skillopt/envs/officeqa/evaluator.py) scores exact match after normalization:
lowercase, drop commas and punctuation (keeping digits, ".", "-", "%"), drop the words
million(s)/billion(s)/dollar(s)/nominal, collapse whitespace. The prediction is the last
<answer>...</answer> block if present, else its last non-empty line
(rollout._extract_answer). No numeric tolerance, unlike multi_tolerance.
"""
from __future__ import annotations

import re
import string

_NUMERIC_CHARS = set("0123456789.-")
_FINAL_RE = re.compile(r"<answer>(.*?)</answer>", re.IGNORECASE | re.DOTALL)


def normalize_answer(text: str) -> str:
    text = text.lower().strip()
    text = text.replace(",", "")
    text = "".join(ch for ch in text if ch not in string.punctuation or ch in _NUMERIC_CHARS or ch == "%")
    text = re.sub(r"\b(million|millions|billion|billions|dollars|dollar|nominal)\b", " ", text)
    return " ".join(text.split())


def extract_answer(text: str) -> str:
    match = _FINAL_RE.search(text)
    if match:
        return match.group(1).strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else text.strip()


def score_officeqa_em(question: str, predicted: str, ground_truth: str) -> float:
    answer = extract_answer(str(predicted or ""))
    if not answer:
        return 0.0
    return float(normalize_answer(answer) == normalize_answer(str(ground_truth)))
