"""Rendering utilities for HTML dashboards."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping

from app.config import load_config
from pipeline.input_collection import collector

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

def render_initial_preferences_form() -> str:
    """Return the HTML page used to collect initial user inputs."""
    template = _load_template("index.html")
    html = template.replace("__COMMON_DIETS__", json.dumps(collector.COMMON_DIETS))
    html = html.replace("__NO_DIET_OPTION__", collector.NO_DIET_OPTION)
    html = html.replace("__CUSTOM_DIET_OPTION__", collector.CUSTOM_DIET_OPTION)
    return html


def render_plan_dashboard(plan_rows: Iterable[Mapping[str, str]]) -> Path:
    """Render the cleaned meal plan into an HTML dashboard and persist it."""
    config = load_config()
    output_dir = Path(config["base_dir"]) / "pipeline" / "rendering" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    plan_data = list(plan_rows)
    cards_html = "\n".join(_render_plan_card(row, index) for index, row in enumerate(plan_data, start=1))

    template = _load_template("dashboard.html")
    html = template.replace("__PLAN_CARDS__", cards_html)

    output_path = output_dir / "dashboard.html"
    output_path.write_text(html, encoding="utf-8")

    return output_path


def _render_plan_card(row: Mapping[str, str], sequence_number: int) -> str:
    return (
        f"<article class=\"plan-card\" data-day=\"{row['day']}\">"
        f"<header><span class=\"day\">{row['day']}</span>"
        f"<span class=\"sequence\">Day {sequence_number}</span></header>"
        f"<h3>{row['meal']}</h3>"
        f"<section class=\"segment\"><h4>Why this meal</h4><p>{_format_text(row['rationale'])}</p></section>"
        f"<section class=\"segment\"><h4>Recipe</h4>{_format_multiline(row['recipe'])}</section>"
        f"<section class=\"segment\"><h4>Nutritional Value</h4><p>{_format_text(row['nutritional_value'])}</p></section>"
        "</article>"
    )


def _format_text(text: str) -> str:
    return text.replace("\n", "<br />")


def _format_multiline(text: str) -> str:
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if len(lines) <= 1:
        return f"<p>{_format_text(text)}</p>"
    items = "".join(f"<li>{line}</li>" for line in lines)
    return f"<ol>{items}</ol>"


def _load_template(filename: str) -> str:
    path = TEMPLATE_DIR / filename
    return path.read_text(encoding="utf-8")
