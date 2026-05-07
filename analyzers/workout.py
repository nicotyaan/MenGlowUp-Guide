from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class AnalysisResult:
    score: int
    points: int
    comment: str


EXERCISE_KEYWORDS = [
    "ベンチ",
    "スクワット",
    "デッド",
    "懸垂",
    "ランニング",
    "プランク",
    "腕立て",
    "腹筋",
    "bench",
    "squat",
    "deadlift",
    "run",
    "push-up",
]


def is_workout_related(content: str) -> bool:
    text = content.lower()
    if any(kw in text for kw in EXERCISE_KEYWORDS):
        return True
    if re.search(r"(\d{1,3})\s?kg", text):
        return True
    if re.search(r"[x×]\s?(\d{1,2})", text):
        return True
    if re.search(r"(\d{1,3})\s?分", text):
        return True
    return False


def analyze_workout(content: str) -> AnalysisResult:
    text = content.lower()
    exercise_count = sum(1 for kw in EXERCISE_KEYWORDS if kw in text)
    kg_values = [int(v) for v in re.findall(r"(\d{2,3})\s?kg", text)]
    set_matches = [int(v) for v in re.findall(r"[x×]\s?(\d{1,2})", text)]
    cardio_minutes = [int(v) for v in re.findall(r"(\d{1,3})\s?分", text)]

    score = 1
    score += min(3, exercise_count)
    score += 2 if kg_values else 0
    score += 2 if sum(set_matches) >= 10 else (1 if set_matches else 0)
    score += 2 if sum(cardio_minutes) >= 20 else (1 if cardio_minutes else 0)
    score = max(1, min(10, score))

    points = score * 10
    if score >= 8:
        comment = "強度も種目バランスも良いです。継続すれば確実に伸びます。"
    elif score >= 5:
        comment = "良い報告です。種目かセットを少し増やすとさらに高評価です。"
    else:
        comment = "まずは継続を最優先。短時間でも毎日積み上げましょう。"
    return AnalysisResult(score=score, points=points, comment=comment)
