"""
Claude Code CLI LLM Wrapper

This module provides a LangChain-compatible wrapper for Claude Code CLI.
Allows using Claude Pro subscription instead of Anthropic API key.

Usage:
    llm = ChatClaudeCode(model="sonnet")
    response = llm.invoke("Hello, Claude!")
"""

import json
import os
import pty
import re
import select
import shutil
import subprocess
import time
from typing import Any, Iterator, List, Optional

from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field, model_validator


# Find claude CLI path
def find_claude_cli() -> str:
    """Find the claude CLI executable path."""
    # Try common locations
    common_paths = [
        "/Users/a/.nvm/versions/node/v22.16.0/bin/claude",
        "/usr/local/bin/claude",
        shutil.which("claude"),
    ]

    for path in common_paths:
        if path and shutil.os.path.exists(path):
            return path

    # Try which command as fallback
    result = subprocess.run(["which", "claude"], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()

    raise RuntimeError("Claude CLI not found. Please install it: npm install -g @anthropic-ai/claude-code")


class ChatClaudeCode(BaseChatModel):
    """
    LangChain-compatible chat model that uses Claude Code CLI.

    This allows using Claude Pro subscription without needing an API key.

    Args:
        model: Model to use ("opus", "sonnet", "haiku", or full model name)
        timeout: Timeout for CLI calls in seconds
        max_tokens: Maximum tokens in response (optional)
    """

    model: str = Field(default="sonnet", description="Model name (opus/sonnet/haiku)")
    timeout: int = Field(default=120, description="Timeout in seconds")
    max_tokens: Optional[int] = Field(default=None, description="Max output tokens")
    claude_cli_path: str = Field(default="", description="Path to claude CLI")

    @model_validator(mode="after")
    def validate_and_set_cli_path(self) -> "ChatClaudeCode":
        """Find and set the claude CLI path."""
        if not self.claude_cli_path:
            self.claude_cli_path = find_claude_cli()
        return self

    @property
    def _llm_type(self) -> str:
        """Return identifier of the LLM."""
        return "claude-code"

    @property
    def _identifying_params(self) -> dict:
        """Return identifying parameters."""
        return {
            "model": self.model,
            "timeout": self.timeout,
            "max_tokens": self.max_tokens,
        }

    def _normalize_model_name(self, model: str) -> str:
        """Normalize model name for CLI."""
        # Map short names to full model names
        model_mapping = {
            "opus": "opus",
            "sonnet": "sonnet",
            "haiku": "haiku",
        }

        # Check if it's a short name
        model_lower = model.lower()
        for short, cli_name in model_mapping.items():
            if short in model_lower:
                return cli_name

        # Return as-is for full model names
        return model

    def _messages_to_prompt(self, messages: List[BaseMessage]) -> tuple[str, Optional[str]]:
        """Convert messages to a prompt string and optional system prompt."""
        system_prompt = None
        prompt_parts = []

        for msg in messages:
            if isinstance(msg, SystemMessage):
                system_prompt = msg.content
            elif isinstance(msg, HumanMessage):
                prompt_parts.append(msg.content)
            elif isinstance(msg, AIMessage):
                prompt_parts.append(f"Assistant: {msg.content}")

        return "\n\n".join(prompt_parts), system_prompt

    def _clean_terminal_output(self, text: str) -> str:
        """Remove ANSI escape codes and terminal control sequences."""
        # Remove ANSI escape sequences
        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        text = ansi_escape.sub("", text)
        # Remove OSC sequences (like terminal title setting)
        text = re.sub(r"\x1B\][^\x07]*\x07", "", text)
        text = re.sub(r"\]9;[0-9;]+;", "", text)  # iTerm2 specific
        # Remove CSI sequences
        text = re.sub(r"\[\?[0-9;]*[a-zA-Z]", "", text)
        # Remove misc control sequences
        text = re.sub(r"\[<u", "", text)
        text = re.sub(r"\[25h", "", text)
        # Remove carriage returns
        text = text.replace("\r", "")
        # Clean up multiple newlines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _call_claude_cli(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Call Claude CLI and return the response."""
        # Build command
        cmd = [
            self.claude_cli_path,
            "--model",
            self._normalize_model_name(self.model),
            "--print",  # Non-interactive output
            "--output-format",
            "text",  # Plain text output
        ]

        # Add system prompt if provided
        if system_prompt:
            cmd.extend(["--system-prompt", system_prompt])

        # Add the prompt at the end (positional argument)
        cmd.append(prompt)

        try:
            # Use PTY for the CLI since it requires a terminal
            master_fd, slave_fd = pty.openpty()
            proc = subprocess.Popen(
                cmd,
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                close_fds=True,
            )
            os.close(slave_fd)

            # Read output with timeout
            output = b""
            start_time = time.time()

            while time.time() - start_time < self.timeout:
                if select.select([master_fd], [], [], 1.0)[0]:
                    try:
                        chunk = os.read(master_fd, 4096)
                        if not chunk:
                            break
                        output += chunk
                    except OSError:
                        break

                # Check if process finished
                if proc.poll() is not None:
                    # Read remaining output
                    while select.select([master_fd], [], [], 0.1)[0]:
                        try:
                            chunk = os.read(master_fd, 4096)
                            if not chunk:
                                break
                            output += chunk
                        except OSError:
                            break
                    break

            os.close(master_fd)

            # Check for timeout
            if proc.poll() is None:
                proc.kill()
                raise RuntimeError(f"Claude CLI timed out after {self.timeout} seconds")

            # Decode and clean output
            response = output.decode("utf-8", errors="replace")
            response = self._clean_terminal_output(response)

            if proc.returncode != 0:
                raise RuntimeError(f"Claude CLI error (code {proc.returncode}): {response[:500]}")

            return response

        except FileNotFoundError:
            raise RuntimeError(f"Claude CLI not found at {self.claude_cli_path}")

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a response from the model."""
        prompt, system_prompt = self._messages_to_prompt(messages)

        response = self._call_claude_cli(prompt, system_prompt)

        # Apply stop sequences if provided
        if stop:
            for stop_seq in stop:
                if stop_seq in response:
                    response = response[: response.index(stop_seq)]

        message = AIMessage(content=response)
        generation = ChatGeneration(message=message)

        return ChatResult(generations=[generation])

    def with_structured_output(
        self,
        schema: Any,
        method: str = "json_mode",
        **kwargs: Any,
    ) -> "StructuredClaudeCode":
        """Return a wrapper that parses output to a Pydantic model."""
        return StructuredClaudeCode(
            base_model=self,
            schema=schema,
        )


class StructuredClaudeCode:
    """Wrapper that adds structured output parsing to ChatClaudeCode."""

    def __init__(self, base_model: ChatClaudeCode, schema: Any):
        self.base_model = base_model
        self.schema = schema

    def _get_example_from_schema(self, schema: dict, defs: dict = None) -> dict:
        """Generate an example from a JSON schema."""
        if defs is None:
            defs = schema.get("$defs", {})

        # Handle $ref
        if "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            if ref_name in defs:
                return self._get_example_from_schema(defs[ref_name], defs)
            return {}

        schema_type = schema.get("type", "object")

        if schema_type == "object":
            example = {}
            properties = schema.get("properties", {})

            # Handle additionalProperties (for dict types)
            if "additionalProperties" in schema:
                add_props = schema["additionalProperties"]
                inner_example = self._get_example_from_schema(add_props, defs)
                example["TICKER"] = inner_example
                return example

            for prop_name, prop_schema in properties.items():
                example[prop_name] = self._get_value_for_schema(prop_schema, defs)
            return example

        return self._get_value_for_schema(schema, defs)

    def _get_value_for_schema(self, schema: dict, defs: dict) -> Any:
        """Get an example value for a schema."""
        # Handle $ref
        if "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            if ref_name in defs:
                return self._get_example_from_schema(defs[ref_name], defs)
            return None

        # Handle anyOf (for Optional types or Literal)
        if "anyOf" in schema:
            for option in schema["anyOf"]:
                if option.get("type") != "null":
                    return self._get_value_for_schema(option, defs)
            return None

        # Handle const (for Literal single values)
        if "const" in schema:
            return schema["const"]

        # Handle enum
        if "enum" in schema:
            return schema["enum"][0]

        prop_type = schema.get("type", "string")

        if prop_type == "string":
            desc = schema.get("description", "")
            return f"<{desc[:30]}>" if desc else "<string>"
        elif prop_type == "integer":
            return 50  # Use a mid-range default
        elif prop_type == "number":
            return 0.0
        elif prop_type == "boolean":
            return True
        elif prop_type == "object":
            return self._get_example_from_schema(schema, defs)
        elif prop_type == "array":
            items = schema.get("items", {})
            return [self._get_value_for_schema(items, defs)]

        return None

    def invoke(self, messages: Any, **kwargs) -> Any:
        """Invoke the model and parse the response."""
        # Add JSON instruction to the prompt
        if hasattr(messages, "to_messages"):
            messages = messages.to_messages()
        elif isinstance(messages, str):
            messages = [HumanMessage(content=messages)]
        elif not isinstance(messages, list):
            messages = list(messages)

        # Build example JSON
        example_str = ""
        if hasattr(self.schema, "model_json_schema"):
            schema = self.schema.model_json_schema()
            example = self._get_example_from_schema(schema)
            example_str = json.dumps(example, indent=2)

        # Add JSON instruction at the END of the last human message
        # This is more effective than a system message
        if messages:
            last_msg = messages[-1]
            if isinstance(last_msg, HumanMessage):
                messages = messages[:-1] + [HumanMessage(content=(f"{last_msg.content}\n\n" f"RESPOND WITH ONLY VALID JSON (no other text). Use this exact format:\n" f"{example_str}"))]
            else:
                messages = messages + [HumanMessage(content=(f"RESPOND WITH ONLY VALID JSON (no other text). Use this exact format:\n" f"{example_str}"))]

        # Get response
        result = self.base_model._generate(messages)
        response_text = result.generations[0].message.content

        # Extract JSON from response
        json_str = self._extract_json(response_text)

        # Parse into the schema
        try:
            data = json.loads(json_str)
            return self.schema(**data)
        except (json.JSONDecodeError, Exception) as e:
            # Try to fix common issues
            try:
                data = json.loads(json_str)

                # Check if any required top-level field is missing
                for field_name, field_info in self.schema.model_fields.items():
                    if field_name not in data and isinstance(data, dict):
                        # The model returned the inner dict without the wrapper
                        # Try wrapping it
                        wrapped = {field_name: data}
                        return self.schema(**wrapped)

                # Check for field name mismatches (e.g., "rationale" instead of "reasoning")
                field_aliases = {
                    "rationale": "reasoning",
                    "reason": "reasoning",
                    "explanation": "reasoning",
                }

                def fix_field_names(obj):
                    if isinstance(obj, dict):
                        fixed = {}
                        for k, v in obj.items():
                            new_key = field_aliases.get(k, k)
                            fixed[new_key] = fix_field_names(v)
                        return fixed
                    elif isinstance(obj, list):
                        return [fix_field_names(item) for item in obj]
                    return obj

                fixed_data = fix_field_names(data)
                return self.schema(**fixed_data)

            except Exception as fix_error:
                pass
            raise ValueError(f"Failed to parse response as {self.schema.__name__}: {e}\nResponse: {response_text}")

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text, handling code blocks."""
        text = text.strip()

        # Try to find JSON in code block
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end != -1:
                return text[start:end].strip()

        # Try to find JSON in generic code block
        if "```" in text:
            start = text.find("```") + 3
            # Skip language identifier if present
            newline = text.find("\n", start)
            if newline != -1:
                start = newline + 1
            end = text.find("```", start)
            if end != -1:
                return text[start:end].strip()

        # Try to find JSON object directly
        if text.startswith("{"):
            # Find matching closing brace
            depth = 0
            for i, c in enumerate(text):
                if c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        return text[: i + 1]

        # Return as-is and hope for the best
        return text


# Convenience function
def get_claude_code_model(
    model: str = "sonnet",
    timeout: int = 120,
    max_tokens: Optional[int] = None,
) -> ChatClaudeCode:
    """
    Get a ChatClaudeCode instance.

    Args:
        model: Model name ("opus", "sonnet", "haiku" or full name)
        timeout: Timeout in seconds
        max_tokens: Maximum output tokens

    Returns:
        ChatClaudeCode instance
    """
    return ChatClaudeCode(
        model=model,
        timeout=timeout,
        max_tokens=max_tokens,
    )
