#!/usr/bin/env python3
"""
Demo script for AI Hedge Fund with Claude Code CLI Integration

This script demonstrates the AI Hedge Fund running with Claude models
via Claude Code CLI (uses your Claude Pro subscription - no API key needed).

Usage:
    poetry run python scripts/demo_claude.py

Requirements:
    - Claude Code CLI installed: npm install -g @anthropic-ai/claude-code
    - Optional: FINANCIAL_DATASETS_API_KEY for non-free stocks

The script will:
1. Check Claude Code CLI availability
2. Show the model tier configuration
3. Run analysis with a subset of famous investor agents
4. Display the portfolio manager's decisions
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from colorama import Fore, Style, init

# Load environment variables
load_dotenv()
init(autoreset=True)


def check_claude_code():
    """Check if Claude Code CLI is available."""
    from src.llm.claude_code import is_claude_code_available, get_status
    
    if not is_claude_code_available():
        print(f"{Fore.RED}Error: Claude Code CLI is not installed.{Style.RESET_ALL}")
        print(f"\nInstall with:")
        print(f"  npm install -g @anthropic-ai/claude-code")
        print(f"\nThen run this script again.")
        return False
    
    status = get_status()
    print(f"{Fore.GREEN}✓ Claude Code CLI detected{Style.RESET_ALL}")
    if status.get("version"):
        print(f"  Version: {status['version']}")
    return True


def show_model_config():
    """Display the Claude model tier configuration."""
    from src.llm.claude_code import get_status, AGENT_MODEL_TIERS
    
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Claude Model Tier Configuration{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    status = get_status()
    for tier_name, description in status["model_tiers"].items():
        print(f"{Fore.GREEN}Tier: {tier_name.upper()}{Style.RESET_ALL}")
        print(f"  {description}")
        print()
    
    print(f"{Fore.YELLOW}Agent Model Assignments:{Style.RESET_ALL}")
    opus_agents = [a for a, t in AGENT_MODEL_TIERS.items() if t == "opus"]
    sonnet_agents = [a for a, t in AGENT_MODEL_TIERS.items() if t == "sonnet"]
    
    print(f"  OPUS ({len(opus_agents)} agents): Complex reasoning required")
    for agent in opus_agents[:3]:
        print(f"    - {agent}")
    if len(opus_agents) > 3:
        print(f"    ... and {len(opus_agents) - 3} more")
    
    print(f"  SONNET ({len(sonnet_agents)} agents): Balanced performance")
    for agent in sonnet_agents[:3]:
        print(f"    - {agent}")
    if len(sonnet_agents) > 3:
        print(f"    ... and {len(sonnet_agents) - 3} more")


def run_demo():
    """Run the demo with free stocks."""
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    from src.main import run_hedge_fund
    from src.utils.display import print_trading_output
    
    # Configuration
    tickers = ["AAPL", "NVDA", "TSLA"]  # Free stocks
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - relativedelta(months=3)).strftime("%Y-%m-%d")
    
    # Select a subset of agents for the demo
    selected_analysts = [
        "warren_buffett",      # Famous investor - uses OPUS
        "sentiment",           # Analysis - uses SONNET
        "technicals",          # Analysis - uses SONNET
        "valuation",           # Analysis - uses SONNET
    ]
    
    # Portfolio configuration
    portfolio = {
        "cash": 100000.0,
        "margin_requirement": 0.0,
        "margin_used": 0.0,
        "positions": {
            ticker: {
                "long": 0,
                "short": 0,
                "long_cost_basis": 0.0,
                "short_cost_basis": 0.0,
                "short_margin_used": 0.0,
            }
            for ticker in tickers
        },
        "realized_gains": {
            ticker: {"long": 0.0, "short": 0.0}
            for ticker in tickers
        },
    }
    
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}AI Hedge Fund Demo - Claude Code CLI{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    print(f"{Fore.YELLOW}Configuration:{Style.RESET_ALL}")
    print(f"  Tickers: {', '.join(tickers)}")
    print(f"  Date Range: {start_date} to {end_date}")
    print(f"  Initial Cash: $100,000")
    print(f"  Analysts: {', '.join(selected_analysts)}")
    print(f"  Model Provider: Claude Code CLI (uses your subscription)")
    print()
    
    print(f"{Fore.GREEN}Running analysis...{Style.RESET_ALL}")
    print(f"(This may take a few minutes as each agent analyzes the stocks)\n")
    
    # Run the hedge fund with Claude Code
    result = run_hedge_fund(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
        portfolio=portfolio,
        show_reasoning=True,
        selected_analysts=selected_analysts,
        model_name="sonnet",  # Will be overridden by tier selection
        model_provider="ClaudeCode",  # Use Claude Code CLI
    )
    
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Results{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    print_trading_output(result)
    
    return result


def main():
    """Main entry point."""
    print(f"\n{Fore.CYAN}AI Hedge Fund - Claude Code CLI Demo{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*40}{Style.RESET_ALL}\n")
    
    # Check Claude Code CLI
    if not check_claude_code():
        sys.exit(1)
    
    # Show model configuration
    show_model_config()
    
    # Ask to continue
    print(f"\n{Fore.YELLOW}Ready to run the demo?{Style.RESET_ALL}")
    print("This will use Claude Code CLI with your Claude subscription.")
    print("No API key required!")
    response = input("Continue? [y/N]: ").strip().lower()
    
    if response != 'y':
        print("Demo cancelled.")
        sys.exit(0)
    
    # Run the demo
    try:
        result = run_demo()
        print(f"\n{Fore.GREEN}Demo completed successfully!{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Error during demo: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
