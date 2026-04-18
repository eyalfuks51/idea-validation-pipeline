#!/usr/bin/env python3
"""Generate comparison dashboard across all analyzed ideas."""

import json
import os
import sys
import webbrowser

import yaml
from jinja2 import Environment, FileSystemLoader

import config


def load_all_ideas() -> list[dict]:
    """Load scores and metadata for all analyzed ideas."""
    ideas = []

    if not os.path.exists(config.IDEAS_DIR):
        print("Error: ideas/ directory not found")
        sys.exit(1)

    for idea_slug in sorted(os.listdir(config.IDEAS_DIR)):
        idea_dir = os.path.join(config.IDEAS_DIR, idea_slug)
        if not os.path.isdir(idea_dir):
            continue

        scores_path = os.path.join(idea_dir, "analysis", "scores.json")
        yaml_path = os.path.join(idea_dir, "idea.yaml")

        if not os.path.exists(scores_path):
            continue

        # Load idea metadata
        idea_data = {}
        if os.path.exists(yaml_path):
            with open(yaml_path, "r", encoding="utf-8") as f:
                idea_data = yaml.safe_load(f) or {}

        # Load scores
        with open(scores_path, "r", encoding="utf-8") as f:
            scores = json.load(f)

        # Load other analysis files for detail view
        analysis_dir = os.path.join(idea_dir, "analysis")
        analysis = {"scores": scores}
        for filename in ["synthesis.json", "devils-advocate.json", "market-realist.json", "builder-lens.json"]:
            filepath = os.path.join(analysis_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    key = filename.replace(".json", "").replace("-", "_")
                    analysis[key] = json.load(f)

        ideas.append({
            "slug": idea_slug,
            "name": idea_data.get("name", idea_slug),
            "thesis": idea_data.get("thesis", ""),
            "date_added": str(idea_data.get("date_added", "")),
            "scores": scores,
            "analysis": analysis,
        })

    return ideas


def generate_dashboard(ideas: list[dict]) -> str:
    """Render the comparison dashboard HTML."""
    # Sort by composite score descending
    ideas.sort(key=lambda x: x["scores"].get("composite_score", 0), reverse=True)

    env = Environment(loader=FileSystemLoader(config.TEMPLATES_DIR))
    template = env.get_template("dashboard.html.j2")

    score_labels = [
        "market_gap_severity",
        "demand_urgency",
        "willingness_to_pay",
        "competitive_moat",
        "solo_builder_feasibility",
        "gtm_clarity",
        "year1_revenue_potential",
        "timing_fit",
    ]

    html = template.render(
        ideas=ideas,
        score_labels=score_labels,
        score_weights=config.SCORE_WEIGHTS,
    )

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path


def main():
    ideas = load_all_ideas()

    if not ideas:
        print("No analyzed ideas found. Run analyze.py first.")
        sys.exit(1)

    print(f"Found {len(ideas)} analyzed idea(s):")
    for idea in ideas:
        verdict = idea["scores"].get("verdict", "N/A")
        composite = idea["scores"].get("composite_score", "N/A")
        print(f"  - {idea['name']}: {verdict} ({composite})")

    dashboard_path = generate_dashboard(ideas)
    print(f"\nDashboard generated: {dashboard_path}")

    webbrowser.open(f"file://{os.path.abspath(dashboard_path)}")


if __name__ == "__main__":
    main()
