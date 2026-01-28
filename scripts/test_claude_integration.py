#!/usr/bin/env python3
"""
Test script for Claude Code CLI integration.

This script tests the AI Hedge Fund with Claude Code CLI (no API key required).
Uses Claude Pro subscription via the `claude` CLI.
"""

import os
import sys

# Ensure no API key is used
os.environ.pop('ANTHROPIC_API_KEY', None)

from datetime import datetime
from dateutil.relativedelta import relativedelta

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm.claude_config import is_claude_code_available, get_default_model
from src.llm.models import get_model, ModelProvider
from src.agents.portfolio_manager import PortfolioManagerOutput
from langchain_core.prompts import ChatPromptTemplate
import json


def test_claude_code_availability():
    """Test that Claude Code CLI is available."""
    print("=" * 60)
    print("Testing Claude Code CLI availability...")
    print("=" * 60)
    
    available = is_claude_code_available()
    print(f"  Claude Code CLI available: {available}")
    
    if not available:
        print("  ERROR: Claude Code CLI not found!")
        print("  Please install with: npm install -g @anthropic-ai/claude-code")
        return False
    
    model_name, provider = get_default_model()
    print(f"  Default model: {model_name} ({provider})")
    
    return True


def test_simple_call():
    """Test a simple Claude call."""
    print("\n" + "=" * 60)
    print("Testing simple Claude call...")
    print("=" * 60)
    
    from src.llm.claude_code_llm import ChatClaudeCode
    from langchain_core.messages import HumanMessage
    
    llm = ChatClaudeCode(model='sonnet', timeout=60)
    result = llm.invoke([HumanMessage(content='Say "Hello from Claude Code!" and nothing else.')])
    
    print(f"  Response: {result.content[:100]}")
    return "hello" in result.content.lower()


def test_structured_output():
    """Test structured output with portfolio decisions."""
    print("\n" + "=" * 60)
    print("Testing structured output...")
    print("=" * 60)
    
    llm = get_model('sonnet', ModelProvider.CLAUDE_CODE)
    
    signals = {
        'AAPL': {'sentiment': {'sig': 'bullish', 'conf': 80}},
        'NVDA': {'sentiment': {'sig': 'bullish', 'conf': 90}},
        'TSLA': {'sentiment': {'sig': 'bearish', 'conf': 60}},
    }
    allowed = {
        'AAPL': {'buy': 50, 'hold': 0},
        'NVDA': {'buy': 30, 'hold': 0},
        'TSLA': {'sell': 20, 'short': 10, 'hold': 0},
    }
    
    template = ChatPromptTemplate.from_messages([
        ('system', 'You are a portfolio manager. Make trading decisions based on analyst signals.'),
        ('human', 'Signals:\n{signals}\n\nAllowed actions:\n{allowed}')
    ])
    
    prompt = template.invoke({
        'signals': json.dumps(signals, indent=2),
        'allowed': json.dumps(allowed, indent=2)
    })
    
    structured_llm = llm.with_structured_output(PortfolioManagerOutput)
    result = structured_llm.invoke(prompt)
    
    print(f"  Decisions received for {len(result.decisions)} tickers:")
    for ticker, decision in result.decisions.items():
        print(f"    {ticker}: {decision.action} {decision.quantity} shares")
        print(f"      Confidence: {decision.confidence}%")
        print(f"      Reasoning: {decision.reasoning[:60]}...")
    
    return len(result.decisions) > 0


def test_agent_tier_selection():
    """Test that agents get the correct model tier."""
    print("\n" + "=" * 60)
    print("Testing agent tier selection...")
    print("=" * 60)
    
    from src.llm.claude_config import get_claude_model_for_agent
    
    test_agents = [
        ('warren_buffett_agent', 'opus'),
        ('portfolio_manager', 'sonnet'),
        ('sentiment_analyst_agent', 'sonnet'),
    ]
    
    all_pass = True
    for agent_name, expected_tier in test_agents:
        model_name, provider = get_claude_model_for_agent(agent_name, use_cli=True)
        matches = expected_tier in model_name.lower()
        status = "✓" if matches else "✗"
        print(f"  {status} {agent_name}: {model_name} (expected: {expected_tier})")
        all_pass = all_pass and matches
    
    return all_pass


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("AI HEDGE FUND - CLAUDE CODE CLI INTEGRATION TEST")
    print("=" * 60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Claude Code availability", test_claude_code_availability),
        ("Agent tier selection", test_agent_tier_selection),
        ("Simple call", test_simple_call),
        ("Structured output", test_structured_output),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed, None))
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"  ERROR: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, p, _ in results if p)
    total = len(results)
    
    for name, p, error in results:
        status = "✓ PASS" if p else "✗ FAIL"
        print(f"  {status}: {name}")
        if error:
            print(f"         Error: {error[:50]}...")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
