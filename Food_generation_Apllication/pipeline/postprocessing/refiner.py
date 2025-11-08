"""Validate and clean AI-generated meal plans."""
from __future__ import annotations

import csv
import unicodedata
from pathlib import Path
from typing import Dict, List

class PostprocessingError(Exception):
    """Raised when postprocessing fails."""


_REQUIRED_COLUMNS = ["day", "meal", "rationale", "recipe", "nutritional_value"]
_ALLOWED_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


def validate_and_clean_plan(plan_csv: Path) -> List[Dict[str, str]]:
    """Ensure AI output is well-formed and sanitized before rendering."""
    if not plan_csv.exists():
        raise PostprocessingError(f"Plan file does not exist: {plan_csv}")

    cleaned_rows: List[Dict[str, str]] = []
    seen_days = set()

    with plan_csv.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)

        fieldnames = reader.fieldnames or []
        missing_columns = [col for col in _REQUIRED_COLUMNS if col not in fieldnames]
        if missing_columns:
            raise PostprocessingError(
                f"Plan CSV missing required columns: {', '.join(missing_columns)}"
            )

        for row in reader:
            cleaned = {column: _sanitize_text(row.get(column, "")) for column in _REQUIRED_COLUMNS}

            day = _normalize_day(cleaned["day"])
            if day is None:
                raise PostprocessingError(f"Invalid day entry encountered: {cleaned['day']}")
            if day in seen_days:
                raise PostprocessingError(f"Duplicate day detected: {day}")
            seen_days.add(day)
            cleaned["day"] = day

            for column in _REQUIRED_COLUMNS[1:]:
                if not cleaned[column]:
                    raise PostprocessingError(f"Empty value detected for '{column}' on {day}")

            cleaned_rows.append(cleaned)

    if len(cleaned_rows) != len(_ALLOWED_DAYS):
        raise PostprocessingError("Plan must contain exactly five weekday entries.")

    cleaned_rows.sort(key=lambda row: _ALLOWED_DAYS.index(row["day"]))
    return cleaned_rows


def _sanitize_text(value: str) -> str:
    """Trim whitespace and strip control characters that could break rendering."""
    value = value.replace("\r", "")
    filtered = []
    for char in value:
        category = unicodedata.category(char)
        if category in {"Cc", "Cf"} and char not in {"\n", "\t"}:
            continue
        filtered.append(char)
    sanitized = "".join(filtered).strip()
    # collapse excessive whitespace but keep line breaks
    lines = [" ".join(part.split()) for part in sanitized.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def _normalize_day(day_value: str) -> str | None:
    candidate = day_value.strip().capitalize()
    for allowed in _ALLOWED_DAYS:
        if candidate.lower() == allowed.lower():
            return allowed
    return None


def write_clean_plan_csv(plan_rows: List[Dict[str, str]], destination: Path) -> Path:
    """Persist cleaned plan data to a CSV location."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=_REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(plan_rows)
    return destination
