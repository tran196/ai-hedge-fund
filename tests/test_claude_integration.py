"""
Tests for Claude Integration

This module tests:
1. Claude model configuration and tier selection
2. LLM call integration with Claude
3. Agent-specific model selection
4. Fallback behavior when Claude is not configured
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from pydantic import BaseModel, Field
from typing_extensions import Literal

# Import the modules under test
from src.llm.claude_config import (
    ClaudeModelTier,
    CLAUDE_MODELS,
    AGENT_MODEL_TIERS,
    get_claude_model_for_agent,
    is_claude_configured,
    get_default_model,
    get_model_tier_info,
)
from src.llm.models import ModelProvider, get_model
from src.utils.llm import call_llm, get_agent_model_config


class TestSignal(BaseModel):
    """Test Pydantic model for LLM output."""
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: int = Field(description="Confidence 0-100")
    reasoning: str = Field(description="Brief reasoning")


class TestClaudeConfig:
    """Tests for Claude configuration module."""

    def test_claude_models_defined(self):
        """Verify all model tiers have corresponding model names."""
        assert ClaudeModelTier.OPUS in CLAUDE_MODELS
        assert ClaudeModelTier.SONNET in CLAUDE_MODELS
        assert ClaudeModelTier.HAIKU in CLAUDE_MODELS
        
        # Verify model names look correct
        assert "opus" in CLAUDE_MODELS[ClaudeModelTier.OPUS].lower()
        assert "sonnet" in CLAUDE_MODELS[ClaudeModelTier.SONNET].lower()
        assert "haiku" in CLAUDE_MODELS[ClaudeModelTier.HAIKU].lower()

    def test_agent_model_tiers_defined(self):
        """Verify key agents have tier assignments."""
        # Famous investors should be OPUS
        assert AGENT_MODEL_TIERS["warren_buffett_agent"] == ClaudeModelTier.OPUS
        assert AGENT_MODEL_TIERS["charlie_munger_agent"] == ClaudeModelTier.OPUS
        assert AGENT_MODEL_TIERS["ben_graham_agent"] == ClaudeModelTier.OPUS
        
        # Analysis agents should be SONNET
        assert AGENT_MODEL_TIERS["sentiment_analyst_agent"] == ClaudeModelTier.SONNET
        assert AGENT_MODEL_TIERS["technicals_analyst_agent"] == ClaudeModelTier.SONNET
        
        # Portfolio manager should be SONNET
        assert AGENT_MODEL_TIERS["portfolio_manager"] == ClaudeModelTier.SONNET

    def test_get_claude_model_for_known_agent(self):
        """Test model selection for a known agent."""
        model_name, provider = get_claude_model_for_agent("warren_buffett_agent")
        
        assert provider == ModelProvider.ANTHROPIC.value
        assert "opus" in model_name.lower()

    def test_get_claude_model_for_unknown_agent(self):
        """Test model selection falls back to SONNET for unknown agents."""
        model_name, provider = get_claude_model_for_agent("unknown_agent")
        
        assert provider == ModelProvider.ANTHROPIC.value
        assert "sonnet" in model_name.lower()

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key-12345"})
    def test_is_claude_configured_with_key(self):
        """Test that Claude is detected as configured when API key exists."""
        assert is_claude_configured() is True

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=True)
    def test_is_claude_configured_without_key(self):
        """Test that Claude is not configured without API key."""
        # Clear the env var completely
        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]
        assert is_claude_configured() is False

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "your-anthropic-api-key"})
    def test_is_claude_configured_with_placeholder(self):
        """Test that placeholder API key is treated as not configured."""
        assert is_claude_configured() is False

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    def test_get_default_model_with_claude(self):
        """Test default model is Claude when configured."""
        model_name, provider = get_default_model()
        
        assert provider == ModelProvider.ANTHROPIC.value
        assert "claude" in model_name.lower()

    @patch.dict(os.environ, {}, clear=True)
    def test_get_default_model_without_claude(self):
        """Test default model falls back to OpenAI when Claude not configured."""
        # Ensure ANTHROPIC_API_KEY is not set
        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]
            
        model_name, provider = get_default_model()
        
        assert provider == ModelProvider.OPENAI.value
        assert "gpt" in model_name.lower()

    def test_get_model_tier_info(self):
        """Test model tier information is complete."""
        info = get_model_tier_info()
        
        assert "opus" in info
        assert "sonnet" in info
        assert "haiku" in info
        
        for tier_name, tier_info in info.items():
            assert "model" in tier_info
            assert "description" in tier_info
            assert "use_cases" in tier_info
            assert "cost" in tier_info


class TestGetModel:
    """Tests for model instantiation."""

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    def test_get_anthropic_model(self):
        """Test that Anthropic model can be instantiated."""
        model = get_model(
            "claude-sonnet-4-20250514",
            ModelProvider.ANTHROPIC,
            {"ANTHROPIC_API_KEY": "test-key"}
        )
        
        assert model is not None
        # ChatAnthropic should have a model attribute
        assert hasattr(model, 'model')

    def test_get_model_missing_api_key(self):
        """Test that missing API key raises appropriate error."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove the key if present
            if "ANTHROPIC_API_KEY" in os.environ:
                del os.environ["ANTHROPIC_API_KEY"]
                
            with pytest.raises(ValueError, match="Anthropic API key not found"):
                get_model("claude-sonnet-4-20250514", ModelProvider.ANTHROPIC, {})


