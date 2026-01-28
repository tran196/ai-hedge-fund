"""
Rich Output Module - Beautiful terminal output for AI Hedge Fund

Features:
- Colored terminal output with Rich library
- ASCII art portfolio allocation charts
- Confidence score visualization
- Summary reports with timing metrics
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from colorama import Fore, Style
from rich import print as rprint
from rich.box import DOUBLE, HEAVY, ROUNDED
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

console = Console()


# ═══════════════════════════════════════════════════════════════════════════════
# ASCII Chart Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def create_ascii_bar(value: float, max_value: float = 100, width: int = 20, filled_char: str = "█", empty_char: str = "░") -> str:
    """Create an ASCII progress bar."""
    if max_value <= 0:
        return empty_char * width
    ratio = min(value / max_value, 1.0)
    filled = int(ratio * width)
    return filled_char * filled + empty_char * (width - filled)


def create_confidence_bar(confidence: int) -> str:
    """Create a colored confidence bar based on confidence level."""
    bar = create_ascii_bar(confidence, 100, 15)
    if confidence >= 80:
        return f"[green]{bar}[/green]"
    elif confidence >= 60:
        return f"[yellow]{bar}[/yellow]"
    elif confidence >= 40:
        return f"[orange3]{bar}[/orange3]"
    else:
        return f"[red]{bar}[/red]"


def create_portfolio_pie_chart(allocations: Dict[str, float], width: int = 40) -> str:
    """
    Create an ASCII horizontal bar chart showing portfolio allocation.

    Args:
        allocations: Dict of ticker -> allocation percentage
        width: Width of the chart in characters
    """
    if not allocations:
        return "  No allocations"

    total = sum(allocations.values())
    if total <= 0:
        return "  No allocations"

    lines = []
    colors = ["cyan", "green", "yellow", "magenta", "blue", "red", "white"]

    for i, (ticker, value) in enumerate(sorted(allocations.items(), key=lambda x: x[1], reverse=True)):
        pct = (value / total) * 100
        bar_width = int((pct / 100) * width)
        bar = "█" * max(bar_width, 1)
        color = colors[i % len(colors)]
        lines.append(f"  [{color}]{ticker:6}[/{color}] [{color}]{bar}[/{color}] {pct:5.1f}%")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# Summary Report Components
# ═══════════════════════════════════════════════════════════════════════════════


def print_header():
    """Print the AI Hedge Fund header with ASCII art."""
    header = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║     █████╗ ██╗    ██╗  ██╗███████╗██████╗  ██████╗ ███████╗                   ║
║    ██╔══██╗██║    ██║  ██║██╔════╝██╔══██╗██╔════╝ ██╔════╝                   ║
║    ███████║██║    ███████║█████╗  ██║  ██║██║  ███╗█████╗                     ║
║    ██╔══██║██║    ██╔══██║██╔══╝  ██║  ██║██║   ██║██╔══╝                     ║
║    ██║  ██║██║    ██║  ██║███████╗██████╔╝╚██████╔╝███████╗                   ║
║    ╚═╝  ╚═╝╚═╝    ╚═╝  ╚═╝╚══════╝╚═════╝  ╚═════╝ ╚══════╝                   ║
║                                                                               ║
║              🤖 AI-Powered Investment Analysis Platform 🤖                    ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""
    console.print(header, style="bold cyan")


def print_investor_legend():
    """Print legend showing all available investor agents."""
    legend_data = [
        ("Warren Buffett", "Value investing, competitive moats, quality businesses"),
        ("Charlie Munger", "Mental models, predictable businesses, quality over price"),
        ("Ben Graham", "Deep value, margin of safety, Graham Number"),
        ("Peter Lynch", "GARP strategy, PEG ratio, invest in what you know"),
        ("Cathie Wood", "Disruptive innovation, exponential growth"),
        ("Michael Burry", "Contrarian value, asymmetric bets"),
        ("Bill Ackman", "Activist investing, catalyst-driven"),
        ("Stanley Druckenmiller", "Macro trends, position sizing"),
    ]

    table = Table(title="🎭 Famous Investor Agents", box=ROUNDED)
    table.add_column("Investor", style="cyan", width=20)
    table.add_column("Investment Philosophy", style="white", width=55)

    for name, philosophy in legend_data:
        table.add_row(name, philosophy)

    console.print(table)


def print_analysis_summary(result: dict, timing_info: Optional[dict] = None) -> None:
    """
    Print a beautiful summary report of the analysis.

    Args:
        result: Dictionary containing decisions and analyst_signals
        timing_info: Optional dict with timing metrics
    """
    print_header()
    console.print()

    decisions = result.get("decisions", {})
    analyst_signals = result.get("analyst_signals", {})

    if not decisions:
        console.print("[red]❌ No trading decisions available[/red]")
        return

    # ─── Analysis Overview ───
    console.print(Panel.fit("[bold]📊 ANALYSIS OVERVIEW[/bold]", border_style="cyan"))

    overview_table = Table(box=None, show_header=False, padding=(0, 2))
    overview_table.add_column("Key", style="dim")
    overview_table.add_column("Value", style="bold")

    overview_table.add_row("Tickers Analyzed", ", ".join(decisions.keys()))
    overview_table.add_row("Active Agents", str(len(analyst_signals)))
    overview_table.add_row("Analysis Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    if timing_info:
        total_time = timing_info.get("total_seconds", 0)
        overview_table.add_row("Total Duration", f"{total_time:.1f}s")

    console.print(overview_table)
    console.print()

    # ─── Agent Signals Grid ───
    console.print(Panel.fit("[bold]🤖 AGENT SIGNALS[/bold]", border_style="green"))

    for ticker in decisions.keys():
        console.print(f"\n[bold cyan]═══ {ticker} ═══[/bold cyan]")

        signal_table = Table(box=ROUNDED, show_lines=True)
        signal_table.add_column("Agent", style="cyan", width=22)
        signal_table.add_column("Signal", justify="center", width=10)
        signal_table.add_column("Conf", justify="center", width=8)
        signal_table.add_column("Confidence", justify="left", width=17)
        signal_table.add_column("Reasoning", style="dim", width=45)

        for agent_name, signals in analyst_signals.items():
            if agent_name == "risk_management_agent":
                continue
            if ticker not in signals:
                continue

            signal = signals[ticker]
            display_name = agent_name.replace("_agent", "").replace("_", " ").title()

            signal_type = signal.get("signal", "neutral").upper()
            confidence = signal.get("confidence", 50)
            reasoning = signal.get("reasoning", "")

            # Truncate reasoning for table display
            if len(reasoning) > 43:
                reasoning = reasoning[:40] + "..."

            # Color-code signal
            signal_style = {"BULLISH": "[bold green]▲ BULL[/bold green]", "BEARISH": "[bold red]▼ BEAR[/bold red]", "NEUTRAL": "[bold yellow]◆ NEUT[/bold yellow]"}.get(signal_type, signal_type)

            conf_bar = create_confidence_bar(confidence)

            signal_table.add_row(display_name, signal_style, f"{confidence}%", conf_bar, reasoning)

        console.print(signal_table)

    # ─── Trading Decisions ───
    console.print()
    console.print(Panel.fit("[bold]💼 TRADING DECISIONS[/bold]", border_style="yellow"))

    decision_table = Table(box=DOUBLE)
    decision_table.add_column("Ticker", style="bold cyan", width=8)
    decision_table.add_column("Action", justify="center", width=10)
    decision_table.add_column("Qty", justify="right", width=8)
    decision_table.add_column("Conf", justify="center", width=8)
    decision_table.add_column("Reasoning", width=50)

    for ticker, decision in decisions.items():
        action = decision.get("action", "HOLD").upper()
        quantity = decision.get("quantity", 0)
        confidence = decision.get("confidence", 0)
        reasoning = decision.get("reasoning", "")

        # Color-code actions
        action_display = {"BUY": "[bold green]🟢 BUY[/bold green]", "SELL": "[bold red]🔴 SELL[/bold red]", "HOLD": "[bold yellow]🟡 HOLD[/bold yellow]", "SHORT": "[bold red]📉 SHORT[/bold red]", "COVER": "[bold green]📈 COVER[/bold green]"}.get(action, action)

        # Truncate reasoning
        if len(reasoning) > 48:
            reasoning = reasoning[:45] + "..."

        decision_table.add_row(ticker, action_display, str(quantity), f"{confidence:.0f}%", reasoning)

    console.print(decision_table)

    # ─── Portfolio Allocation Chart ───
    console.print()
    console.print(Panel.fit("[bold]📈 PORTFOLIO ALLOCATION[/bold]", border_style="magenta"))

    # Calculate allocations from decisions
    allocations = {}
    total_value = 0
    for ticker, decision in decisions.items():
        quantity = abs(decision.get("quantity", 0))
        if quantity > 0:
            # Use quantity as proxy for allocation weight
            allocations[ticker] = quantity
            total_value += quantity

    if allocations:
        chart = create_portfolio_pie_chart(allocations)
        console.print(chart)
    else:
        console.print("  [dim]No active positions recommended[/dim]")

    # ─── Performance Metrics (if available) ───
    if timing_info:
        console.print()
        console.print(Panel.fit("[bold]⏱️ PERFORMANCE METRICS[/bold]", border_style="blue"))

        perf_table = Table(box=None, show_header=False)
        perf_table.add_column("Metric", style="dim", width=25)
        perf_table.add_column("Value", style="bold", width=20)

        if "agent_timings" in timing_info:
            for agent, time_sec in timing_info["agent_timings"].items():
                display_name = agent.replace("_agent", "").replace("_", " ").title()
                perf_table.add_row(f"  {display_name}", f"{time_sec:.2f}s")

        perf_table.add_row("─" * 25, "─" * 15)
        perf_table.add_row("  Total Time", f"{timing_info.get('total_seconds', 0):.2f}s")

        console.print(perf_table)

    # ─── Footer ───
    console.print()
    console.print("[dim]═══════════════════════════════════════════════════════════════════[/dim]")
    console.print("[dim]AI Hedge Fund - Analysis powered by Claude Code CLI[/dim]", justify="center")
    console.print("[dim]⚠️  This is for educational purposes only. Not financial advice.[/dim]", justify="center")


def print_agent_vote_summary(analyst_signals: dict, ticker: str) -> None:
    """
    Print a summary showing how agents voted for a specific ticker.

    Args:
        analyst_signals: Dict of agent_name -> {ticker -> signal_info}
        ticker: The ticker to summarize
    """
    bullish = 0
    bearish = 0
    neutral = 0

    for agent_name, signals in analyst_signals.items():
        if agent_name == "risk_management_agent":
            continue
        if ticker in signals:
            signal = signals[ticker].get("signal", "neutral").lower()
            if signal == "bullish":
                bullish += 1
            elif signal == "bearish":
                bearish += 1
            else:
                neutral += 1

    total = bullish + bearish + neutral
    if total == 0:
        return

    console.print(f"\n[bold]Vote Summary for {ticker}:[/bold]")
    console.print(f"  [green]▲ Bullish: {bullish}[/green] ({bullish/total*100:.0f}%)")
    console.print(f"  [red]▼ Bearish: {bearish}[/red] ({bearish/total*100:.0f}%)")
    console.print(f"  [yellow]◆ Neutral: {neutral}[/yellow] ({neutral/total*100:.0f}%)")

    # Visual vote bar
    width = 30
    bull_width = int((bullish / total) * width)
    bear_width = int((bearish / total) * width)
    neut_width = width - bull_width - bear_width

    bar = f"[green]{'█' * bull_width}[/green]" + f"[yellow]{'█' * neut_width}[/yellow]" + f"[red]{'█' * bear_width}[/red]"
    console.print(f"  {bar}")


def print_backtesting_comparison(predictions: dict, actual_returns: dict) -> None:
    """
    Print a comparison of agent predictions vs actual performance.

    Args:
        predictions: Dict of agent_name -> {ticker -> signal}
        actual_returns: Dict of ticker -> actual_return_pct
    """
    console.print()
    console.print(Panel.fit("[bold]📊 BACKTESTING COMPARISON[/bold]", border_style="cyan"))

    # Calculate accuracy for each agent
    agent_accuracy = {}

    for agent_name, signals in predictions.items():
        if agent_name == "risk_management_agent":
            continue

        correct = 0
        total = 0

        for ticker, signal_info in signals.items():
            if ticker not in actual_returns:
                continue

            signal = signal_info.get("signal", "neutral").lower()
            actual_return = actual_returns[ticker]

            # Determine if prediction was correct
            if signal == "bullish" and actual_return > 2:  # >2% gain
                correct += 1
            elif signal == "bearish" and actual_return < -2:  # >2% loss
                correct += 1
            elif signal == "neutral" and -2 <= actual_return <= 2:  # Flat
                correct += 1

            total += 1

        if total > 0:
            agent_accuracy[agent_name] = {"correct": correct, "total": total, "accuracy": (correct / total) * 100}

    # Sort by accuracy
    sorted_agents = sorted(agent_accuracy.items(), key=lambda x: x[1]["accuracy"], reverse=True)

    table = Table(title="Agent Prediction Accuracy", box=ROUNDED)
    table.add_column("Rank", justify="center", width=6)
    table.add_column("Agent", style="cyan", width=25)
    table.add_column("Accuracy", justify="center", width=12)
    table.add_column("Score", width=20)
    table.add_column("Correct/Total", justify="center", width=12)

    for rank, (agent_name, stats) in enumerate(sorted_agents, 1):
        display_name = agent_name.replace("_agent", "").replace("_", " ").title()
        accuracy = stats["accuracy"]

        # Medal for top 3
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, str(rank))

        accuracy_bar = create_confidence_bar(int(accuracy))

        table.add_row(medal, display_name, f"{accuracy:.1f}%", accuracy_bar, f"{stats['correct']}/{stats['total']}")

    console.print(table)


# ═══════════════════════════════════════════════════════════════════════════════
# Timing Context Manager
# ═══════════════════════════════════════════════════════════════════════════════


class TimingTracker:
    """Track timing for analysis operations."""

    def __init__(self):
        self.start_time: Optional[datetime] = None
        self.agent_timings: Dict[str, float] = {}
        self._current_agent: Optional[str] = None
        self._agent_start: Optional[datetime] = None

    def start(self):
        """Start the overall timer."""
        self.start_time = datetime.now()
        self.agent_timings = {}

    def start_agent(self, agent_name: str):
        """Start timing an agent."""
        self._current_agent = agent_name
        self._agent_start = datetime.now()

    def end_agent(self):
        """End timing for current agent."""
        if self._current_agent and self._agent_start:
            elapsed = (datetime.now() - self._agent_start).total_seconds()
            self.agent_timings[self._current_agent] = elapsed
            self._current_agent = None
            self._agent_start = None

    def get_results(self) -> dict:
        """Get timing results."""
        total = 0
        if self.start_time:
            total = (datetime.now() - self.start_time).total_seconds()

        return {"total_seconds": total, "agent_timings": self.agent_timings}


# Global timing tracker
timing_tracker = TimingTracker()
