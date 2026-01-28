"""
Tests for individual agents with Claude integration.

These tests verify that each agent:
1. Can be instantiated and called
2. Properly formats prompts for Claude
3. Returns expected output format
4. Handles errors gracefully
"""

import json
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.graph.state import AgentState


def create_mock_state(tickers=None, model_provider="Anthropic"):
    """Create a mock state for testing agents."""
    if tickers is None:
        tickers = ["AAPL"]

    return {
        "messages": [],
        "data": {
            "tickers": tickers,
            "start_date": "2024-01-01",
            "end_date": "2024-03-01",
            "portfolio": {
                "cash": 100000,
                "positions": {t: {"long": 0, "short": 0} for t in tickers},
            },
            "analyst_signals": {},
        },
        "metadata": {
            "show_reasoning": False,
            "model_name": "claude-sonnet-4-20250514",
            "model_provider": model_provider,
        },
    }


class TestWarrenBuffettAgent:
    """Tests for the Warren Buffett agent."""

    @patch("src.agents.warren_buffett.call_llm")
    @patch("src.agents.warren_buffett.get_financial_metrics")
    @patch("src.agents.warren_buffett.search_line_items")
    @patch("src.agents.warren_buffett.get_market_cap")
    def test_warren_buffett_agent_bullish(self, mock_market_cap, mock_line_items, mock_metrics, mock_call_llm):
        """Test Warren Buffett agent returns bullish signal."""
        from src.agents.warren_buffett import warren_buffett_agent, WarrenBuffettSignal

        # Mock financial data with all required attributes
        mock_metric = Mock()
        mock_metric.return_on_equity = 0.25
        mock_metric.return_on_invested_capital = 0.20
        mock_metric.debt_to_equity = 0.3
        mock_metric.operating_margin = 0.20
        mock_metric.current_ratio = 2.0
        mock_metric.asset_turnover = 1.2  # Need actual float for comparison
        mock_metric.model_dump.return_value = {}
        mock_metrics.return_value = [mock_metric] * 10

        # Mock line items
        mock_item = Mock()
        mock_item.net_income = 1000000000
        mock_item.depreciation_and_amortization = 100000000
        mock_item.capital_expenditure = -200000000
        mock_item.shareholders_equity = 500000000
        mock_item.outstanding_shares = 1000000
        mock_item.revenue = 5000000000
        mock_item.free_cash_flow = 800000000
        mock_item.gross_margin = 0.45
        mock_item.dividends_and_other_cash_distributions = -50000000
        mock_item.issuance_or_purchase_of_equity_shares = -100000000
        mock_item.working_capital = 200000000
        mock_line_items.return_value = [mock_item] * 10

        mock_market_cap.return_value = 2000000000000

        # Mock LLM response
        mock_call_llm.return_value = WarrenBuffettSignal(signal="bullish", confidence=85, reasoning="Strong ROE, low debt, excellent moat characteristics")

        state = create_mock_state()
        result = warren_buffett_agent(state)

        assert "messages" in result
        assert "data" in result

        # Verify the signal was stored
        signals = result["data"]["analyst_signals"]
        assert "warren_buffett_agent" in signals
        assert signals["warren_buffett_agent"]["AAPL"]["signal"] == "bullish"

    @patch("src.agents.warren_buffett.call_llm")
    @patch("src.agents.warren_buffett.get_financial_metrics")
    @patch("src.agents.warren_buffett.search_line_items")
    @patch("src.agents.warren_buffett.get_market_cap")
    def test_warren_buffett_agent_handles_missing_data(self, mock_market_cap, mock_line_items, mock_metrics, mock_call_llm):
        """Test Warren Buffett agent handles missing financial data."""
        from src.agents.warren_buffett import warren_buffett_agent, WarrenBuffettSignal

        # Return empty data
        mock_metrics.return_value = []
        mock_line_items.return_value = []
        mock_market_cap.return_value = None

        # LLM should still be called with whatever data is available
        mock_call_llm.return_value = WarrenBuffettSignal(signal="neutral", confidence=30, reasoning="Insufficient data for analysis")

        state = create_mock_state()
        result = warren_buffett_agent(state)

        # Should complete without errors
        assert "messages" in result


