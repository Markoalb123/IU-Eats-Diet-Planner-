"""Entry point for the diet generation application."""
from pathlib import Path

from app.config import load_config
from pipeline.input_collection import collect_from_cli
from pipeline.preprocessing import preprocess_user_input
from pipeline.ai_model import generate_weekly_plan
from pipeline.postprocessing import validate_and_clean_plan, write_clean_plan_csv
from pipeline.storage import store_plan_in_dashboard
from pipeline.rendering import render_plan_dashboard


def run() -> None:
    """Execute the end-to-end flow from input collection to dashboard rendering."""
    config = load_config()

    user_input = collect_from_cli()
    artifacts = preprocess_user_input(user_input)

    print("\nCaptured user preferences saved to:")
    for name, path in artifacts.items():
        print(f"  {name}: {path}")

    plan_csv = generate_weekly_plan(artifacts)
    cleaned_plan = validate_and_clean_plan(plan_csv)

    render_output_dir = Path(config["base_dir"]) / "pipeline" / "rendering" / "output"
    clean_csv_path = write_clean_plan_csv(cleaned_plan, render_output_dir / "weekday_plan.csv")
    db_path = store_plan_in_dashboard(cleaned_plan)
    dashboard_path = render_plan_dashboard(cleaned_plan)

    print("\nGenerated weekday meal plan:")
    print(f"  raw_plan_csv: {plan_csv}")
    print(f"  cleaned_plan_csv: {clean_csv_path}")
    print(f"  dashboard_db: {db_path}")
    print(f"  dashboard_html: {dashboard_path}")


if __name__ == "__main__":
    run()
