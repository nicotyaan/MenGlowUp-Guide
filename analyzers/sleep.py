from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class AnalysisResult:
    score: int
    points: int
    comment: str
    hours: float | None


def _parse_sleep_hours(content: str) -> float | None:
    text = content.lower().strip()
    m = re.search(r"(\d+(?:\.\d+)?)\s?(?:h|時間)", text)
    if m:
        return float(m.group(1))
    m2 = re.search(r"(\d{1,2})時間\s?(\d{1,2})分", text)
    if m2:
        hours = int(m2.group(1))
        mins = int(m2.group(2))
        return hours + mins / 60
    return None


def is_sleep_report(content: str) -> bool:
    return _parse_sleep_hours(content) is not None


def analyze_sleep(content: str) -> AnalysisResult:
    hours = _parse_sleep_hours(content)
    if hours is None:
        return AnalysisResult(
            score=1,
            points=5,
            comment="睡眠時間を `7.5時間` や `7h` の形式で書いてください。",
            hours=None,
        )

    if 7 <= hours <= 9:
        score = 10
        comment = "理想的な睡眠です。回復効率が高い状態です。"
    elif 6 <= hours < 7 or 9 < hours <= 10:
        score = 7
        comment = "良好です。7-9時間に寄せるとさらに安定します。"
    elif 5 <= hours < 6:
        score = 4
        comment = "睡眠不足ぎみです。明日は就寝を30分早めましょう。"
    else:
        score = 3
        comment = "コンディション低下リスクあり。睡眠時間の確保を優先してください。"
    return AnalysisResult(score=score, points=score * 8, comment=comment, hours=hours)
