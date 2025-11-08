"""Input collection stage."""

from .collector import (
    CUSTOM_DIET_OPTION,
    NO_DIET_OPTION,
    COMMON_DIETS,
    UserInput,
    collect_from_cli,
    get_diet_options,
)

__all__ = [
    "CUSTOM_DIET_OPTION",
    "NO_DIET_OPTION",
    "COMMON_DIETS",
    "UserInput",
    "collect_from_cli",
    "get_diet_options",
]
