"""User input collection step for the weekly diet pipeline."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

COMMON_DIETS: List[str] = [
    "Mediterranean Diet",
    "Ketogenic Diet",
    "Paleo Diet",
    "Vegetarian Diet",
    "Vegan Diet",
    "Pescatarian Diet",
    "DASH Diet",
    "Low-Carb Diet",
    "High-Protein Diet",
    "Gluten-Free Diet",
    "Whole30 Diet",
    "Flexitarian Diet",
]

NO_DIET_OPTION = "No Specific Diet"
CUSTOM_DIET_OPTION = "Custom Diet"


@dataclass
class UserInput:
    """Structured container for the user's initial preferences."""

    available_items: List[str]
    weekly_goal: str
    diet_choice: str
    custom_diet_description: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Convert the dataclass into a plain dictionary."""
        return asdict(self)


def collect_from_cli() -> UserInput:
    """Interactively collect preferences from the command line."""
    available_items = _collect_available_items()

    print("\nDescribe your primary goal for this week (e.g., 'cut down on sugar'):")
    weekly_goal = input("> ").strip()

    diet_choice = _choose_diet_option()

    custom_description: Optional[str] = None
    if diet_choice == CUSTOM_DIET_OPTION:
        print("\nDescribe your custom diet preference:")
        custom_description = input("> ").strip() or None

    return UserInput(
        available_items=available_items,
        weekly_goal=weekly_goal,
        diet_choice=diet_choice,
        custom_diet_description=custom_description,
    )


def get_diet_options() -> List[str]:
    """Return the list of available diet selections for UI rendering."""
    return [*COMMON_DIETS, NO_DIET_OPTION, CUSTOM_DIET_OPTION]


def _choose_diet_option() -> str:
    """Prompt the user to choose a diet option from the predefined list."""
    options = get_diet_options()
    print("\nSelect a diet plan for the week (enter the number):")
    for index, option in enumerate(options, start=1):
        print(f"  {index}. {option}")

    while True:
        selection = input("> ").strip()
        if selection.isdigit():
            idx = int(selection)
            if 1 <= idx <= len(options):
                return options[idx - 1]
        print("Invalid choice. Please enter a valid option number.")


def _collect_available_items() -> List[str]:
    """Collect pantry items one by one for easier processing."""
    print("Enter each item available in your kitchen. Press Enter on an empty line when finished.")
    items: List[str] = []
    while True:
        prompt = f"Item {len(items) + 1}> "
        value = input(prompt).strip()
        if not value:
            break
        items.append(value)
    return items