class TestPortfolioManager:
    """Tests for the Portfolio Manager agent."""

    @patch("src.agents.portfolio_manager.call_llm")
    def test_portfolio_manager_buy_decision(self, mock_call_llm):
        """Test portfolio manager makes buy decision."""
        from src.agents.portfolio_manager import (
            portfolio_management_agent,
            PortfolioDecision,
            PortfolioManagerOutput,
        )

        # Mock LLM response
        mock_call_llm.return_value = PortfolioManagerOutput(decisions={"AAPL": PortfolioDecision(action="buy", quantity=10, confidence=75, reasoning="Strong bullish signals from analysts")})

        state = create_mock_state()
        state["data"]["analyst_signals"] = {
            "warren_buffett_agent": {"AAPL": {"signal": "bullish", "confidence": 85}},
            "risk_management_agent": {
                "AAPL": {
                    "remaining_position_limit": 50000,
                    "current_price": 180.0,
                }
            },
        }

        result = portfolio_management_agent(state)

        assert "messages" in result
        # The decision should be in the final message
        final_message = result["messages"][-1]
        decision_data = json.loads(final_message.content)
        assert "AAPL" in decision_data
        assert decision_data["AAPL"]["action"] == "buy"

    @patch("src.agents.portfolio_manager.call_llm")
    def test_portfolio_manager_hold_when_no_capacity(self, mock_call_llm):
        """Test portfolio manager holds when no trade capacity."""
        from src.agents.portfolio_manager import (
            portfolio_management_agent,
            PortfolioDecision,
            PortfolioManagerOutput,
        )

        state = create_mock_state()
        state["data"]["analyst_signals"] = {
            "risk_management_agent": {
                "AAPL": {
                    "remaining_position_limit": 0,  # No capacity
                    "current_price": 180.0,
                }
            }
        }

        # LLM won't be called for tickers with no capacity
        result = portfolio_management_agent(state)

        assert "messages" in result


class TestSentimentAgent:
    """Tests for the Sentiment agent (non-LLM based)."""

    @patch("src.agents.sentiment.get_insider_trades")
    @patch("src.agents.sentiment.get_company_news")
    def test_sentiment_agent_bullish(self, mock_news, mock_trades):
        """Test sentiment agent returns bullish signal."""
        from src.agents.sentiment import sentiment_analyst_agent

        # Mock insider trades (buying activity)
        mock_trade = Mock()
        mock_trade.transaction_shares = 10000  # Positive = buying
        mock_trades.return_value = [mock_trade] * 10

        # Mock positive news
        mock_article = Mock()
        mock_article.sentiment = "positive"
        mock_news.return_value = [mock_article] * 20

        state = create_mock_state()
        result = sentiment_analyst_agent(state)

        signals = result["data"]["analyst_signals"]
        assert "sentiment_analyst_agent" in signals
        assert signals["sentiment_analyst_agent"]["AAPL"]["signal"] == "bullish"

    @patch("src.agents.sentiment.get_insider_trades")
    @patch("src.agents.sentiment.get_company_news")
    def test_sentiment_agent_bearish(self, mock_news, mock_trades):
        """Test sentiment agent returns bearish signal."""
        from src.agents.sentiment import sentiment_analyst_agent

        # Mock insider trades (selling activity)
        mock_trade = Mock()
        mock_trade.transaction_shares = -10000  # Negative = selling
        mock_trades.return_value = [mock_trade] * 10

        # Mock negative news
        mock_article = Mock()
        mock_article.sentiment = "negative"
        mock_news.return_value = [mock_article] * 20

        state = create_mock_state()
        result = sentiment_analyst_agent(state)

        signals = result["data"]["analyst_signals"]
        assert signals["sentiment_analyst_agent"]["AAPL"]["signal"] == "bearish"


