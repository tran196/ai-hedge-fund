"""
Unit tests for Claude Code CLI LLM wrapper.

Tests the ChatClaudeCode class and StructuredClaudeCode wrapper.
"""

import json
from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import BaseModel, Field
from typing_extensions import Literal


# Test models (named without 'Test' prefix to avoid pytest collection)
class PortfolioDecision(BaseModel):
    """Model for structured output testing."""

    action: Literal["buy", "sell", "hold"]
    quantity: int = Field(description="Number of shares")
    confidence: int = Field(description="Confidence 0-100")
    reasoning: str = Field(description="Brief reasoning")


class PortfolioOutput(BaseModel):
    """Model for portfolio output testing."""

    decisions: dict[str, PortfolioDecision]


class TestFindClaudeCli:
    """Tests for find_claude_cli function."""

    @patch("shutil.os.path.exists")
    def test_finds_cli_at_common_path(self, mock_exists):
        """Test that CLI is found at common installation path."""
        mock_exists.return_value = True

        from src.llm.claude_code_llm import find_claude_cli

        path = find_claude_cli()

        assert path is not None
        assert "claude" in path

    @patch("shutil.os.path.exists")
    @patch("subprocess.run")
    def test_uses_which_as_fallback(self, mock_run, mock_exists):
        """Test that 'which' command is used as fallback."""
        mock_exists.return_value = False
        mock_run.return_value = Mock(returncode=0, stdout="/usr/local/bin/claude\n")

        from src.llm.claude_code_llm import find_claude_cli

        path = find_claude_cli()

        assert path == "/usr/local/bin/claude"


class TestChatClaudeCode:
    """Tests for ChatClaudeCode class."""

    def test_model_initialization(self):
        """Test that model initializes with correct defaults."""
        from src.llm.claude_code_llm import ChatClaudeCode

        # Use model_construct to create instance without validation
        llm = ChatClaudeCode.model_construct(model="sonnet", timeout=120, max_tokens=None, claude_cli_path="/usr/bin/claude")

        assert llm.model == "sonnet"
        assert llm.timeout == 120
        assert llm._llm_type == "claude-code"

    def test_model_name_normalization(self):
        """Test model name normalization."""
        from src.llm.claude_code_llm import ChatClaudeCode

        # Use model_construct to create instance without validation
        llm = ChatClaudeCode.model_construct(model="sonnet", timeout=120, max_tokens=None, claude_cli_path="/usr/bin/claude")

        assert llm._normalize_model_name("sonnet") == "sonnet"
        assert llm._normalize_model_name("opus") == "opus"
        assert llm._normalize_model_name("claude-sonnet-4") == "sonnet"

    def test_clean_terminal_output(self):
        """Test terminal output cleaning."""
        from src.llm.claude_code_llm import ChatClaudeCode

        # Use model_construct to create instance without validation
        llm = ChatClaudeCode.model_construct(model="sonnet", timeout=120, max_tokens=None, claude_cli_path="/usr/bin/claude")

        # Test ANSI escape removal
        dirty = "Hello\x1b[0m World\x1b[32m!\n\n\n\nExtra"
        clean = llm._clean_terminal_output(dirty)

        assert "\x1b" not in clean
        assert "Hello" in clean
        assert "World" in clean
        # Multiple newlines should be reduced
        assert "\n\n\n\n" not in clean


class TestStructuredClaudeCode:
    """Tests for StructuredClaudeCode wrapper."""

    def test_example_generation_simple(self):
        """Test example generation for simple schema."""
        from src.llm.claude_code_llm import ChatClaudeCode, StructuredClaudeCode

        # Use model_construct to create instance without validation
        llm = ChatClaudeCode.model_construct(model="sonnet", timeout=120, max_tokens=None, claude_cli_path="/usr/bin/claude")

        structured = StructuredClaudeCode(llm, PortfolioDecision)
        schema = PortfolioDecision.model_json_schema()
        example = structured._get_example_from_schema(schema)

        assert "action" in example
        assert "quantity" in example
        assert "confidence" in example
        assert "reasoning" in example
        assert example["action"] == "buy"  # First enum value

    def test_example_generation_nested(self):
        """Test example generation for nested schema with dict."""
        from src.llm.claude_code_llm import ChatClaudeCode, StructuredClaudeCode

        # Use model_construct to create instance without validation
        llm = ChatClaudeCode.model_construct(model="sonnet", timeout=120, max_tokens=None, claude_cli_path="/usr/bin/claude")

        structured = StructuredClaudeCode(llm, PortfolioOutput)
        schema = PortfolioOutput.model_json_schema()
        example = structured._get_example_from_schema(schema)

        assert "decisions" in example
        # Should have a TICKER key with nested structure
        assert "TICKER" in example["decisions"]
        ticker_example = example["decisions"]["TICKER"]
        assert "action" in ticker_example
        assert "quantity" in ticker_example

    def test_json_extraction_from_code_block(self):
        """Test JSON extraction from markdown code blocks."""
        from src.llm.claude_code_llm import ChatClaudeCode, StructuredClaudeCode

        # Use model_construct to create instance without validation
        llm = ChatClaudeCode.model_construct(model="sonnet", timeout=120, max_tokens=None, claude_cli_path="/usr/bin/claude")
        structured = StructuredClaudeCode(llm, PortfolioDecision)

        response = """Here's the result:
            
```json
{"action": "buy", "quantity": 10, "confidence": 80, "reasoning": "Test"}
```

That's my decision."""

        json_str = structured._extract_json(response)
        data = json.loads(json_str)

        assert data["action"] == "buy"
        assert data["quantity"] == 10

    def test_json_extraction_direct_object(self):
        """Test JSON extraction when response is a direct JSON object."""
        from src.llm.claude_code_llm import ChatClaudeCode, StructuredClaudeCode

        # Use model_construct to create instance without validation
        llm = ChatClaudeCode.model_construct(model="sonnet", timeout=120, max_tokens=None, claude_cli_path="/usr/bin/claude")
        structured = StructuredClaudeCode(llm, PortfolioDecision)

        response = '{"action": "sell", "quantity": 5, "confidence": 60, "reasoning": "Bearish"}'
        json_str = structured._extract_json(response)
        data = json.loads(json_str)

        assert data["action"] == "sell"


class TestIntegration:
    """Integration tests (require actual Claude CLI)."""

    @pytest.mark.skipif(not __import__("shutil").which("claude"), reason="Claude CLI not available")
    def test_real_cli_simple_call(self):
        """Test actual CLI call if available."""
        from langchain_core.messages import HumanMessage

        from src.llm.claude_code_llm import ChatClaudeCode

        llm = ChatClaudeCode(model="sonnet", timeout=30)
        result = llm.invoke([HumanMessage(content='Say "test" and nothing else')])

        assert result.content is not None
        assert len(result.content) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
