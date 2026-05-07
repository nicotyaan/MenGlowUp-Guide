# 男磨きコミュニティBot 使い方ガイド

筋トレ・食事・睡眠・タイピング報告をポイント化し、ランキングで競えるDiscord Botです。  
このリポジトリには、機密情報を除いた実装コードも含めています。

## 招待リンク

管理者が発行した招待リンクからサーバーに参加してください。  
必要権限: `applications.commands` / `Send Messages` / `Embed Links` / `Read Message History` / `Manage Roles`

## 報告チャンネル

- `#筋トレ報告`
- `#食事報告`
- `#睡眠報告`
- `#タイピング報告`

## 投稿フォーマット例

### 筋トレ報告

ベンチプレス80kg 5x5  
スクワット100kg 3x5  
ランニング20分

### 食事報告

朝: オートミール、卵、プロテイン  
昼: 鶏むね肉、玄米、サラダ  
夜: 魚、味噌汁、野菜

### 睡眠報告

7.5時間  
または  
7時間30分

### タイピング報告（必須）

WPM: 92  
Accuracy: 98%

## コマンド一覧

- `/ranking`
- `/workoutrank`
- `/typingrank`
- `/sleeprank`
- `/weeklyrank`
- `/mypoint`
- `/streak`

## ルール

- 同じカテゴリは1日1回までポイント加算
- 毎日継続でstreak加算
- 7日 / 30日 / 100日でボーナス
- ポイントに応じて自動ロール付与
- `#筋トレ報告` / `#食事報告` / `#睡眠報告` は、内容がカテゴリと無関係（睡眠は睡眠時間が解析できない）だと **Botは無反応**（返信なし・ポイント加算なし）

## 実装コードについて

- `bot.py`、`cogs/`、`analyzers/`、`services/`、`utils/` を公開
- `requirements.txt`、`render.yaml`、`.env.example` を公開
- `.env`、`data/bot.db`、トークン/キーは公開しない（`.gitignore`で除外）
