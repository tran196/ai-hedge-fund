"""
Tests for Claude Code CLI Integration

These tests verify:
1. Claude Code CLI availability detection
2. Structured output parsing
3. Model tier selection for agents
4. Fallback behavior
"""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import BaseModel, Field
from typing_extensions import Literal


# Test model for structured output
class MockSignal(BaseModel):
    signal: Literal["bullish", "bearish", "neutral"]
    confidence: int = Field(description="Confidence 0-100")
    reasoning: str = Field(description="Brief reasoning")


class TestClaudeCodeAvailability:
    """Tests for Claude Code CLI availability."""

    @patch("shutil.which")
    def test_claude_code_available(self, mock_which):
        """Test detection when Claude Code CLI is installed."""
        from src.llm.claude_code import is_claude_code_available

        mock_which.return_value = "/usr/local/bin/claude"
        assert is_claude_code_available() is True

    @patch("shutil.which")
    def test_claude_code_not_available(self, mock_which):
        """Test detection when Claude Code CLI is not installed."""
        from src.llm.claude_code import is_claude_code_available

        mock_which.return_value = None
        assert is_claude_code_available() is False


class TestClaudeCodeCall:
    """Tests for calling Claude Code CLI."""

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_call_claude_code_success(self, mock_which, mock_run):
        """Test successful Claude Code CLI call."""
        from src.llm.claude_code import call_claude_code

        mock_which.return_value = "/usr/local/bin/claude"
        mock_run.return_value = Mock(returncode=0, stdout='{"result": "test response"}', stderr="")

        result = call_claude_code("Test prompt", model="sonnet")

        assert "result" in result
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "--print" in call_args[0][0]
        assert "--model" in call_args[0][0]
        assert "sonnet" in call_args[0][0]

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_call_claude_code_failure(self, mock_which, mock_run):
        """Test Claude Code CLI failure handling."""
        from src.llm.claude_code import call_claude_code, ClaudeCodeError

        mock_which.return_value = "/usr/local/bin/claude"
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="Error: Rate limited")

        with pytest.raises(ClaudeCodeError, match="Rate limited"):
            call_claude_code("Test prompt")

    @patch("shutil.which")
    def test_call_claude_code_not_installed(self, mock_which):
        """Test error when Claude Code CLI is not installed."""
        from src.llm.claude_code import call_claude_code, ClaudeCodeError

        mock_which.return_value = None

        with pytest.raises(ClaudeCodeError, match="not installed"):
            call_claude_code("Test prompt")


class TestClaudeCodeStructuredOutput:
    """Tests for structured output with Claude Code CLI."""

    @patch("src.llm.claude_code.call_claude_code")
    def test_structured_output_success(self, mock_call):
        """Test successful structured output parsing."""
        from src.llm.claude_code import call_claude_code_structured

        mock_call.return_value = {"result": json.dumps({"signal": "bullish", "confidence": 85, "reasoning": "Strong fundamentals"})}

        result = call_claude_code_structured(prompt="Analyze AAPL", pydantic_model=MockSignal, model="opus")

        assert isinstance(result, MockSignal)
        assert result.signal == "bullish"
        assert result.confidence == 85

    @patch("src.llm.claude_code.call_claude_code")
    def test_structured_output_with_markdown(self, mock_call):
        """Test parsing JSON from markdown code block."""
        from src.llm.claude_code import call_claude_code_structured

        mock_call.return_value = {"result": """Here's my analysis:
```json
{
    "signal": "bearish",
    "confidence": 70,
    "reasoning": "High debt levels"
}
```
That's my recommendation."""}

        result = call_claude_code_structured(prompt="Analyze TSLA", pydantic_model=MockSignal, model="sonnet")

        assert result.signal == "bearish"
        assert result.confidence == 70

    @patch("src.llm.claude_code.call_claude_code")
    def test_structured_output_fallback(self, mock_call):
        """Test fallback to default when parsing fails."""
        from src.llm.claude_code import call_claude_code_structured

        mock_call.return_value = {"result": "This is not valid JSON at all"}

        result = call_claude_code_structured(prompt="Analyze AAPL", pydantic_model=MockSignal, model="sonnet", max_retries=1)

        # Should return default values
        assert isinstance(result, MockSignal)
        assert result.signal in ["bullish", "bearish", "neutral"]


class TestModelTierSelection:
    """Tests for agent-to-model tier mapping."""

    def test_famous_investor_gets_opus(self):
        """Test that famous investor agents get OPUS tier."""
        from src.llm.claude_code import get_model_for_agent

        assert get_model_for_agent("warren_buffett_agent") == "opus"
        assert get_model_for_agent("charlie_munger_agent") == "opus"
        assert get_model_for_agent("ben_graham_agent") == "opus"

    def test_analysis_agent_gets_sonnet(self):
        """Test that analysis agents get SONNET tier."""
        from src.llm.claude_code import get_model_for_agent

        assert get_model_for_agent("sentiment_analyst_agent") == "sonnet"
        assert get_model_for_agent("technicals_analyst_agent") == "sonnet"
        assert get_model_for_agent("valuation_analyst_agent") == "sonnet"

    def test_unknown_agent_gets_sonnet(self):
        """Test that unknown agents default to SONNET tier."""
        from src.llm.claude_code import get_model_for_agent

        assert get_model_for_agent("unknown_agent") == "sonnet"
        assert get_model_for_agent("") == "sonnet"


