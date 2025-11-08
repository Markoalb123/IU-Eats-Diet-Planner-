"""Persistence utilities for storing generated diet plans."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Mapping, Dict, Any

from app.config import load_config


def store_plan_in_dashboard(plan_rows: Iterable[Mapping[str, str]]) -> Path:
    """Persist sanitized plan rows into the dashboard SQLite database."""
    config = load_config()
    db_path = Path(config["dashboard_db"])
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    try:
        _ensure_schema(connection)
        _replace_plan(connection, plan_rows)
    finally:
        connection.close()

    return db_path


def append_plan_history(
    plan_rows: Iterable[Mapping[str, str]],
    weekly_goal: str,
    diet_descriptor: str,
) -> Path:
    """Append a historical snapshot of the generated plan."""
    config = load_config()
    db_path = Path(config["dashboard_db"])
    db_path.parent.mkdir(parents=True, exist_ok=True)

    payload = list(plan_rows)
    timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    connection = sqlite3.connect(db_path)
    try:
        _ensure_schema(connection)
        with connection:
            connection.execute(
                """
                INSERT INTO plan_history (created_at, weekly_goal, diet_descriptor, plan_json)
                VALUES (?, ?, ?, ?)
                """,
                (
                    timestamp,
                    weekly_goal,
                    diet_descriptor,
                    json.dumps(payload, ensure_ascii=False),
                ),
            )
    finally:
        connection.close()

    return db_path


def fetch_plan_history(limit: int = 20) -> List[Dict[str, Any]]:
    """Return recent historical plans ordered from newest to oldest."""
    config = load_config()
    db_path = Path(config["dashboard_db"])
    if not db_path.exists():
        return []

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        _ensure_schema(connection)
        cursor = connection.execute(
            """
            SELECT id, created_at, weekly_goal, diet_descriptor, plan_json
            FROM plan_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        history: List[Dict[str, Any]] = []
        for row in cursor.fetchall():
            try:
                plan = json.loads(row["plan_json"] or "[]")
            except json.JSONDecodeError:
                plan = []
            history.append(
                {
                    "id": row["id"],
                    "created_at": row["created_at"],
                    "weekly_goal": row["weekly_goal"],
                    "diet_descriptor": row["diet_descriptor"],
                    "plan": plan,
                }
            )
        return history
    finally:
        connection.close()


def _ensure_schema(connection: sqlite3.Connection) -> None:
    with connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS meal_plan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                day TEXT NOT NULL UNIQUE,
                meal TEXT NOT NULL,
                rationale TEXT NOT NULL,
                recipe TEXT NOT NULL,
                nutritional_value TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS plan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                weekly_goal TEXT,
                diet_descriptor TEXT,
                plan_json TEXT NOT NULL
            )
            """
        )


def _replace_plan(connection: sqlite3.Connection, plan_rows: Iterable[Mapping[str, str]]) -> None:
    payload = list(plan_rows)
    with connection:
        connection.execute("DELETE FROM meal_plan")
        connection.executemany(
            """
            INSERT INTO meal_plan (day, meal, rationale, recipe, nutritional_value)
            VALUES (:day, :meal, :rationale, :recipe, :nutritional_value)
            """,
            payload,
        )
