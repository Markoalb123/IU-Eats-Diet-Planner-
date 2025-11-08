"""Configuration helpers for the diet generation application."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

_DEFAULT_PREPROCESSING_DIR = "data/preprocessing"
_DEFAULT_AI_OUTPUT_DIR = "data/model_outputs"
_DEFAULT_MODEL_NAME = "gpt-4.1-mini"
_DEFAULT_DASHBOARD_DB = "pipeline/rendering/index.db"
_DEFAULT_FRONTEND_ORIGIN = "http://localhost:5173"


def load_config() -> Dict[str, Any]:
    """Load configuration values from environment variables with sensible defaults."""
    load_dotenv()

    base_dir = Path(os.getenv("APP_BASE_DIR", Path(__file__).resolve().parent.parent))

    preprocessing_dir = Path(os.getenv("PREPROCESSING_OUTPUT_DIR", _DEFAULT_PREPROCESSING_DIR))
    if not preprocessing_dir.is_absolute():
        preprocessing_dir = base_dir / preprocessing_dir

    ai_output_dir = Path(os.getenv("AI_OUTPUT_DIR", _DEFAULT_AI_OUTPUT_DIR))
    if not ai_output_dir.is_absolute():
        ai_output_dir = base_dir / ai_output_dir

    dashboard_db_path = Path(os.getenv("DASHBOARD_DB_PATH", _DEFAULT_DASHBOARD_DB))
    if not dashboard_db_path.is_absolute():
        dashboard_db_path = base_dir / dashboard_db_path

    config = {
        "base_dir": base_dir,
        "preprocessing_output": str(preprocessing_dir),
        "ai_output": str(ai_output_dir),
        "model_name": os.getenv("MODEL_NAME", _DEFAULT_MODEL_NAME),
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "dashboard_db": str(dashboard_db_path),
        "frontend_origin": os.getenv("FRONTEND_ORIGIN", _DEFAULT_FRONTEND_ORIGIN),
    }

    return config
