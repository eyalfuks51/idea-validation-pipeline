#!/usr/bin/env python3
"""Run multi-agent analysis on a business idea's research files."""

import argparse
import json
import os
import sys
import time
import webbrowser

import yaml
from jinja2 import Environment, FileSystemLoader

import config
from claude_runner import invoke_claude, extract_json_from_response


def load_idea(idea_slug: str) -> dict:
    """Load idea.yaml for the given idea."""
    yaml_path = os.path.join(config.IDEAS_DIR, idea_slug, "idea.yaml")
    if not os.path.exists(yaml_path):
        print(f"Error: idea.yaml not found at {yaml_path}")
        sys.exit(1)
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_research_files(idea_slug: str) -> str:
    """Load all research files from the idea's research/ folder."""
    research_dir = os.path.join(config.IDEAS_DIR, idea_slug, "research")
    if not os.path.exists(research_dir):
        print(f"Error: research/ folder not found at {research_dir}")
        sys.exit(1)

    research_texts = []
    for filename in sorted(os.listdir(research_dir)):
        if filename.endswith((".md", ".txt")):
            filepath = os.path.join(research_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            research_texts.append(f"--- FILE: {filename} ---\n{content}")

    if not research_texts:
        print(f"Error: no .md or .txt files found in {research_dir}")
        sys.exit(1)

    print(f"  Loaded {len(research_texts)} research files")
    return "\n\n".join(research_texts)


def load_prompt(agent_name: str) -> str:
    """Load an agent's system prompt."""
    path = os.path.join(config.PROMPTS_DIR, f"{agent_name}.md")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def call_agent(system_prompt: str, user_message: str, agent_name: str, model: str = None) -> dict:
    """Call Claude CLI with an agent prompt and parse JSON response."""
    if model is None:
        model = config.SCAN_MODEL

    print(f"  Running {agent_name} ({model})...", end="", flush=True)
    start = time.time()

    response = invoke_claude(
        prompt=user_message,
        model=model,
        timeout=config.TIMEOUT,
        system_prompt=system_prompt,
    )

    result = extract_json_from_response(response["content"])
    elapsed = time.time() - start
    tokens = response["input_tokens"] + response["output_tokens"]
    print(f" done ({elapsed:.1f}s, {tokens} tokens)")
    return result


def save_json(data: dict, idea_slug: str, filename: str) -> str:
    """Save JSON data to the idea's analysis/ folder."""
    analysis_dir = os.path.join(config.IDEAS_DIR, idea_slug, "analysis")
    os.makedirs(analysis_dir, exist_ok=True)
    filepath = os.path.join(analysis_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return filepath


def render_report(idea_slug: str, idea_data: dict, synthesis: dict, devils: dict, market: dict, builder: dict, scores: dict):
    """Render single-idea HTML report using Jinja2."""
    env = Environment(loader=FileSystemLoader(config.TEMPLATES_DIR))
    template = env.get_template("report.html.j2")

    html = template.render(
        idea=idea_data,
        synthesis=synthesis,
        devils_advocate=devils,
        market_realist=market,
        builder_lens=builder,
        scores=scores,
    )

    report_path = os.path.join(config.IDEAS_DIR, idea_slug, "analysis", "report.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)

    return report_path


def analyze(idea_slug: str, force: bool = False):
    """Run the full analysis pipeline for an idea."""
    analysis_dir = os.path.join(config.IDEAS_DIR, idea_slug, "analysis")
    scores_path = os.path.join(analysis_dir, "scores.json")

    if os.path.exists(scores_path) and not force:
        print(f"Analysis already exists for '{idea_slug}'. Use --force to re-run.")
        return

    # Load inputs
    idea_data = load_idea(idea_slug)
    research_text = load_research_files(idea_slug)
    idea_name = idea_data.get("name", idea_slug)

    print(f"\nAnalyzing: {idea_name}")
    print(f"Thesis: {idea_data.get('thesis', 'N/A')}\n")

    # Agent 1: Synthesizer (sonnet)
    synthesis = call_agent(
        load_prompt("synthesizer"),
        f"Idea: {idea_name}\nThesis: {idea_data.get('thesis', '')}\n\n"
        f"Research reports:\n\n{research_text}",
        "Synthesizer",
    )
    save_json(synthesis, idea_slug, "synthesis.json")

    # Agent 2: Devil's Advocate (opus — deeper reasoning)
    devils = call_agent(
        load_prompt("devils_advocate"),
        f"Idea: {idea_name}\n\nSynthesis:\n{json.dumps(synthesis, indent=2)}",
        "Devil's Advocate",
        model=config.DEEP_MODEL,
    )
    save_json(devils, idea_slug, "devils-advocate.json")

    # Agent 3: Market Realist (sonnet)
    market = call_agent(
        load_prompt("market_realist"),
        f"Idea: {idea_name}\n\n"
        f"Synthesis:\n{json.dumps(synthesis, indent=2)}\n\n"
        f"Devil's Advocate Challenges:\n{json.dumps(devils, indent=2)}",
        "Market Realist",
    )
    save_json(market, idea_slug, "market-realist.json")

    # Agent 4: Builder's Lens (sonnet)
    builder = call_agent(
        load_prompt("builder_lens"),
        f"Idea: {idea_name}\nThesis: {idea_data.get('thesis', '')}\n\n"
        f"Synthesis:\n{json.dumps(synthesis, indent=2)}\n\n"
        f"Market Realist Assessment:\n{json.dumps(market, indent=2)}",
        "Builder's Lens",
    )
    save_json(builder, idea_slug, "builder-lens.json")

    # Scorer (opus — deeper reasoning)
    scores = call_agent(
        load_prompt("scorer"),
        f"Idea: {idea_name}\n\n"
        f"Synthesis:\n{json.dumps(synthesis, indent=2)}\n\n"
        f"Devil's Advocate:\n{json.dumps(devils, indent=2)}\n\n"
        f"Market Realist:\n{json.dumps(market, indent=2)}\n\n"
        f"Builder's Lens:\n{json.dumps(builder, indent=2)}",
        "Scorer",
        model=config.DEEP_MODEL,
    )
    save_json(scores, idea_slug, "scores.json")

    # Update idea status
    idea_data["status"] = "analyzed"
    yaml_path = os.path.join(config.IDEAS_DIR, idea_slug, "idea.yaml")
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(idea_data, f, default_flow_style=False)

    # Render HTML report
    report_path = render_report(idea_slug, idea_data, synthesis, devils, market, builder, scores)

    print(f"\nAnalysis complete!")
    print(f"  Scores: {scores_path}")
    print(f"  Report: {report_path}")

    verdict = scores.get("verdict", "N/A")
    composite = scores.get("composite_score", "N/A")
    print(f"\n  Verdict: {verdict} (composite: {composite})")

    return report_path


def main():
    parser = argparse.ArgumentParser(description="Analyze a business idea")
    parser.add_argument("--idea", required=True, help="Idea folder name (slug)")
    parser.add_argument("--force", action="store_true", help="Re-run even if analysis exists")
    parser.add_argument("--open", action="store_true", help="Open report in browser when done")
    args = parser.parse_args()

    report_path = analyze(args.idea, force=args.force)

    if args.open and report_path:
        webbrowser.open(f"file://{os.path.abspath(report_path)}")


if __name__ == "__main__":
    main()
