"""FastAPI server exposing the diet generation pipeline."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from app.config import load_config
from pipeline.input_collection.collector import (
    CUSTOM_DIET_OPTION,
    NO_DIET_OPTION,
    COMMON_DIETS,
    UserInput,
)
from pipeline.preprocessing import preprocess_user_input
from pipeline.ai_model import generate_weekly_plan, ModelGenerationError
from pipeline.postprocessing import (
    validate_and_clean_plan,
    write_clean_plan_csv,
    PostprocessingError,
)
from pipeline.storage import (
    store_plan_in_dashboard,
    append_plan_history,
    fetch_plan_history,
)
from pipeline.rendering import render_plan_dashboard


config = load_config()

app = FastAPI(title="Weekly Diet Planner API", version="0.1.0")

frontend_origin = config.get("frontend_origin", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PlanRequest(BaseModel):
    available_items: List[str] = Field(default_factory=list)
    weekly_goal: str = Field(..., min_length=1)
    diet_choice: str = Field(..., min_length=1)
    custom_diet_description: Optional[str] = None


class PlanResponse(BaseModel):
    plan: List[dict]
    csv_endpoint: str
    dashboard_endpoint: str
    dashboard_db_path: str


class HistoryItem(BaseModel):
    id: int
    created_at: str
    weekly_goal: Optional[str]
    diet_descriptor: Optional[str]
    plan: List[dict]


@app.get("/diets", response_model=List[str])
def list_diets() -> List[str]:
    """Return available diet options for the UI."""
    return [*COMMON_DIETS, NO_DIET_OPTION, CUSTOM_DIET_OPTION]


@app.post("/plan", response_model=PlanResponse)
def create_plan(payload: PlanRequest) -> PlanResponse:
    """Run the pipeline using JSON request data and return generated artifacts."""
    user_input = UserInput(
        available_items=payload.available_items,
        weekly_goal=payload.weekly_goal,
        diet_choice=payload.diet_choice,
        custom_diet_description=payload.custom_diet_description,
    )

    try:
        artifacts = preprocess_user_input(user_input)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        plan_csv = generate_weekly_plan(artifacts)
    except ModelGenerationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    try:
        cleaned_plan = validate_and_clean_plan(plan_csv)
    except PostprocessingError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    render_output_dir = Path(config["base_dir"]) / "pipeline" / "rendering" / "output"
    write_clean_plan_csv(cleaned_plan, render_output_dir / "weekday_plan.csv")
    dashboard_db = store_plan_in_dashboard(cleaned_plan)
    render_plan_dashboard(cleaned_plan)

    diet_descriptor = (
        (payload.custom_diet_description or "").strip()
        if payload.diet_choice == CUSTOM_DIET_OPTION
        else payload.diet_choice
    )
    append_plan_history(cleaned_plan, payload.weekly_goal, diet_descriptor)

    return PlanResponse(
        plan=cleaned_plan,
        csv_endpoint="/plan/csv",
        dashboard_endpoint="/dashboard",
        dashboard_db_path=str(dashboard_db.relative_to(config["base_dir"])),
    )


@app.get("/plan/csv")
def download_plan_csv() -> FileResponse:
    """Serve the cleaned plan CSV for download."""
    path = Path(config["base_dir"]) / "pipeline" / "rendering" / "output" / "weekday_plan.csv"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Plan CSV not found")
    return FileResponse(path, media_type="text/csv", filename="weekday_plan.csv")


@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard() -> HTMLResponse:
    """Serve the rendered HTML dashboard."""
    html_path = Path(config["base_dir"]) / "pipeline" / "rendering" / "output" / "dashboard.html"
    if not html_path.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.get("/history", response_model=List[HistoryItem])
def get_history(limit: int = Query(20, ge=1, le=100)) -> List[HistoryItem]:
    """Return the most recent saved plans."""
    return fetch_plan_history(limit=limit)