class TestAgentModelConfig:
    """Tests for agent model configuration selection."""

    @patch('src.utils.llm.is_claude_configured')
    def test_agent_config_from_state(self, mock_is_claude):
        """Test that explicit state config takes precedence."""
        mock_is_claude.return_value = True
        
        state = {
            "metadata": {
                "model_name": "gpt-4o",
                "model_provider": "OpenAI"
            }
        }
        
        model_name, provider = get_agent_model_config(state, "warren_buffett_agent")
        
        # Should use explicit config, not Claude
        assert model_name == "gpt-4o"
        assert provider == "OpenAI"

    @patch('src.utils.llm.is_claude_configured')
    def test_agent_config_claude_tier_selection(self, mock_is_claude):
        """Test Claude tier selection when provider is Anthropic."""
        mock_is_claude.return_value = True
        
        state = {
            "metadata": {
                "model_provider": "Anthropic"
            }
        }
        
        # Warren Buffett should get OPUS
        model_name, provider = get_agent_model_config(state, "warren_buffett_agent")
        assert "opus" in model_name.lower()
        assert provider == "Anthropic"
        
        # Sentiment analyst should get SONNET
        model_name, provider = get_agent_model_config(state, "sentiment_analyst_agent")
        assert "sonnet" in model_name.lower()

    @patch('src.utils.llm.is_claude_configured')
    def test_agent_config_fallback_to_claude(self, mock_is_claude):
        """Test fallback to Claude when no config specified and Claude available."""
        mock_is_claude.return_value = True
        
        state = {
            "metadata": {}
        }
        
        model_name, provider = get_agent_model_config(state, "warren_buffett_agent")
        
        assert "claude" in model_name.lower()
        assert provider == "Anthropic"