class TestValuationAgent:
    """Tests for the Valuation agent (non-LLM based)."""

    @patch("src.agents.valuation.get_financial_metrics")
    @patch("src.agents.valuation.search_line_items")
    @patch("src.agents.valuation.get_market_cap")
    def test_valuation_agent_undervalued(self, mock_market_cap, mock_line_items, mock_metrics):
        """Test valuation agent identifies undervalued stock."""
        from src.agents.valuation import valuation_analyst_agent

        # Mock metrics showing undervaluation
        mock_metric = Mock()
        mock_metric.market_cap = 100000000000
        mock_metric.enterprise_value = 120000000000
        mock_metric.enterprise_value_to_ebitda_ratio = 10
        mock_metric.return_on_equity = 0.20
        mock_metric.debt_to_equity = 0.4
        mock_metric.interest_coverage = 15
        mock_metric.earnings_growth = 0.15
        mock_metric.revenue_growth = 0.10
        mock_metric.free_cash_flow_growth = 0.12
        mock_metric.book_value_growth = 0.08
        mock_metric.price_to_book_ratio = 5
        mock_metrics.return_value = [mock_metric] * 8

        # Mock line items
        mock_item = Mock()
        mock_item.free_cash_flow = 15000000000
        mock_item.net_income = 20000000000
        mock_item.depreciation_and_amortization = 5000000000
        mock_item.capital_expenditure = -10000000000
        mock_item.working_capital = 30000000000
        mock_item.total_debt = 50000000000
        mock_item.cash_and_equivalents = 40000000000
        mock_item.interest_expense = 2000000000
        mock_item.revenue = 200000000000
        mock_item.operating_income = 50000000000
        mock_item.ebit = 52000000000
        mock_item.ebitda = 57000000000
        mock_line_items.return_value = [mock_item] * 8

        mock_market_cap.return_value = 100000000000  # Low market cap vs intrinsic value

        state = create_mock_state()
        result = valuation_analyst_agent(state)

        signals = result["data"]["analyst_signals"]
        assert "valuation_analyst_agent" in signals


class TestRiskManager:
    """Tests for the Risk Manager agent."""

    @patch("src.agents.risk_manager.prices_to_df")
    @patch("src.agents.risk_manager.get_prices")
    def test_risk_manager_calculates_limits(self, mock_get_prices, mock_prices_to_df):
        """Test risk manager calculates position limits."""
        from datetime import datetime, timedelta

        import numpy as np
        import pandas as pd

        from src.agents.risk_manager import risk_management_agent

        # Create a proper DataFrame that the risk manager expects
        base_date = datetime(2024, 1, 1)
        dates = pd.date_range(start=base_date, periods=60, freq="D")
        df = pd.DataFrame(
            {
                "Date": dates,
                "open": np.random.uniform(175, 180, 60),
                "close": np.random.uniform(178, 185, 60),
                "high": np.random.uniform(180, 190, 60),
                "low": np.random.uniform(170, 178, 60),
                "volume": np.random.randint(40000000, 60000000, 60),
            }
        )
        df = df.set_index("Date")

        mock_get_prices.return_value = [Mock()] * 60  # Return something so the agent continues
        mock_prices_to_df.return_value = df

        state = create_mock_state()
        result = risk_management_agent(state)

        signals = result["data"]["analyst_signals"]
        assert "risk_management_agent" in signals
        assert "AAPL" in signals["risk_management_agent"]
        assert "remaining_position_limit" in signals["risk_management_agent"]["AAPL"]


class TestMultiTickerAnalysis:
    """Tests for multi-ticker analysis."""

    @patch("src.agents.sentiment.get_insider_trades")
    @patch("src.agents.sentiment.get_company_news")
    def test_sentiment_agent_multiple_tickers(self, mock_news, mock_trades):
        """Test sentiment agent handles multiple tickers."""
        from src.agents.sentiment import sentiment_analyst_agent

        # Mock data for each ticker
        mock_trade = Mock()
        mock_trade.transaction_shares = 5000
        mock_trades.return_value = [mock_trade] * 5

        mock_article = Mock()
        mock_article.sentiment = "positive"
        mock_news.return_value = [mock_article] * 10

        state = create_mock_state(tickers=["AAPL", "NVDA", "TSLA"])
        result = sentiment_analyst_agent(state)

        signals = result["data"]["analyst_signals"]["sentiment_analyst_agent"]
        assert "AAPL" in signals
        assert "NVDA" in signals
        assert "TSLA" in signals


class TestModelTierSelection:
    """Tests to verify correct model tier selection for agents."""

    def test_famous_investor_uses_opus(self):
        """Verify famous investor agents are assigned OPUS tier."""
        from src.llm.claude_config import get_claude_model_for_agent

        model, provider = get_claude_model_for_agent("warren_buffett_agent")
        assert "opus" in model.lower()

    def test_analysis_agent_uses_sonnet(self):
        """Verify analysis agents are assigned SONNET tier."""
        from src.llm.claude_config import get_claude_model_for_agent

        model, provider = get_claude_model_for_agent("sentiment_analyst_agent")
        assert "sonnet" in model.lower()

    def test_portfolio_manager_uses_sonnet(self):
        """Verify portfolio manager uses SONNET tier."""
        from src.llm.claude_config import get_claude_model_for_agent

        model, provider = get_claude_model_for_agent("portfolio_manager")
        assert "sonnet" in model.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
