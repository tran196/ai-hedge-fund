# Claude Code CLI Setup Guide

This guide explains how to use the AI Hedge Fund with **Claude Code CLI** (Claude Pro subscription) instead of the Anthropic API. This is ideal for Claude Pro subscribers who want to leverage their subscription without additional API costs.

## Overview

The AI Hedge Fund supports two ways to use Claude models:

1. **Anthropic API** (default) - Requires `ANTHROPIC_API_KEY`
2. **Claude Code CLI** (new!) - Uses your Claude Pro subscription

## Prerequisites

### 1. Claude Pro Subscription
You need an active [Claude Pro subscription](https://claude.ai/pro) ($20/month).

### 2. Install Claude Code CLI

```bash
# Install via npm (Node.js 18+ required)
npm install -g @anthropic-ai/claude-code

# Verify installation
claude --version
```

### 3. Authenticate Claude Code

```bash
# Login to Claude (opens browser for authentication)
claude auth login
```

## Usage

### Option 1: Model Selection at Runtime

When you run the hedge fund, select a Claude model from the menu:

```bash
python src/main.py \
  --tickers AAPL,NVDA,TSLA \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --show-reasoning \
  --analysts-all
```

Then select **Claude Opus 4**, **Claude Sonnet 4**, or **Claude Haiku 3.5** from the model menu.

### Option 2: Running with Default Claude

The system automatically detects if Claude Code CLI is available:

1. If `claude` CLI is installed and authenticated → Uses Claude Code
2. If not → Falls back to Anthropic API (requires `ANTHROPIC_API_KEY`)

## How It Works

### Architecture

```
┌─────────────────────┐
│  AI Hedge Fund      │
│  Agent Pipeline     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  ChatClaudeCode     │
│  (LangChain Wrapper)│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Claude Code CLI    │
│  (PTY subprocess)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Claude Pro API     │
│  (Anthropic)        │
└─────────────────────┘
```

### Key Files

- `src/llm/claude_code_llm.py` - LangChain-compatible Claude Code wrapper
- `src/llm/models.py` - Model configuration and routing
- `src/llm/util.py` - Helper utilities for model selection

## Supported Models

| Model | CLI Name | Best For |
|-------|----------|----------|
| Claude Opus 4 | `opus` | Complex analysis, research |
| Claude Sonnet 4 | `sonnet` | Balanced speed/quality |
| Claude Haiku 3.5 | `haiku` | Fast, cost-effective |

## Structured Output

The system uses structured output for consistent JSON responses from Claude:

```python
from src.llm.claude_code_llm import ChatClaudeCode

llm = ChatClaudeCode(model="sonnet")
structured = llm.with_structured_output(MyPydanticModel)
result = structured.invoke([HumanMessage(content="...")])
```

## Troubleshooting

### Claude CLI Not Found

```
RuntimeError: Claude CLI not found
```

**Solution:**
```bash
# Check if claude is in PATH
which claude

# If not, reinstall
npm install -g @anthropic-ai/claude-code
```

### Authentication Issues

```
Error: Not authenticated
```

**Solution:**
```bash
claude auth login
```

### Timeout Issues

For long-running analyses, increase the timeout:

```python
llm = ChatClaudeCode(model="opus", timeout=300)  # 5 minutes
```

### PTY Errors on Windows

Claude Code CLI requires a pseudo-terminal. On Windows:

1. Use WSL2 (recommended)
2. Or use Git Bash / Cygwin

## Performance Tips

1. **Use Sonnet for most tasks** - Best balance of speed and quality
2. **Use Opus for complex analysis** - Better reasoning for valuation models
3. **Use Haiku for simple tasks** - Fast sentiment classification

## API Key Fallback

If Claude Code CLI isn't available, the system falls back to Anthropic API:

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

## Contributing

To add support for new Claude models:

1. Update `src/llm/models.py` with the new model
2. Add to `LLM_ORDER` list
3. Test with `pytest tests/test_claude_code.py`

## License

MIT License - See [LICENSE](../LICENSE) for details.
