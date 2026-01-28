# Pull Request: Claude Code CLI Integration

## 🎯 Summary

This PR adds support for **Claude Code CLI**, allowing users to run the AI Hedge Fund with their existing Claude Pro subscription - no API key required!

## ✨ What's New

### Claude Code CLI Integration
- **New LLM wrapper** (`src/llm/claude_code.py`) that interfaces with Claude Code CLI
- **LangChain-compatible** implementation for seamless integration with existing agents
- **Intelligent model tiering** - automatically selects OPUS for complex investor reasoning, SONNET for analysis tasks

### Enhanced Investor Prompts
- Rich biographical context for each famous investor agent
- Famous quotes that capture their investment philosophy  
- Specific investment criteria checklists
- Structured reasoning guidance with confidence scales

### Rich Terminal Output
- 🎨 ASCII art branding header
- 📊 Colored confidence bars with visual indicators
- 📈 Portfolio allocation ASCII charts
- 🗳️ Agent vote distribution summaries
- 🏆 Backtesting comparison with ranked accuracy
- ⏱️ Performance timing metrics

### Demo Scripts
- `scripts/demo_claude.py` - Full demo with live API calls
- `scripts/demo_output.py` - UI showcase with mock data (no API needed)

## 📁 Files Changed

```
src/
├── llm/
│   ├── claude_code.py        # NEW: Claude Code CLI wrapper
│   └── claude_code_llm.py    # NEW: LangChain-compatible LLM
├── prompts/
│   ├── __init__.py           # NEW: Prompts module
│   └── investor_prompts.py   # NEW: Enhanced investor prompts
└── utils/
    └── rich_output.py        # NEW: Rich terminal output

scripts/
├── demo_claude.py            # NEW: Full demo script
└── demo_output.py            # NEW: UI demo script

tests/
├── test_claude_code.py       # NEW: Claude Code tests
├── test_claude_code_llm.py   # NEW: LLM wrapper tests
└── test_agents_claude.py     # NEW: Agent integration tests

docs/
└── CLAUDE_INTEGRATION.md     # NEW: Integration guide
```

## 🧪 Testing

```bash
# Run all tests (91 tests passing)
poetry run pytest

# Run Claude-specific tests
poetry run pytest tests/test_claude_code.py tests/test_agents_claude.py -v

# UI demo (no API calls)
poetry run python scripts/demo_output.py
```

## 🚀 How to Use

### Quick Start
```bash
# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Run the hedge fund
poetry run python src/main.py --ticker AAPL,NVDA,TSLA
# Select "Claude Sonnet 4" from the model menu
```

### With Show Reasoning
```bash
poetry run python src/main.py --ticker AAPL,NVDA,TSLA --show-reasoning
```

## 📸 Sample Output

```
╔═══════════════════════════════════════════════════════════════╗
║     █████╗ ██╗    ██╗  ██╗███████╗██████╗  ██████╗ ███████╗   ║
║              🤖 AI-Powered Investment Analysis Platform       ║
╚═══════════════════════════════════════════════════════════════╝

📊 ANALYSIS OVERVIEW
  Tickers: AAPL, NVDA, TSLA
  Agents:  8 famous investors
  Time:    127.5s

🤖 AGENT SIGNALS
═══ AAPL ═══
Warren Buffett  ▲ BULLISH  88%  ████████████████
Charlie Munger  ▲ BULLISH  85%  ███████████████░
Ben Graham      ◆ NEUTRAL  45%  ███████░░░░░░░░░

💼 TRADING DECISIONS
  AAPL  🟢 BUY   50 shares  78%
  NVDA  🟡 HOLD   0 shares  55%
  TSLA  🔴 SELL  30 shares  72%

🏆 BACKTESTING COMPARISON
  🥇 Warren Buffett   66.7%
  🥈 Charlie Munger   66.7%
```

## ⚠️ Breaking Changes

None. This is an additive feature that works alongside existing LLM options.

## 📋 Checklist

- [x] Tests passing (91 tests)
- [x] Code formatted (black, isort)
- [x] Documentation updated
- [x] Demo scripts working
- [x] README updated with troubleshooting
- [x] No breaking changes to existing functionality

## 🔗 Related

- [Claude Code CLI](https://docs.anthropic.com/claude/docs/claude-code-cli)
- Integration Guide: `docs/CLAUDE_INTEGRATION.md`
- Summary: `CLAUDE_INTEGRATION_SUMMARY.md`
