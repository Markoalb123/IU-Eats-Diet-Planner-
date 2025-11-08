"""Preprocess collected preferences for downstream pipeline steps."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict

from app.config import load_config
from pipeline.input_collection import UserInput


class PreprocessingError(Exception):
    """Raised when preprocessing fails."""


def preprocess_user_input(user_input: UserInput) -> Dict[str, Path]:
    """Persist user input into structured CSV files.

    Returns a mapping with paths to the generated CSV artifacts.
    """
    config = load_config()
    output_dir = _ensure_output_dir(config)

    available_items_path = output_dir / "available_items.csv"
    goals_path = output_dir / "weekly_preferences.csv"

    _write_available_items_csv(available_items_path, user_input)
    _write_weekly_preferences_csv(goals_path, user_input)

    return {
        "available_items": available_items_path,
        "weekly_preferences": goals_path,
    }


def _ensure_output_dir(config) -> Path:
    """Ensure preprocessing output directory exists."""
    data_root = Path(config.get("preprocessing_output", "./data/preprocessing"))
    data_root.mkdir(parents=True, exist_ok=True)
    return data_root


def _write_available_items_csv(path: Path, user_input: UserInput) -> None:
    """Write available pantry items to a CSV file with a single column."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["available_food"])
        for item in user_input.available_items:
            writer.writerow([item])


def _write_weekly_preferences_csv(path: Path, user_input: UserInput) -> None:
    """Write weekly goal and diet information to a CSV file."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["goal", "diet"],
        )
        writer.writeheader()
        writer.writerow(
            {
                "goal": user_input.weekly_goal,
                "diet": _compile_diet_description(user_input),
            }
        )


def _compile_diet_description(user_input: UserInput) -> str:
    """Convert diet selection into a human-readable description."""
    if user_input.custom_diet_description:
        return user_input.custom_diet_description
    return user_input.diet_choice
