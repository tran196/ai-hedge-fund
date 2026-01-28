# Claude Integration Summary

**Date:** January 28, 2025
**Branch:** `feature/claude-integration`
**Status:** ✅ Complete

## Major Update: Claude Code CLI Integration

This integration uses **Claude Code CLI** instead of the Anthropic API, allowing you to use your **existing Claude Pro subscription** without needing a separate API key!

## What Was Accomplished

### 1. Claude Code CLI Integration
- Created `src/llm/claude_code.py` with CLI wrapper
- Calls `claude --print --model <tier> --output-format json <prompt>`
- No API key required - uses your Claude subscription

### 2. Tiered Model Selection
| Tier | Agents | Use Case |
|------|--------|----------|
| **OPUS** | Warren Buffett, Charlie Munger, etc. | Complex investment reasoning |
| **SONNET** | Valuation, Sentiment, Risk, Portfolio | Balanced analysis |
| **HAIKU** | (Available for future use) | Quick tasks |

### 3. Smart Routing
The system automatically:
1. Checks if Claude Code CLI is available
2. Uses CLI for Claude provider requests
3. Falls back to Anthropic API if `USE_ANTHROPIC_API=true`
4. Falls back to OpenAI if nothing else available

### 4. Comprehensive Tests
- 22 tests for Claude Code CLI integration
- 77 total tests passing

## Quick Start

### 1. Install Claude Code CLI
```bash
npm install -g @anthropic-ai/claude-code
```

### 2. Verify Installation
```bash
claude --version
```

### 3. Run the Demo
```bash
poetry run python scripts/demo_claude.py
```

### 4. Run the Hedge Fund
```bash
poetry run python src/main.py --ticker AAPL,NVDA,TSLA
# Select "Claude Sonnet 4" from the menu
```

## Files Changed

### New Files
- `src/llm/claude_code.py` - Claude Code CLI wrapper
- `docs/CLAUDE_INTEGRATION.md` - Documentation
- `scripts/demo_claude.py` - Demo script
- `tests/test_claude_code.py` - Tests (22 tests)

### Modified Files
- `src/utils/llm.py` - Updated to route to Claude Code CLI
- `src/llm/api_models.json` - Reordered models
- `README.md` - Added Claude section

## Architecture

```
User Request
     │
     ▼
call_llm()
     │
     ├── Claude provider?
     │        │
     │        ├── CLI available? ──► subprocess: claude --print --model opus "prompt"
     │        │
     │        └── API key set? ──► LangChain: ChatAnthropic()
     │
     └── Other provider ──► LangChain: ChatOpenAI(), etc.
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| (none) | Claude Code CLI uses your subscription | No |
| `USE_ANTHROPIC_API` | Force API instead of CLI | No |
| `ANTHROPIC_API_KEY` | API key (only if forcing API) | No |
| `FINANCIAL_DATASETS_API_KEY` | For non-free stocks | No |

## Tests

```bash
# Run Claude Code tests only
poetry run pytest tests/test_claude_code.py -v

# Run all tests
poetry run pytest tests/ -v
```

## Git Commits

1. `feat: Add Claude model integration with tiered selection`
2. `docs: Add Claude integration guide and demo script`
3. `test: Add comprehensive agent tests for Claude integration`
4. `refactor: Switch to Claude Code CLI for Pro subscription support`

## Benefits of CLI Over API

| Aspect | Claude Code CLI | Anthropic API |
|--------|-----------------|---------------|
| Cost | Free with Pro subscription | Pay per token |
| Auth | Automatic (uses browser auth) | Requires API key |
| Setup | `npm install -g @anthropic-ai/claude-code` | Get key from console |
| Rate Limits | Pro subscription limits | API rate limits |

## Next Steps (Optional)

If time permits:
- [ ] Add streaming support for real-time output
- [ ] Implement extended thinking for complex valuations
- [ ] Add cost tracking (when using API fallback)
- [ ] Create benchmark comparing model tiers
