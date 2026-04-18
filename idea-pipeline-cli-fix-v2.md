# Idea Validation Pipeline — Claude CLI Fix (v2)

## Context
The current build uses `anthropic` Python SDK with API keys — WRONG.
Eyal runs Claude via CLI on his Max plan. The exact pattern is in `polymarket-scout/scout/analysis/claude_runner.py`.

## CLI Pattern to Follow

The Claude CLI call signature is:
```
claude -p --model <model> --output-format json --dangerously-skip-permissions
```

Key details from the working Polymarket Scout implementation:
- **`-p` flag** (same as `--print`) — non-interactive output
- **`--output-format json`** — returns `{"result": "...", "input_tokens": ..., ...}`
- **`--dangerously-skip-permissions`** — uninterrupted execution
- **Prompt is piped via stdin** (not `--input-file`)
- **Model names:** `sonnet` for fast analysis, `opus` for deep analysis
- **JSON extraction:** The `result` field contains the actual response as a string. Must handle markdown fences, preamble text, and nested JSON
- **Windows compatibility:** Use `shutil.which("claude")` for path resolution
- **Timeout:** 180s default per call (bump to 300s for this project since research files are large)

## Implementation

```python
import subprocess
import shutil
import json
import sys

def invoke_claude(
    prompt: str,
    model: str = "sonnet",
    timeout: int = 300,
    system_prompt: str = None
) -> dict:
    """Call Claude CLI using Max plan subscription.
    
    Returns parsed JSON from Claude's response.
    Pattern matches polymarket-scout/scout/analysis/claude_runner.py
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
            encoding='utf-8'
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
    import re
    
    # Try 1: direct parse
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # Try 2: extract from markdown fence
    fence_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try 3: find first { ... } block
    brace_match = re.search(r'\{.*\}', content, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass
    
    raise ValueError(f"Could not extract JSON from response:\n{content[:500]}")
```

## Model Configuration
```python
# config.py
SCAN_MODEL = "sonnet"      # Synthesizer, Market Realist, Builder's Lens, Prompt Gen
DEEP_MODEL = "opus"         # Devil's Advocate, Scorer (these benefit from deeper reasoning)
TIMEOUT = 300               # 5 min per agent call
```

## What to Change in the Project

1. **Delete:** `.env` file, any `ANTHROPIC_API_KEY` references
2. **Delete:** `anthropic` from `requirements.txt`
3. **Replace:** All `client.messages.create()` calls with `invoke_claude()` + `extract_json_from_response()`
4. **Delete:** Retry/backoff logic (Claude CLI handles rate limits internally)
5. **Keep:** Everything else (Jinja2 templates, YAML, CLI args, file structure)

## Claude Code Command

```
Refactor the Idea Validation Pipeline to use Claude CLI instead of the anthropic SDK.

Here is the exact pattern to follow:

1. Claude CLI call: `claude -p --model <model> --output-format json --dangerously-skip-permissions`
2. Prompt piped via stdin (not as argument or file)
3. CLI returns JSON envelope: {"result": "...", "input_tokens": N, ...}
4. The "result" field contains the actual response text
5. Must extract JSON from the response (handle markdown fences, preamble text)
6. Use shutil.which("claude") for Windows path resolution
7. Timeout 300s per call

Use "sonnet" for most agents, "opus" for Devil's Advocate and Scorer.
Remove all anthropic SDK imports, .env file, and API key references.
No retry/backoff needed — CLI handles it.
```