class TestClaudeCodeStatus:
    """Tests for status reporting."""

    @patch("subprocess.run")
    @patch("shutil.which")
    def test_get_status_available(self, mock_which, mock_run):
        """Test status when CLI is available."""
        from src.llm.claude_code import get_status

        mock_which.return_value = "/usr/local/bin/claude"
        mock_run.return_value = Mock(returncode=0, stdout="1.0.0", stderr="")

        status = get_status()

        assert status["available"] is True
        assert status["version"] == "1.0.0"
        assert "model_tiers" in status
        assert "opus" in status["model_tiers"]

    @patch("shutil.which")
    def test_get_status_not_available(self, mock_which):
        """Test status when CLI is not available."""
        from src.llm.claude_code import get_status

        mock_which.return_value = None

        status = get_status()

        assert status["available"] is False
        assert status["version"] is None


class TestLLMRouting:
    """Tests for LLM routing between Claude Code CLI and other providers."""

    @patch("src.llm.claude_code.is_claude_code_available")
    def test_should_use_claude_code_when_available(self, mock_available):
        """Test that Claude Code CLI is used when available."""
        from src.utils.llm import should_use_claude_code

        mock_available.return_value = True

        assert should_use_claude_code("Anthropic") is True
        assert should_use_claude_code("Claude") is True
        assert should_use_claude_code("ClaudeCode") is True

    @patch("src.llm.claude_code.is_claude_code_available")
    def test_should_not_use_claude_code_for_openai(self, mock_available):
        """Test that OpenAI doesn't use Claude Code CLI."""
        from src.utils.llm import should_use_claude_code

        mock_available.return_value = True

        assert should_use_claude_code("OpenAI") is False
        assert should_use_claude_code("Groq") is False

    @patch("src.llm.claude_code.is_claude_code_available")
    def test_should_not_use_claude_code_when_unavailable(self, mock_available):
        """Test fallback when CLI is not available."""
        from src.utils.llm import should_use_claude_code

        mock_available.return_value = False

        assert should_use_claude_code("Anthropic") is False

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key", "USE_ANTHROPIC_API": "true"})
    @patch("src.llm.claude_code.is_claude_code_available")
    def test_prefer_api_when_flag_set(self, mock_available):
        """Test that API is used when USE_ANTHROPIC_API is set."""
        from src.utils.llm import should_use_claude_code

        mock_available.return_value = True

        # When USE_ANTHROPIC_API=true and API key is set, use API
        assert should_use_claude_code("Anthropic") is False


class TestDefaultModelSelection:
    """Tests for default model selection."""

    @patch("src.llm.claude_code.is_claude_code_available")
    def test_default_model_with_claude_code(self, mock_available):
        """Test default model when Claude Code CLI is available."""
        from src.utils.llm import get_default_model

        mock_available.return_value = True

        model, provider = get_default_model("warren_buffett_agent")

        assert model == "opus"  # Famous investor gets Opus
        assert provider == "ClaudeCode"

    @patch("src.llm.claude_code.is_claude_code_available")
    @patch.dict("os.environ", {}, clear=True)
    def test_default_model_fallback_to_openai(self, mock_available):
        """Test fallback to OpenAI when no Claude options available."""
        from src.utils.llm import get_default_model

        mock_available.return_value = False

        # Clear any existing env vars
        import os

        if "ANTHROPIC_API_KEY" in os.environ:
            del os.environ["ANTHROPIC_API_KEY"]

        model, provider = get_default_model("test_agent")

        assert model == "gpt-4.1"
        assert provider == "OpenAI"


class TestJSONExtraction:
    """Tests for JSON extraction from responses."""

    def test_extract_json_from_code_block(self):
        """Test extracting JSON from markdown code block."""
        from src.llm.claude_code import extract_json_from_response

        content = """Here's the result:
```json
{"signal": "bullish", "confidence": 90}
```
That's all."""

        result = extract_json_from_response(content)

        assert result is not None
        assert result["signal"] == "bullish"
        assert result["confidence"] == 90

    def test_extract_json_direct(self):
        """Test extracting direct JSON."""
        from src.llm.claude_code import extract_json_from_response

        content = '{"signal": "neutral", "confidence": 50}'

        result = extract_json_from_response(content)

        assert result is not None
        assert result["signal"] == "neutral"

    def test_extract_json_embedded(self):
        """Test extracting JSON embedded in text."""
        from src.llm.claude_code import extract_json_from_response

        content = 'The analysis shows {"signal": "bearish", "confidence": 75} for this stock.'

        result = extract_json_from_response(content)

        assert result is not None
        assert result["signal"] == "bearish"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
