"""Interface for invoking the AI model to generate diet plans."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Sequence

from openai import OpenAI, PermissionDeniedError, APIError

from app.config import load_config
from pipeline.ai_model.prompt import build_generation_prompt


class ModelGenerationError(Exception):
    """Raised when the AI model cannot produce a valid meal plan."""


def generate_weekly_plan(artifact_paths: Dict[str, Path]) -> Path:
    """Produce a weekday meal plan CSV using previously collected artifacts."""
    config = load_config()

    api_key = config.get("openai_api_key")
    if not api_key:
        raise ModelGenerationError("OPENAI_API_KEY is not configured. Set it in your .env file.")

    available_items = _load_available_items(artifact_paths["available_items"])
    weekly_goal, diet_description = _load_weekly_preferences(artifact_paths["weekly_preferences"])

    prompt = build_generation_prompt(available_items, weekly_goal, diet_description)

    client = OpenAI(api_key=api_key)
    try:
        response = client.responses.create(
            model=config.get("model_name"),
            input=[
                {
                    "role": "system",
                    "content": "You are a meticulous dietitian and recipe developer.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
        )
    except PermissionDeniedError as exc:
        raise ModelGenerationError(
            "The configured OpenAI project does not have access to the selected model."
        ) from exc
    except APIError as exc:  # pragma: no cover - defensive
        raise ModelGenerationError(str(exc)) from exc

    raw_output = response.output_text
    plan_items = _parse_plan_response(raw_output)

    output_path = _write_plan_csv(plan_items, Path(config["ai_output"]))
    return output_path


def _load_available_items(path: Path) -> List[str]:
    items: List[str] = []
    with path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            value = (row.get("available_food") or "").strip()
            if value:
                items.append(value)
    return items


def _load_weekly_preferences(path: Path) -> Sequence[str]:
    with path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            goal = (row.get("goal") or "").strip()
            diet = (row.get("diet") or "").strip()
            return goal, diet
    return "", ""


def _parse_plan_response(raw_output: str) -> List[Dict[str, str]]:
    candidate = _extract_json_array(raw_output)
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ModelGenerationError("Model response was not valid JSON.") from exc

    if not isinstance(data, list):
        raise ModelGenerationError("Model response must be a JSON array.")

    required_keys = {"day", "meal", "rationale", "recipe", "nutritional_value"}
    normalized: List[Dict[str, str]] = []

    for entry in data:
        if not isinstance(entry, dict):
            raise ModelGenerationError("Each plan entry must be an object.")
        missing = required_keys - entry.keys()
        if missing:
            raise ModelGenerationError(
                f"Model response missing fields: {', '.join(sorted(missing))}."
            )
        normalized.append({key: str(entry[key]).strip() for key in required_keys})

    if len(normalized) != 5:
        raise ModelGenerationError("Plan must contain exactly five weekday entries.")

    return normalized


def _extract_json_array(raw_output: str) -> str:
    """Strip code fences/prose and return the JSON array string."""
    text = raw_output.strip()
    # Remove Markdown-style code fences if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, count=1).strip()
        text = re.sub(r"```$", "", text).strip()

    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return text  # Fallback so json.loads raises a clear error
    return text[start : end + 1]


def _write_plan_csv(plan_items: List[Dict[str, str]], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "weekday_plan.csv"
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["day", "meal", "rationale", "recipe", "nutritional_value"],
        )
        writer.writeheader()
        writer.writerows(plan_items)
    return output_path