class TestCallLLM:
    """Tests for the call_llm function with Claude."""

    @patch('src.utils.llm.get_model')
    @patch('src.utils.llm.get_model_info')
    @patch('src.utils.llm.is_claude_configured')
    def test_call_llm_with_claude(self, mock_is_claude, mock_get_info, mock_get_model):
        """Test LLM call flow with Claude model."""
        mock_is_claude.return_value = True
        
        # Mock model info
        mock_info = Mock()
        mock_info.has_json_mode.return_value = True
        mock_get_info.return_value = mock_info
        
        # Mock the LLM response
        mock_llm = Mock()
        mock_llm_with_output = Mock()
        mock_llm.with_structured_output.return_value = mock_llm_with_output
        mock_llm_with_output.invoke.return_value = TestSignal(
            signal="bullish",
            confidence=85,
            reasoning="Strong fundamentals"
        )
        mock_get_model.return_value = mock_llm
        
        # Create test state
        state = {
            "metadata": {
                "model_provider": "Anthropic"
            }
        }
        
        # Call the function
        result = call_llm(
            prompt="Analyze AAPL",
            pydantic_model=TestSignal,
            agent_name="warren_buffett_agent",
            state=state
        )
        
        # Verify result
        assert result.signal == "bullish"
        assert result.confidence == 85
        
        # Verify the model was called with structured output
        mock_llm.with_structured_output.assert_called_once()

    @patch('src.utils.llm.get_model')
    @patch('src.utils.llm.get_model_info')
    @patch('src.utils.llm.is_claude_configured')
    def test_call_llm_retry_on_failure(self, mock_is_claude, mock_get_info, mock_get_model):
        """Test that LLM call retries on failure."""
        mock_is_claude.return_value = True
        
        # Mock model info
        mock_info = Mock()
        mock_info.has_json_mode.return_value = True
        mock_get_info.return_value = mock_info
        
        # Mock the LLM to fail twice then succeed
        mock_llm = Mock()
        mock_llm_with_output = Mock()
        mock_llm.with_structured_output.return_value = mock_llm_with_output
        
        # First two calls fail, third succeeds
        mock_llm_with_output.invoke.side_effect = [
            Exception("Rate limit"),
            Exception("Rate limit"),
            TestSignal(signal="neutral", confidence=50, reasoning="Mixed signals")
        ]
        mock_get_model.return_value = mock_llm
        
        state = {"metadata": {"model_provider": "Anthropic"}}
        
        result = call_llm(
            prompt="Analyze AAPL",
            pydantic_model=TestSignal,
            agent_name="sentiment_analyst_agent",
            state=state,
            max_retries=3
        )
        
        # Should succeed on third attempt
        assert result.signal == "neutral"
        assert mock_llm_with_output.invoke.call_count == 3

    @patch('src.utils.llm.get_model')
    @patch('src.utils.llm.get_model_info')
    @patch('src.utils.llm.is_claude_configured')
    def test_call_llm_default_factory_on_failure(self, mock_is_claude, mock_get_info, mock_get_model):
        """Test that default factory is used when all retries fail."""
        mock_is_claude.return_value = True
        
        mock_info = Mock()
        mock_info.has_json_mode.return_value = True
        mock_get_info.return_value = mock_info
        
        # Mock the LLM to always fail
        mock_llm = Mock()
        mock_llm_with_output = Mock()
        mock_llm.with_structured_output.return_value = mock_llm_with_output
        mock_llm_with_output.invoke.side_effect = Exception("Always fails")
        mock_get_model.return_value = mock_llm
        
        state = {"metadata": {"model_provider": "Anthropic"}}
        
        # Provide a default factory
        def my_default():
            return TestSignal(signal="neutral", confidence=0, reasoning="Default")
        
        result = call_llm(
            prompt="Analyze AAPL",
            pydantic_model=TestSignal,
            agent_name="technicals_analyst_agent",
            state=state,
            max_retries=2,
            default_factory=my_default
        )
        
        # Should use default factory
        assert result.signal == "neutral"
        assert result.confidence == 0
        assert result.reasoning == "Default"


class TestModelTierIntegration:
    """Integration tests for model tier selection across agents."""

    def test_all_famous_investors_use_opus(self):
        """Verify all famous investor agents are assigned to OPUS tier."""
        famous_investors = [
            "warren_buffett_agent",
            "charlie_munger_agent",
            "ben_graham_agent",
            "peter_lynch_agent",
            "phil_fisher_agent",
            "michael_burry_agent",
            "bill_ackman_agent",
            "cathie_wood_agent",
            "stanley_druckenmiller_agent",
            "mohnish_pabrai_agent",
            "rakesh_jhunjhunwala_agent",
            "aswath_damodaran_agent",
        ]
        
        for agent in famous_investors:
            model_name, provider = get_claude_model_for_agent(agent)
            assert "opus" in model_name.lower(), f"{agent} should use OPUS tier"

    def test_analysis_agents_use_sonnet(self):
        """Verify analysis agents use SONNET tier."""
        analysis_agents = [
            "sentiment_analyst_agent",
            "technicals_analyst_agent",
            "fundamentals_analyst_agent",
            "valuation_analyst_agent",
        ]
        
        for agent in analysis_agents:
            model_name, provider = get_claude_model_for_agent(agent)
            assert "sonnet" in model_name.lower(), f"{agent} should use SONNET tier"

    def test_management_agents_use_appropriate_tier(self):
        """Verify management agents use appropriate tiers."""
        model_name, provider = get_claude_model_for_agent("portfolio_manager")
        assert "sonnet" in model_name.lower()
        
        model_name, provider = get_claude_model_for_agent("risk_management_agent")
        assert "sonnet" in model_name.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
