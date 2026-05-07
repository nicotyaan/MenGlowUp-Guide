from __future__ import annotations

import json
import os
from dataclasses import dataclass

import httpx


@dataclass
class AnalysisResult:
    score: int
    points: int
    comment: str
    source: str


def _fallback_food(content: str) -> AnalysisResult:
    text = content.lower()
    good = ["鶏むね", "魚", "卵", "野菜", "サラダ", "豆腐", "納豆", "玄米", "オートミール", "protein"]
    bad = ["揚げ", "ラーメン", "菓子", "ジュース", "爆食", "深夜", "アルコール", "fried", "soda"]
    score = 5
    score += min(3, sum(1 for g in good if g in text))
    score -= min(3, sum(1 for b in bad if b in text))
    score = max(1, min(10, score))
    comment = "たんぱく質と野菜を意識するとさらに良くなります。"
    if score >= 8:
        comment = "高品質な食事内容です。継続すれば体づくりが加速します。"
    elif score <= 4:
        comment = "脂質・糖質過多の可能性があります。次回はたんぱく質を増やしましょう。"
    return AnalysisResult(score=score, points=score * 9, comment=comment, source="rule")


async def analyze_food(content: str) -> AnalysisResult:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return _fallback_food(content)

    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    prompt = (
        "次の食事報告を健康観点で1-10点評価し、短い改善コメントを返してください。"
        "JSONのみ返す: {\"score\": int, \"comment\": string}。"
        f"\n食事報告:\n{content[:700]}"
    )

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "あなたは栄養バランスを評価するコーチです。"},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 120,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            parsed = json.loads(text)
            score = max(1, min(10, int(parsed["score"])))
            comment = str(parsed["comment"])[:180]
            return AnalysisResult(score=score, points=score * 9, comment=comment, source="llm")
    except Exception:
        return _fallback_food(content)
