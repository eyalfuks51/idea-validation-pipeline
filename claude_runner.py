"""Claude CLI runner — calls Claude via subprocess using Max plan.

Pattern matches polymarket-scout/scout/analysis/claude_runner.py
"""

import json
import re
import shutil
import subprocess
import sys


def invoke_claude(
    prompt: str,
    model: str = "sonnet",
    timeout: int = 300,
    system_prompt: str = None,
) -> dict:
    """Call Claude CLI using Max plan subscription.

    Returns parsed JSON from Claude's response.
    """
    claude_path = shutil.which("claude")
    if not claude_path:
        print("ERROR: 'claude' CLI not found in PATH", file=sys.stderr)
        sys.exit(1)

    cmd = [
        claude_path,
        "-p",
        "--model", model,
        "--output-format", "json",
        "--dangerously-skip-permissions",
    ]

    # Build the full prompt with system context if provided
    full_prompt = ""
    if system_prompt:
        full_prompt = f"<system>\n{system_prompt}\n</system>\n\n"
    full_prompt += prompt

    try:
        result = subprocess.run(
            cmd,
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
        )

        if result.returncode != 0:
            raise RuntimeError(f"Claude CLI error: {result.stderr}")

        # Parse the CLI JSON envelope
        cli_response = json.loads(result.stdout)

        # Extract the actual content from the "result" field
        content = cli_response.get("result", "")

        return {
            "content": content,
            "input_tokens": cli_response.get("input_tokens", 0),
            "output_tokens": cli_response.get("output_tokens", 0),
        }

    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Claude CLI timed out after {timeout}s")
    except json.JSONDecodeError:
        raise RuntimeError(f"Failed to parse Claude CLI output as JSON")


def extract_json_from_response(content: str) -> dict:
    """Extract JSON from Claude's response text.

    Handles:
    - Raw JSON
    - JSON wrapped in ```json ... ``` fences
    - JSON with preamble text before it
    """
    # Try 1: direct parse
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try 2: extract from markdown fence
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try 3: find first { ... } block
    brace_match = re.search(r"\{.*\}", content, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract JSON from response:\n{content[:500]}")
