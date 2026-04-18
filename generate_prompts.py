#!/usr/bin/env python3
"""Generate Deep Research prompts for a new business idea."""

import argparse
import json
import os
import re
import sys

import yaml

import config
from claude_runner import invoke_claude, extract_json_from_response


def slugify(name: str) -> str:
    """Convert idea name to folder-friendly slug."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def load_prompt_template() -> str:
    """Load the research generator system prompt."""
    path = os.path.join(config.PROMPTS_DIR, "research_generator.md")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def generate_prompts(idea_name: str, thesis: str) -> dict:
    """Call Claude CLI to generate 4 tailored Deep Research prompts."""
    system_prompt = load_prompt_template()

    response = invoke_claude(
        prompt=(
            f"Generate Deep Research prompts for this business idea:\n\n"
            f"**Idea Name:** {idea_name}\n"
            f"**Thesis:** {thesis}\n\n"
            f"Return the JSON with all 4 research prompts."
        ),
        model=config.SCAN_MODEL,
        timeout=config.TIMEOUT,
        system_prompt=system_prompt,
    )

    return extract_json_from_response(response["content"])


def save_prompts(idea_slug: str, idea_name: str, thesis: str, prompts_data: dict):
    """Save generated prompts and idea.yaml to the idea folder."""
    idea_dir = os.path.join(config.IDEAS_DIR, idea_slug)
    prompts_dir = os.path.join(idea_dir, "prompts")
    research_dir = os.path.join(idea_dir, "research")

    os.makedirs(prompts_dir, exist_ok=True)
    os.makedirs(research_dir, exist_ok=True)

    # Save idea.yaml
    idea_yaml = {
        "name": idea_name,
        "thesis": thesis,
        "date_added": str(__import__("datetime").date.today()),
        "status": "new",
    }
    yaml_path = os.path.join(idea_dir, "idea.yaml")
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(idea_yaml, f, default_flow_style=False)

    # Save individual prompt files
    prompt_files = {
        "competitive": "01-competitive-landscape.md",
        "demand": "02-demand-validation.md",
        "technical": "03-technical-feasibility.md",
        "gtm": "04-go-to-market.md",
    }

    prompts = prompts_data.get("prompts", {})
    for key, filename in prompt_files.items():
        prompt_text = prompts.get(key, "")
        filepath = os.path.join(prompts_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(prompt_text)
        print(f"  Saved: {filepath}")

    print(f"\n  idea.yaml: {yaml_path}")
    return idea_dir


def main():
    parser = argparse.ArgumentParser(
        description="Generate Deep Research prompts for a business idea"
    )
    parser.add_argument("--idea", required=True, help="Idea name (e.g., 'LandedIQ')")
    parser.add_argument(
        "--thesis", required=True, help="One-line thesis for the idea"
    )
    args = parser.parse_args()

    idea_slug = slugify(args.idea)
    print(f"\nGenerating Deep Research prompts for: {args.idea}")
    print(f"Slug: {idea_slug}")
    print(f"Thesis: {args.thesis}\n")

    prompts_data = generate_prompts(args.idea, args.thesis)
    idea_dir = save_prompts(idea_slug, args.idea, args.thesis, prompts_data)

    print(f"\nDone! Prompts saved to: {idea_dir}/prompts/")
    print("\nNext steps:")
    print("  1. Paste each prompt into Perplexity AND Gemini Deep Research")
    print(f"  2. Save outputs as .md files in: {idea_dir}/research/")
    print("     Format: competitive-perplexity.md, competitive-gemini.md, etc.")
    print(f"  3. Run: python analyze.py --idea {idea_slug}")


if __name__ == "__main__":
    main()
