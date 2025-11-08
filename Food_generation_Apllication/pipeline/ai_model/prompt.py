"""Prompt templates and builders for diet plan generation."""
from __future__ import annotations

from textwrap import dedent
from typing import List


def build_generation_prompt(
    available_items: List[str],
    weekly_goal: str,
    diet_description: str,
) -> str:
    """Construct a detailed diet-planning prompt for the language model."""
    items_section = "\n".join(f"- {item}" for item in available_items) or "- (no items provided)"

    prompt = dedent(
        f"""
        You are a registered dietitian and culinary expert helping a client plan weekday meals.
        Craft a Monday-through-Friday plan that uses the user's available items when reasonable,
        advances the weekly wellness goal, and aligns with the stated dietary approach.

        Context
        -------
        Weekly goal: {weekly_goal}
        Dietary framework: {diet_description}
        Ingredients on hand:
        {items_section}

        Requirements
        ------------
        1. Create exactly five entries—one for each weekday from Monday through Friday.
        2. Each entry must include the keys "day", "meal", "rationale", "recipe", "nutritional_value".
        3. Vary meal types, cuisines, and primary ingredients across the week while honoring restrictions.
        4. Assume the client has staple pantry basics (olive oil, salt, pepper, spices) unless the diet forbids them.
        5. If the available items list omits an essential component, you may introduce reasonable grocery additions while keeping focus on items on hand.

        Output Format
        -------------
        Respond with valid JSON only. Do not include explanations, code fences, Markdown, or any text before or after the JSON.
        Return an array of five objects ordered Monday through Friday with the structure:
        [
          {{
            "day": "Monday",
            "meal": "meal description",
            "rationale": "why this meal fits the diet and weekly goal",
            "recipe": "step-by-step instructions",
            "nutritional_value": "key nutrition facts"
          }},
          ... (Tuesday through Friday)
        ]
        """
    ).strip()

    return prompt
