"""
Claude Model Configuration for AI Hedge Fund

This module defines model tiers and agent-specific model assignments
for optimal use of Claude's capabilities.

Model Tiers:
- OPUS: Complex analysis requiring deep reasoning (valuation, fundamentals, famous investors)
- SONNET: Routine tasks with good reasoning (sentiment, technicals, risk management)
- HAIKU: Quick decisions and simple formatting (portfolio manager final decisions)

Provider Options:
- ANTHROPIC: Uses Anthropic API (requires ANTHROPIC_API_KEY)
- CLAUDE_CODE: Uses Claude Code CLI (requires Claude Pro subscription, no API key)
"""

import os
import shutil
import subprocess
from enum import Enum
from typing import Dict, Optional, Tuple

from src.llm.models import ModelProvider


class ClaudeModelTier(str, Enum):
    """Model tiers based on complexity and cost."""
    OPUS = "opus"      # Most capable, for complex analysis
    SONNET = "sonnet"  # Balanced, for most tasks
    HAIKU = "haiku"    # Fast and efficient, for simple tasks


# Claude model names for each tier (for API)
CLAUDE_MODELS = {
    ClaudeModelTier.OPUS: "claude-opus-4-20250514",
    ClaudeModelTier.SONNET: "claude-sonnet-4-20250514",
    ClaudeModelTier.HAIKU: "claude-3-5-haiku-latest",
}

# Claude Code CLI model names (simpler names for CLI)
CLAUDE_CODE_MODELS = {
    ClaudeModelTier.OPUS: "opus",
    ClaudeModelTier.SONNET: "sonnet",
    ClaudeModelTier.HAIKU: "haiku",
}


# Agent-to-tier mapping
# Complex analysis agents get Opus, routine tasks get Sonnet/Haiku
AGENT_MODEL_TIERS: Dict[str, ClaudeModelTier] = {
    # Famous investor agents - require deep reasoning like the investors themselves
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
    
    # Analysis agents - Sonnet for good reasoning at lower cost
    "valuation_analyst_agent": ClaudeModelTier.SONNET,
    "fundamentals_analyst_agent": ClaudeModelTier.SONNET,
    "sentiment_analyst_agent": ClaudeModelTier.SONNET,
    "technicals_analyst_agent": ClaudeModelTier.SONNET,
    "news_sentiment_agent": ClaudeModelTier.SONNET,
    
    # Management agents - Sonnet for final decisions
    "risk_management_agent": ClaudeModelTier.SONNET,
    "portfolio_manager": ClaudeModelTier.SONNET,
}


def is_claude_code_available() -> bool:
    """Check if Claude Code CLI is available."""
    # Try common paths first
    common_paths = [
        "/Users/a/.nvm/versions/node/v22.16.0/bin/claude",
        shutil.which("claude"),
    ]
    
    for path in common_paths:
        if path and os.path.exists(path):
            return True
    
    # Try which command
    try:
        result = subprocess.run(
            ["which", "claude"], 
            capture_output=True, 
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False


def get_claude_model_for_agent(agent_name: str, use_cli: bool = None) -> Tuple[str, str]:
    """
    Get the appropriate Claude model for a given agent.
    
    Args:
        agent_name: The name of the agent (e.g., "warren_buffett_agent")
        use_cli: Force CLI (True) or API (False). If None, auto-detect.
        
    Returns:
        Tuple of (model_name, provider_name)
    """
    tier = AGENT_MODEL_TIERS.get(agent_name, ClaudeModelTier.SONNET)
    
    # Determine which provider to use
    if use_cli is None:
        # Auto-detect: prefer CLI if available and API key not set
        use_cli = is_claude_code_available() and not is_claude_configured()
    
    if use_cli:
        model_name = CLAUDE_CODE_MODELS[tier]
        return model_name, ModelProvider.CLAUDE_CODE.value
    else:
        model_name = CLAUDE_MODELS[tier]
        return model_name, ModelProvider.ANTHROPIC.value


def is_claude_configured() -> bool:
    """Check if Anthropic API key is configured."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    return bool(api_key and api_key != "your-anthropic-api-key")


def get_default_model() -> Tuple[str, str]:
    """
    Get the default model based on available options.
    
    Priority:
    1. Claude API if ANTHROPIC_API_KEY is set
    2. Claude Code CLI if available
    3. OpenAI GPT-4.1 as fallback
    """
    if is_claude_configured():
        return CLAUDE_MODELS[ClaudeModelTier.SONNET], ModelProvider.ANTHROPIC.value
    
    if is_claude_code_available():
        return CLAUDE_CODE_MODELS[ClaudeModelTier.SONNET], ModelProvider.CLAUDE_CODE.value
    
    # Fallback to OpenAI
    return "gpt-4.1", ModelProvider.OPENAI.value


def get_model_tier_info() -> Dict[str, Dict]:
    """
    Get information about model tiers for display purposes.
    
    Returns:
        Dictionary with tier info including model name, description, and use cases.
    """
    return {
        ClaudeModelTier.OPUS.value: {
            "model": CLAUDE_MODELS[ClaudeModelTier.OPUS],
            "description": "Most capable - deep reasoning and analysis",
            "use_cases": ["Famous investor agents", "Complex valuation", "Strategic decisions"],
            "cost": "High"
        },
        ClaudeModelTier.SONNET.value: {
            "model": CLAUDE_MODELS[ClaudeModelTier.SONNET],
            "description": "Balanced - good reasoning at lower cost",
            "use_cases": ["Technical analysis", "Sentiment analysis", "Risk management"],
            "cost": "Medium"
        },
        ClaudeModelTier.HAIKU.value: {
            "model": CLAUDE_MODELS[ClaudeModelTier.HAIKU],
            "description": "Fast and efficient - quick decisions",
            "use_cases": ["Simple formatting", "Quick summaries", "High-volume tasks"],
            "cost": "Low"
        },
    }
