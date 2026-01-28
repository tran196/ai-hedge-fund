# Claude Integration Guide

This document describes how the AI Hedge Fund uses Claude via **Claude Code CLI**, allowing you to use your existing Claude Pro subscription without needing a separate API key.

## Overview

The AI Hedge Fund supports Claude models with intelligent **tiered model selection** that assigns the appropriate Claude model to each agent based on task complexity.

**Key feature:** Uses Claude Code CLI - no API key required! Works with your existing Claude subscription.

## Prerequisites

### Install Claude Code CLI

```bash
# Install globally
npm install -g @anthropic-ai/claude-code

# Or locally
npm install @anthropic-ai/claude-code

# Verify installation
claude --version
```

### Authenticate
Claude Code CLI uses your existing Claude authentication. If you're logged into Claude via browser, it should work automatically.

## Model Tiers

| Tier | Model Alias | Use Case | Cost |
|------|-------------|----------|------|
| **OPUS** | `opus` | Complex analysis, deep reasoning | Highest |
| **SONNET** | `sonnet` | Balanced analysis, most tasks | Medium |
| **HAIKU** | `haiku` | Quick decisions, simple tasks | Lowest |

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

## Quick Start

### 1. Install Claude Code CLI
```bash
npm install -g @anthropic-ai/claude-code
```

### 2. Run the Hedge Fund
```bash
poetry run python src/main.py --ticker AAPL,NVDA,TSLA
```

Select "Claude Sonnet 4" or "Claude Opus 4" from the menu.

### 3. Run Demo Script
```bash
poetry run python scripts/demo_claude.py
```

## How It Works

### Detection Flow
1. System checks if `claude` CLI is available
2. If available, uses Claude Code CLI for all Claude provider requests
3. If not available but `ANTHROPIC_API_KEY` is set, falls back to Anthropic API
4. Otherwise falls back to OpenAI

### Tiered Selection
When using Claude (via CLI or API):
1. Agent name is checked against tier mapping
2. Appropriate model tier is selected (opus/sonnet/haiku)
3. Model is called via CLI or API

```python
# Example flow
agent_name = "warren_buffett_agent"
model_tier = get_model_for_agent(agent_name)  # Returns "opus"
result = call_claude_code(prompt, model=model_tier)
```

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `USE_ANTHROPIC_API` | Force API usage instead of CLI | `false` |
| `ANTHROPIC_API_KEY` | API key (only used if API preferred) | None |

### Force API Instead of CLI
```bash
export USE_ANTHROPIC_API=true
export ANTHROPIC_API_KEY=your-key-here
poetry run python src/main.py --ticker AAPL
```

## Architecture

### Files

| File | Purpose |
|------|---------|
| `src/llm/claude_code.py` | Claude Code CLI wrapper |
| `src/llm/claude_config.py` | API-based config (fallback) |
| `src/utils/llm.py` | Main LLM routing logic |

### Call Flow

```
User Request
     │
     ▼
call_llm()
     │
     ├── Claude provider? ──► should_use_claude_code()
     │                              │
     │                              ├── CLI available? ──► call_llm_claude_code()
     │                              │                              │
     │                              │                              └── claude --print --model opus "prompt"
     │                              │
     │                              └── API key set? ──► call_llm_langchain() with ChatAnthropic
     │
     └── Other provider ──► call_llm_langchain()
```

## Testing

Run the Claude Code tests:
```bash
poetry run pytest tests/test_claude_code.py -v
```

Run all tests:
```bash
poetry run pytest tests/ -v
```

## Troubleshooting

### "Claude Code CLI is not installed"
Install the CLI:
```bash
npm install -g @anthropic-ai/claude-code
```

### "claude: command not found"
Add npm global bin to PATH:
```bash
export PATH="$PATH:$(npm config get prefix)/bin"
```

### Rate Limiting
Claude Code CLI respects rate limits. If you hit limits:
- Wait a few minutes
- The system will retry automatically (up to 3 times)

### Fallback to API
If CLI issues persist, force API mode:
```bash
export USE_ANTHROPIC_API=true
export ANTHROPIC_API_KEY=your-key
```

## Comparison: CLI vs API

| Aspect | Claude Code CLI | Anthropic API |
|--------|-----------------|---------------|
| Authentication | Pro subscription | API key |
| Cost | Included in subscription | Pay per token |
| Rate Limits | Subscription limits | API limits |
| Setup | `npm install` | Get API key |
| Offline | No | No |

## Future Improvements

- [ ] Add support for Claude's extended thinking
- [ ] Implement streaming responses
- [ ] Add cost tracking (when using API)
- [ ] Support for MCP servers
- [ ] Add conversation continuity with `--continue`
