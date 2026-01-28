#!/usr/bin/env python3
"""
Demo script showing the enhanced output formatting without making API calls.
Useful for testing the UI and demonstrating capabilities.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console

from src.utils.rich_output import (
    print_agent_vote_summary,
    print_analysis_summary,
    print_backtesting_comparison,
    print_header,
    print_investor_legend,
)

console = Console()


def main():
    """Run demo with mock data."""

    # Print header
    print_header()
    console.print()

    # Show investor legend
    print_investor_legend()
    console.print()

    # Mock result data from a hypothetical analysis
    mock_result = {
        "decisions": {
            "AAPL": {"action": "BUY", "quantity": 50, "confidence": 78.5, "reasoning": "Strong moat in premium hardware/services ecosystem with consistent FCF generation"},
            "NVDA": {"action": "HOLD", "quantity": 0, "confidence": 55.0, "reasoning": "Excellent AI positioning but current valuation leaves no margin of safety"},
            "TSLA": {"action": "SELL", "quantity": 30, "confidence": 72.0, "reasoning": "Significant execution risk, competition intensifying, valuation stretched"},
        },
        "analyst_signals": {
            "warren_buffett_agent": {"AAPL": {"signal": "bullish", "confidence": 88, "reasoning": "Wonderful business at fair price, strong brand moat"}, "NVDA": {"signal": "neutral", "confidence": 52, "reasoning": "Good business but price too high for me"}, "TSLA": {"signal": "bearish", "confidence": 75, "reasoning": "Outside circle of competence, no margin of safety"}},
            "charlie_munger_agent": {"AAPL": {"signal": "bullish", "confidence": 85, "reasoning": "Predictable economics, rational management"}, "NVDA": {"signal": "bullish", "confidence": 68, "reasoning": "Lollapalooza in AI, but watch the price"}, "TSLA": {"signal": "bearish", "confidence": 62, "reasoning": "Too many moving parts, hard to predict"}},
            "ben_graham_agent": {"AAPL": {"signal": "neutral", "confidence": 45, "reasoning": "Above Graham Number, no classic value"}, "NVDA": {"signal": "bearish", "confidence": 35, "reasoning": "Fails all quantitative criteria"}, "TSLA": {"signal": "bearish", "confidence": 82, "reasoning": "P/E too high, no dividend history"}},
            "peter_lynch_agent": {"AAPL": {"signal": "bullish", "confidence": 72, "reasoning": "Stalwart with good PEG, know this business"}, "NVDA": {"signal": "bullish", "confidence": 78, "reasoning": "Fast grower, PEG reasonable for growth"}, "TSLA": {"signal": "neutral", "confidence": 50, "reasoning": "Story getting long, need better entry"}},
            "michael_burry_agent": {"AAPL": {"signal": "neutral", "confidence": 55, "reasoning": "Fair value, no asymmetric opportunity"}, "NVDA": {"signal": "bearish", "confidence": 70, "reasoning": "AI hype creating bubble conditions"}, "TSLA": {"signal": "bearish", "confidence": 78, "reasoning": "Contrarian short, reality vs expectations gap"}},
            "cathie_wood_agent": {"AAPL": {"signal": "neutral", "confidence": 48, "reasoning": "Mature business, limited disruption potential"}, "NVDA": {"signal": "bullish", "confidence": 92, "reasoning": "Cornerstone of AI revolution, Wright's Law"}, "TSLA": {"signal": "bullish", "confidence": 85, "reasoning": "Robotaxi and energy transformation leader"}},
            "sentiment_agent": {"AAPL": {"signal": "bullish", "confidence": 65, "reasoning": "Positive news sentiment, analyst upgrades"}, "NVDA": {"signal": "bullish", "confidence": 80, "reasoning": "AI narrative dominating coverage"}, "TSLA": {"signal": "neutral", "confidence": 50, "reasoning": "Mixed sentiment, political factors"}},
            "technicals_agent": {"AAPL": {"signal": "bullish", "confidence": 70, "reasoning": "Above 200 DMA, RSI healthy"}, "NVDA": {"signal": "bullish", "confidence": 75, "reasoning": "Strong momentum, breakout pattern"}, "TSLA": {"signal": "bearish", "confidence": 60, "reasoning": "Below key support, weakening momentum"}},
        },
    }

    timing_info = {"total_seconds": 127.5, "agent_timings": {"warren_buffett_agent": 18.2, "charlie_munger_agent": 19.5, "ben_graham_agent": 15.8, "peter_lynch_agent": 16.1, "michael_burry_agent": 14.3, "cathie_wood_agent": 17.2, "sentiment_agent": 12.4, "technicals_agent": 14.0}}

    # Print analysis summary
    print_analysis_summary(mock_result, timing_info)

    console.print()

    # Show vote summaries
    console.print("[bold cyan]Agent Vote Distribution:[/bold cyan]")
    for ticker in mock_result["decisions"].keys():
        print_agent_vote_summary(mock_result["analyst_signals"], ticker)

    console.print()

    # Show backtesting comparison
    mock_returns = {"AAPL": 8.5, "NVDA": -5.2, "TSLA": -12.3}  # +8.5% actual return  # -5.2% actual return  # -12.3% actual return
    print_backtesting_comparison(mock_result["analyst_signals"], mock_returns)


if __name__ == "__main__":
    main()
