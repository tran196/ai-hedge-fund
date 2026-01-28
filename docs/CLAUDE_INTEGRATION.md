# Claude Integration Guide

This document describes how the AI Hedge Fund uses Claude models for investment analysis.

## Overview

The AI Hedge Fund supports Claude models from Anthropic with intelligent **tiered model selection** that assigns the appropriate Claude model to each agent based on task complexity.

## Model Tiers

| Tier | Model | Use Case | Cost |
|------|-------|----------|------|
| **OPUS** | claude-opus-4-20250514 | Complex analysis, deep reasoning | High |
| **SONNET** | claude-sonnet-4-20250514 | Balanced analysis, most tasks | Medium |
| **HAIKU** | claude-3-5-haiku-latest | Quick decisions, simple tasks | Low |

## Agent Model Assignments

### OPUS Tier (Complex Reasoning)
Famous investor agents that emulate sophisticated investment philosophies:
- Warren Buffett Agent
- Charlie Munger Agent
- Ben Graham Agent
- Peter Lynch Agent
- Phil Fisher Agent
- Michael Burry Agent
- Bill Ackman Agent
- Cathie Wood Agent
- Stanley Druckenmiller Agent
- Mohnish Pabrai Agent
- Rakesh Jhunjhunwala Agent
- Aswath Damodaran Agent

### SONNET Tier (Balanced Performance)
Analysis and management agents:
- Valuation Analyst Agent
- Fundamentals Analyst Agent
- Sentiment Analyst Agent
- Technicals Analyst Agent
- Risk Management Agent
- Portfolio Manager

## Configuration

### Setting Up

1. Get your API key from [Anthropic Console](https://console.anthropic.com/)

2. Add to your `.env` file:
```bash
ANTHROPIC_API_KEY=your-api-key-here
```

3. Run the hedge fund - it will automatically use Claude when the key is set.

### Model Selection Priority

The system selects models in this order:
1. **Explicit state configuration** - If the user specifies a model via CLI or API
2. **Claude tier selection** - When Anthropic is the provider, uses appropriate tier
3. **Default fallback** - Claude Sonnet if Claude is configured, GPT-4.1 otherwise

### Using Claude via CLI

When you run the hedge fund, select a Claude model from the menu:
```bash
poetry run python src/main.py --ticker AAPL,NVDA,TSLA
```

Select one of:
- Claude Opus 4 (for maximum capability)
- Claude Sonnet 4 (recommended - balanced)
- Claude Haiku 3.5 (for speed/cost optimization)

### Demo Script

Run the demo to see Claude in action:
```bash
poetry run python scripts/demo_claude.py
```

## Architecture

### Model Configuration (`src/llm/claude_config.py`)

```python
from src.llm.claude_config import (
    get_claude_model_for_agent,  # Get model for specific agent
    is_claude_configured,         # Check if API key is set
    get_default_model,            # Get default model based on config
    get_model_tier_info,          # Get tier documentation
)
```

### LLM Utilities (`src/utils/llm.py`)

The `call_llm` function automatically:
1. Checks if Claude is configured
2. Selects the appropriate tier for the agent
3. Makes the API call with retry logic
4. Falls back to default responses on failure

```python
result = call_llm(
    prompt=prompt,
    pydantic_model=OutputModel,
    agent_name="warren_buffett_agent",  # Will use OPUS
    state=state,
)
```

## Cost Optimization

### Recommendations

1. **Development/Testing**: Use Haiku for faster iteration
2. **Production**: Use tiered selection (default)
3. **Critical Analysis**: Force Opus for all agents

### Overriding Tier Selection

To force a specific model for all agents, specify it explicitly:
```python
result = run_hedge_fund(
    tickers=tickers,
    model_name="claude-3-5-haiku-latest",  # Override tier selection
    model_provider="Anthropic",
    ...
)
```

## Testing

Run the Claude integration tests:
```bash
poetry run pytest tests/test_claude_integration.py -v
```

All tests are designed to work without making actual API calls (mocked).

## Troubleshooting

### "Anthropic API key not found"
- Ensure `ANTHROPIC_API_KEY` is set in `.env`
- Check the key is not the placeholder value
- Restart your terminal to reload environment variables

### Rate Limiting
The system automatically retries with exponential backoff on rate limit errors.

### Model Not Available
Ensure your Anthropic account has access to the model tier you're using.
Some tiers may require specific access levels.

## Comparison: Claude vs OpenAI

| Aspect | Claude | OpenAI |
|--------|--------|--------|
| Reasoning | Excellent for financial analysis | Good general purpose |
| JSON Mode | Supported | Supported |
| Context Window | 200K tokens | 128K tokens |
| Tiered Selection | ✅ Automatic | Manual only |

## Future Improvements

- [ ] Add support for Claude's extended thinking for complex valuations
- [ ] Implement model-specific prompt optimization
- [ ] Add cost tracking and reporting
- [ ] Support for Claude's computer use capabilities
