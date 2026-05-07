import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


@dataclass
class UserPoints:
    user_id: int
    total_points: int
    workout_points: int
    food_points: int
    sleep_points: int
    typing_points: int
    streak_days: int
    last_report_date: str | None
    streak_bonus_claimed: int


class Database:
    def __init__(self, db_path: str = "data/bot.db") -> None:
        Path("data").mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                total_points INTEGER NOT NULL DEFAULT 0,
                workout_points INTEGER NOT NULL DEFAULT 0,
                food_points INTEGER NOT NULL DEFAULT 0,
                sleep_points INTEGER NOT NULL DEFAULT 0,
                typing_points INTEGER NOT NULL DEFAULT 0,
                streak_days INTEGER NOT NULL DEFAULT 0,
                last_report_date TEXT,
                streak_bonus_claimed INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_reports (
                user_id INTEGER NOT NULL,
                report_date TEXT NOT NULL,
                category TEXT NOT NULL,
                PRIMARY KEY (user_id, report_date, category)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS report_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                points INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def get_or_create_user(self, user_id: int) -> UserPoints:
        cur = self.conn.cursor()
        cur.execute("INSERT OR IGNORE INTO users(user_id) VALUES (?)", (user_id,))
        self.conn.commit()
        cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return UserPoints(**dict(cur.fetchone()))

    def update_user_points(self, user_id: int, category: str, gained_points: int) -> UserPoints:
        column_map = {"workout": "workout_points", "food": "food_points", "sleep": "sleep_points", "typing": "typing_points"}
        category_col = column_map[category]
        cur = self.conn.cursor()
        cur.execute("INSERT OR IGNORE INTO users(user_id) VALUES (?)", (user_id,))
        cur.execute(
            f"UPDATE users SET total_points = total_points + ?, {category_col} = {category_col} + ? WHERE user_id = ?",
            (gained_points, gained_points, user_id),
        )
        self.conn.commit()
        return self.get_or_create_user(user_id)

    def set_streak(self, user_id: int, streak_days: int, report_date: str) -> None:
        cur = self.conn.cursor()
        cur.execute("INSERT OR IGNORE INTO users(user_id) VALUES (?)", (user_id,))
        cur.execute("UPDATE users SET streak_days = ?, last_report_date = ? WHERE user_id = ?", (streak_days, report_date, user_id))
        self.conn.commit()

    def add_bonus(self, user_id: int, bonus_points: int, bonus_bit: int) -> UserPoints:
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE users SET total_points = total_points + ?, streak_bonus_claimed = streak_bonus_claimed | ? WHERE user_id = ?",
            (bonus_points, bonus_bit, user_id),
        )
        self.conn.commit()
        return self.get_or_create_user(user_id)

    def has_claimed_bonus(self, user_id: int, bonus_bit: int) -> bool:
        user = self.get_or_create_user(user_id)
        return (user.streak_bonus_claimed & bonus_bit) == bonus_bit

    def add_daily_report(self, user_id: int, report_date: str, category: str) -> bool:
        cur = self.conn.cursor()
        try:
            cur.execute("INSERT INTO daily_reports(user_id, report_date, category) VALUES (?, ?, ?)", (user_id, report_date, category))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_top_users(self, category: str = "total_points", limit: int = 10) -> list[sqlite3.Row]:
        cur = self.conn.cursor()
        cur.execute(f"SELECT * FROM users ORDER BY {category} DESC, user_id ASC LIMIT ?", (limit,))
        return list(cur.fetchall())

    def add_report_log(self, user_id: int, category: str, points: int) -> None:
        created_at = datetime.now(timezone.utc).isoformat()
        self.conn.execute("INSERT INTO report_logs(user_id, category, points, created_at) VALUES (?, ?, ?, ?)", (user_id, category, points, created_at))
        self.conn.commit()

    def get_user_rank(self, user_id: int, category: str = "total_points") -> int:
        cur = self.conn.cursor()
        cur.execute(
            f"SELECT 1 + COUNT(*) AS rank FROM users WHERE {category} > (SELECT {category} FROM users WHERE user_id = ?)",
            (user_id,),
        )
        row = cur.fetchone()
        return int(row["rank"]) if row else 1

    def get_weekly_ranking(self, limit: int = 10) -> list[sqlite3.Row]:
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        cur = self.conn.cursor()
        cur.execute(
            "SELECT user_id, SUM(points) AS weekly_points FROM report_logs WHERE created_at >= ? GROUP BY user_id ORDER BY weekly_points DESC, user_id ASC LIMIT ?",
            (since, limit),
        )
        return list(cur.fetchall())

    def raw_user_dict(self, user_id: int) -> dict[str, Any]:
        return dict(self.get_or_create_user(user_id).__dict__)
