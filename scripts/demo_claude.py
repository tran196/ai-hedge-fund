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
4. Display beautiful formatted results with ASCII charts
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from colorama import Fore, init, Style
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

# Load environment variables
load_dotenv()
init(autoreset=True)

console = Console()


def check_claude_code():
    """Check if Claude Code CLI is available."""
    from src.llm.claude_code import get_status, is_claude_code_available

    if not is_claude_code_available():
        console.print("[red]❌ Error: Claude Code CLI is not installed.[/red]")
        console.print("\n[yellow]Install with:[/yellow]")
        console.print("  npm install -g @anthropic-ai/claude-code")
        console.print("\nThen run this script again.")
        return False

    status = get_status()
    console.print("[green]✓ Claude Code CLI detected[/green]")
    if status.get("version"):
        console.print(f"  Version: {status['version']}")
    return True


def show_model_config():
    """Display the Claude model tier configuration."""
    from src.llm.claude_code import AGENT_MODEL_TIERS, get_status

    console.print(Panel.fit("[bold cyan]Claude Model Tier Configuration[/bold cyan]", border_style="cyan"))

    status = get_status()
    for tier_name, description in status["model_tiers"].items():
        console.print(f"[green]Tier: {tier_name.upper()}[/green]")
        console.print(f"  {description}")
        console.print()

    console.print("[yellow]Agent Model Assignments:[/yellow]")
    opus_agents = [a for a, t in AGENT_MODEL_TIERS.items() if t == "opus"]
    sonnet_agents = [a for a, t in AGENT_MODEL_TIERS.items() if t == "sonnet"]

    console.print(f"  [magenta]OPUS[/magenta] ({len(opus_agents)} agents): Complex reasoning required")
    for agent in opus_agents[:3]:
        agent_display = agent.replace("_agent", "").replace("_", " ").title()
        console.print(f"    • {agent_display}")
    if len(opus_agents) > 3:
        console.print(f"    ... and {len(opus_agents) - 3} more")

    console.print(f"  [cyan]SONNET[/cyan] ({len(sonnet_agents)} agents): Balanced performance")
    for agent in sonnet_agents[:3]:
        agent_display = agent.replace("_agent", "").replace("_", " ").title()
        console.print(f"    • {agent_display}")
    if len(sonnet_agents) > 3:
        console.print(f"    ... and {len(sonnet_agents) - 3} more")


def show_investor_legend():
    """Show the famous investor agents and their philosophies."""
    from src.utils.rich_output import print_investor_legend

    console.print()
    print_investor_legend()


def run_demo(use_rich_output: bool = True):
    """Run the demo with free stocks."""
    from dateutil.relativedelta import relativedelta

    from src.main import run_hedge_fund
    from src.utils.display import print_trading_output
    from src.utils.rich_output import print_analysis_summary, timing_tracker

    # Configuration
    tickers = ["AAPL", "NVDA", "TSLA"]  # Free stocks
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - relativedelta(months=3)).strftime("%Y-%m-%d")

    # Select a subset of agents for the demo
    selected_analysts = [
        "warren_buffett",  # Famous investor - uses OPUS
        "charlie_munger",  # Famous investor - uses OPUS
        "ben_graham",  # Famous investor - uses OPUS
        "sentiment",  # Analysis - uses SONNET
        "technicals",  # Analysis - uses SONNET
        "valuation",  # Analysis - uses SONNET
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
        "realized_gains": {ticker: {"long": 0.0, "short": 0.0} for ticker in tickers},
    }

    console.print()
    console.print(Panel.fit("[bold cyan]AI Hedge Fund Demo - Claude Code CLI[/bold cyan]", border_style="cyan"))

    console.print("\n[yellow]Configuration:[/yellow]")
    console.print(f"  Tickers: [cyan]{', '.join(tickers)}[/cyan]")
    console.print(f"  Date Range: {start_date} to {end_date}")
    console.print(f"  Initial Cash: [green]$100,000[/green]")
    console.print(f"  Analysts: {len(selected_analysts)} agents")
    console.print(f"  Model Provider: [magenta]Claude Code CLI[/magenta] (uses your subscription)")
    console.print()

    console.print("[green]Running analysis...[/green]")
    console.print("[dim](This may take a few minutes as each agent analyzes the stocks)[/dim]\n")

    # Start timing
    timing_tracker.start()

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

    # Get timing results
    timing_info = timing_tracker.get_results()

    console.print()

    # Display results
    if use_rich_output:
        print_analysis_summary(result, timing_info)
    else:
        console.print(Panel.fit("[bold cyan]Results[/bold cyan]", border_style="cyan"))
        print_trading_output(result)

    return result, timing_info


def main():
    """Main entry point."""
    from src.utils.rich_output import print_header

    print_header()
    console.print()

    # Check Claude Code CLI
    if not check_claude_code():
        sys.exit(1)

    console.print()

    # Show investor legend
    show_investor_legend()

    console.print()

    # Show model configuration
    show_model_config()

    # Ask to continue
    console.print("\n[yellow]Ready to run the demo?[/yellow]")
    console.print("This will use Claude Code CLI with your Claude subscription.")
    console.print("[dim]No API key required![/dim]")
    response = input("\nContinue? [y/N]: ").strip().lower()

    if response != "y":
        console.print("[dim]Demo cancelled.[/dim]")
        sys.exit(0)

    # Run the demo
    try:
        result, timing_info = run_demo(use_rich_output=True)

        console.print()
        console.print("[bold green]✓ Demo completed successfully![/bold green]")
        console.print(f"[dim]Total analysis time: {timing_info.get('total_seconds', 0):.1f}s[/dim]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error during demo: {e}[/red]")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
