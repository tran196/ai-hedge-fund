"""
Claude Code CLI Integration for AI Hedge Fund

This module provides integration with Claude Code CLI, allowing the hedge fund
to use Claude via the user's Claude Pro subscription instead of requiring
a separate API key.

Usage:
    The `claude` CLI must be installed and authenticated.
    Install: npm install -g @anthropic-ai/claude-code

Model aliases:
    - "opus" or "claude-opus-4-20250514"
    - "sonnet" or "claude-sonnet-4-20250514"
    - "haiku" or "claude-3-5-haiku-latest"
"""

import json
import os
import shutil
import subprocess
from typing import Any, Dict, Optional, Tuple

from pydantic import BaseModel


class ClaudeCodeError(Exception):
    """Exception raised when Claude Code CLI fails."""

    pass


def is_claude_code_available() -> bool:
    """Check if Claude Code CLI is available and accessible."""
    return shutil.which("claude") is not None


def get_claude_code_version() -> Optional[str]:
    """Get the installed Claude Code CLI version."""
    try:
        result = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception:
        return None


def call_claude_code(
    prompt: str,
    model: str = "sonnet",
    system_prompt: Optional[str] = None,
    timeout: int = 120,
    output_format: str = "json",
) -> Dict[str, Any]:
    """
    Call Claude Code CLI with a prompt and return the response.

    Args:
        prompt: The user prompt to send to Claude
        model: Model alias ("opus", "sonnet", "haiku") or full name
        system_prompt: Optional system prompt to prepend
        timeout: Timeout in seconds (default 120)
        output_format: "json" for structured output, "text" for plain text

    Returns:
        Dictionary with response data when output_format="json",
        or {"text": response} when output_format="text"

    Raises:
        ClaudeCodeError: If CLI is not available or call fails
    """
    if not is_claude_code_available():
        raise ClaudeCodeError("Claude Code CLI is not installed. " "Install with: npm install -g @anthropic-ai/claude-code")

    # Normalize model names
    model_map = {
        "opus": "opus",
        "sonnet": "sonnet",
        "haiku": "haiku",
        "claude-opus-4-20250514": "opus",
        "claude-sonnet-4-20250514": "sonnet",
        "claude-3-5-haiku-latest": "haiku",
    }
    model_alias = model_map.get(model, model)

    # Build the full prompt with system context if provided
    full_prompt = prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n{prompt}"

    # Build command
    cmd = ["claude", "--print", "--model", model_alias, "--output-format", output_format, full_prompt]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env={**os.environ, "NO_COLOR": "1"})  # Disable color codes

        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            raise ClaudeCodeError(f"Claude Code CLI failed: {error_msg}")

        response_text = result.stdout.strip()

        if output_format == "json":
            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                # If JSON parsing fails, return as text
                return {"result": response_text, "type": "text"}
        else:
            return {"result": response_text, "type": "text"}

    except subprocess.TimeoutExpired:
        raise ClaudeCodeError(f"Claude Code CLI timed out after {timeout} seconds")
    except Exception as e:
        raise ClaudeCodeError(f"Error calling Claude Code CLI: {str(e)}")


def call_claude_code_structured(
    prompt: str,
    pydantic_model: type[BaseModel],
    model: str = "sonnet",
    system_prompt: Optional[str] = None,
    timeout: int = 120,
    max_retries: int = 3,
) -> BaseModel:
    """
    Call Claude Code CLI and parse response into a Pydantic model.

    Args:
        prompt: The user prompt
        pydantic_model: Pydantic model class to parse response into
        model: Model alias or full name
        system_prompt: Optional system prompt
        timeout: Timeout in seconds
        max_retries: Number of retries on parsing failure

    Returns:
        Instance of pydantic_model with parsed response
    """
    # Get the schema for the Pydantic model
    schema = pydantic_model.model_json_schema()

    # Build a structured output prompt
    json_format_prompt = f"""
{prompt}

Respond with ONLY valid JSON matching this schema:
{json.dumps(schema, indent=2)}

Output ONLY the JSON object, no markdown, no explanation."""

    for attempt in range(max_retries):
        try:
            # Call Claude Code
            result = call_claude_code(prompt=json_format_prompt, model=model, system_prompt=system_prompt, timeout=timeout, output_format="text")  # Get raw text to parse ourselves

            response_text = result.get("result", "")

            # Try to extract JSON from the response
            json_data = extract_json_from_response(response_text)

            if json_data:
                return pydantic_model(**json_data)
            else:
                raise ValueError("Could not extract JSON from response")

        except Exception as e:
            if attempt == max_retries - 1:
                # On final attempt, create a default response
                return create_default_response(pydantic_model, str(e))
            continue

    return create_default_response(pydantic_model, "Max retries exceeded")


