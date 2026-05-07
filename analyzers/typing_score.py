from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class AnalysisResult:
    score: int
    points: int
    comment: str
    wpm: int | None
    accuracy: int | None


def analyze_typing(content: str) -> AnalysisResult:
    wpm_match = re.search(r"wpm\s*[:：]\s*(\d+)", content, flags=re.IGNORECASE)
    acc_match = re.search(r"accuracy\s*[:：]\s*(\d+)\s*%?", content, flags=re.IGNORECASE)

    wpm = int(wpm_match.group(1)) if wpm_match else None
    acc = int(acc_match.group(1)) if acc_match else None

    if wpm is None or acc is None:
        return AnalysisResult(
            score=1,
            points=5,
            comment="`WPM: 95` と `Accuracy: 98%` の形式で投稿してください。",
            wpm=wpm,
            accuracy=acc,
        )

    score = 1
    if wpm >= 100:
        score += 5
    elif wpm >= 80:
        score += 4
    elif wpm >= 60:
        score += 3
    elif wpm >= 40:
        score += 2
    else:
        score += 1

    if acc >= 98:
        score += 4
    elif acc >= 95:
        score += 3
    elif acc >= 90:
        score += 2
    else:
        score += 1

    score = min(10, score)
    points = score * 9
    comment = "高精度タイピングです。実務効率アップに直結します。" if score >= 8 else "ナイス練習。精度95%以上を目標に継続しましょう。"
    return AnalysisResult(score=score, points=points, comment=comment, wpm=wpm, accuracy=acc)