def extract_json_from_response(content: str) -> Optional[Dict[str, Any]]:
    """Extract JSON from a response that may contain markdown or extra text."""
    # Try direct JSON parse first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Try to find JSON in markdown code blocks
    import re

    # Try ```json ... ``` format
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find JSON object directly
    brace_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", content, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def create_default_response(model_class: type[BaseModel], error_msg: str = "") -> BaseModel:
    """Create a safe default response based on the model's fields."""
    default_values = {}

    for field_name, field in model_class.model_fields.items():
        annotation = field.annotation

        if annotation == str:
            default_values[field_name] = f"Error: {error_msg}" if error_msg else "Default"
        elif annotation == float:
            default_values[field_name] = 0.0
        elif annotation == int:
            default_values[field_name] = 0
        elif hasattr(annotation, "__origin__") and annotation.__origin__ == dict:
            default_values[field_name] = {}
        elif hasattr(annotation, "__args__"):
            # For Literal types, use the first allowed value
            default_values[field_name] = annotation.__args__[0]
        else:
            default_values[field_name] = None

    return model_class(**default_values)


# Model tier configuration
class ClaudeModelTier:
    OPUS = "opus"
    SONNET = "sonnet"
    HAIKU = "haiku"


# Agent-to-tier mapping
AGENT_MODEL_TIERS: Dict[str, str] = {
    # Famous investor agents - require deep reasoning (OPUS)
    "warren_buffett_agent": ClaudeModelTier.OPUS,
    "charlie_munger_agent": ClaudeModelTier.OPUS,
    "ben_graham_agent": ClaudeModelTier.OPUS,
    "aswath_damodaran_agent": ClaudeModelTier.OPUS,
    "peter_lynch_agent": ClaudeModelTier.OPUS,
    "phil_fisher_agent": ClaudeModelTier.OPUS,
    "michael_burry_agent": ClaudeModelTier.OPUS,
    "bill_ackman_agent": ClaudeModelTier.OPUS,
    "cathie_wood_agent": ClaudeModelTier.OPUS,
    "stanley_druckenmiller_agent": ClaudeModelTier.OPUS,
    "mohnish_pabrai_agent": ClaudeModelTier.OPUS,
    "rakesh_jhunjhunwala_agent": ClaudeModelTier.OPUS,
    # Analysis agents - balanced (SONNET)
    "valuation_analyst_agent": ClaudeModelTier.SONNET,
    "fundamentals_analyst_agent": ClaudeModelTier.SONNET,
    "sentiment_analyst_agent": ClaudeModelTier.SONNET,
    "technicals_analyst_agent": ClaudeModelTier.SONNET,
    "news_sentiment_agent": ClaudeModelTier.SONNET,
    # Management agents - balanced (SONNET)
    "risk_management_agent": ClaudeModelTier.SONNET,
    "portfolio_manager": ClaudeModelTier.SONNET,
}


def get_model_for_agent(agent_name: str) -> str:
    """Get the appropriate Claude model tier for an agent."""
    return AGENT_MODEL_TIERS.get(agent_name, ClaudeModelTier.SONNET)


def get_status() -> Dict[str, Any]:
    """Get status of Claude Code CLI integration."""
    available = is_claude_code_available()
    version = get_claude_code_version() if available else None

    return {
        "available": available,
        "version": version,
        "model_tiers": {
            "opus": "Complex analysis (famous investors)",
            "sonnet": "Balanced tasks (analysis, management)",
            "haiku": "Quick tasks (not currently assigned)",
        },
        "agent_assignments": dict(list(AGENT_MODEL_TIERS.items())[:5]),
    }
