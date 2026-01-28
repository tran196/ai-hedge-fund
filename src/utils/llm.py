"""Helper functions for LLM

This module provides LLM calling utilities with support for:
1. Claude Code CLI (preferred - uses user's Claude subscription)
2. Anthropic API (fallback when API key provided)
3. OpenAI and other providers via LangChain
"""

import json
import os
from pydantic import BaseModel
from src.llm.models import get_model, get_model_info, ModelProvider
from src.utils.progress import progress
from src.graph.state import AgentState


def call_llm(
    prompt: any,
    pydantic_model: type[BaseModel],
    agent_name: str | None = None,
    state: AgentState | None = None,
    max_retries: int = 3,
    default_factory=None,
) -> BaseModel:
    """
    Makes an LLM call with retry logic.
    
    Priority order:
    1. Claude Code CLI (if available and provider is Anthropic/Claude/ClaudeCode)
    2. Anthropic API (if ANTHROPIC_API_KEY is set)
    3. Other providers via LangChain

    Args:
        prompt: The prompt to send to the LLM
        pydantic_model: The Pydantic model class to structure the output
        agent_name: Optional name of the agent for progress updates and model config extraction
        state: Optional state object to extract agent-specific model configuration
        max_retries: Maximum number of retries (default: 3)
        default_factory: Optional factory function to create default response on failure

    Returns:
        An instance of the specified Pydantic model
    """
    
    # Extract model configuration
    if state and agent_name:
        model_name, model_provider = get_agent_model_config(state, agent_name)
    else:
        model_name, model_provider = get_default_model(agent_name)
    
    # Check if we should use Claude Code CLI
    use_claude_code = should_use_claude_code(model_provider)
    
    if use_claude_code:
        return call_llm_claude_code(
            prompt=prompt,
            pydantic_model=pydantic_model,
            agent_name=agent_name,
            model_name=model_name,
            max_retries=max_retries,
            default_factory=default_factory,
        )
    else:
        return call_llm_langchain(
            prompt=prompt,
            pydantic_model=pydantic_model,
            agent_name=agent_name,
            state=state,
            model_name=model_name,
            model_provider=model_provider,
            max_retries=max_retries,
            default_factory=default_factory,
        )


def should_use_claude_code(model_provider: str) -> bool:
    """
    Determine if Claude Code CLI should be used.
    
    Returns True if:
    1. Provider is Claude/Anthropic/ClaudeCode AND
    2. Claude Code CLI is available AND
    3. No ANTHROPIC_API_KEY is set (prefer CLI over API)
    """
    from src.llm.claude_code import is_claude_code_available
    
    provider_upper = str(model_provider).upper()
    is_claude_provider = provider_upper in ("ANTHROPIC", "CLAUDE", "CLAUDECODE", "CLAUDE_CODE")
    
    if not is_claude_provider:
        return False
    
    if not is_claude_code_available():
        return False
    
    # If API key is set, user might want API instead of CLI
    # But we prefer CLI for Pro subscription usage
    # Only use API if explicitly set and CLI is not preferred
    api_key = os.getenv("ANTHROPIC_API_KEY")
    use_api_key = os.getenv("USE_ANTHROPIC_API", "").lower() == "true"
    
    if api_key and use_api_key:
        return False
    
    return True


def call_llm_claude_code(
    prompt: any,
    pydantic_model: type[BaseModel],
    agent_name: str | None,
    model_name: str,
    max_retries: int,
    default_factory=None,
) -> BaseModel:
    """Call LLM using Claude Code CLI."""
    from src.llm.claude_code import (
        call_claude_code_structured,
        get_model_for_agent,
        create_default_response,
    )
    
    # Get appropriate model tier for agent
    model_tier = get_model_for_agent(agent_name) if agent_name else "sonnet"
    
    # Extract the text content from the prompt
    if hasattr(prompt, 'messages'):
        # LangChain ChatPromptValue
        messages = prompt.messages
        prompt_text = "\n\n".join([
            f"{getattr(m, 'type', 'user').upper()}: {m.content}" 
            for m in messages
        ])
    elif hasattr(prompt, 'to_string'):
        prompt_text = prompt.to_string()
    elif isinstance(prompt, str):
        prompt_text = prompt
    else:
        prompt_text = str(prompt)
    
    if agent_name:
        progress.update_status(agent_name, None, f"Calling Claude ({model_tier})")
    
    try:
        result = call_claude_code_structured(
            prompt=prompt_text,
            pydantic_model=pydantic_model,
            model=model_tier,
            max_retries=max_retries,
        )
        return result
    except Exception as e:
        if agent_name:
            progress.update_status(agent_name, None, f"Error: {str(e)[:50]}")
        print(f"Error in Claude Code call: {e}")
        
        if default_factory:
            return default_factory()
        return create_default_response(pydantic_model, str(e))


def call_llm_langchain(
    prompt: any,
    pydantic_model: type[BaseModel],
    agent_name: str | None,
    state: AgentState | None,
    model_name: str,
    model_provider: str,
    max_retries: int,
    default_factory=None,
) -> BaseModel:
    """Call LLM using LangChain (for Anthropic API, OpenAI, etc.)."""
    
    # Extract API keys from state if available
    api_keys = None
    if state:
        request = state.get("metadata", {}).get("request")
        if request and hasattr(request, 'api_keys'):
            api_keys = request.api_keys

    model_info = get_model_info(model_name, model_provider)
    llm = get_model(model_name, model_provider, api_keys)

    # For non-JSON support models, we can use structured output
    if not (model_info and not model_info.has_json_mode()):
        llm = llm.with_structured_output(
            pydantic_model,
            method="json_mode",
        )

    # Call the LLM with retries
    for attempt in range(max_retries):
        try:
            if agent_name:
                progress.update_status(agent_name, None, f"Calling {model_provider}")
            
            # Call the LLM
            result = llm.invoke(prompt)

            # For non-JSON support models, we need to extract and parse the JSON manually
            if model_info and not model_info.has_json_mode():
                parsed_result = extract_json_from_response(result.content)
                if parsed_result:
                    return pydantic_model(**parsed_result)
            else:
                return result

        except Exception as e:
            if agent_name:
                progress.update_status(agent_name, None, f"Error - retry {attempt + 1}/{max_retries}")

            if attempt == max_retries - 1:
                print(f"Error in LLM call after {max_retries} attempts: {e}")
                if default_factory:
                    return default_factory()
                return create_default_response(pydantic_model)

    return create_default_response(pydantic_model)


def get_default_model(agent_name: str | None = None) -> tuple[str, str]:
    """
    Get the default model based on available providers.
    
    Priority:
    1. Claude Code CLI (if available)
    2. Anthropic API (if ANTHROPIC_API_KEY is set)
    3. OpenAI (fallback)
    """
    from src.llm.claude_code import is_claude_code_available, get_model_for_agent
    
    # Check Claude Code CLI first
    if is_claude_code_available():
        model_tier = get_model_for_agent(agent_name) if agent_name else "sonnet"
        return model_tier, "ClaudeCode"
    
    # Check Anthropic API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key and api_key != "your-anthropic-api-key":
        from src.llm.claude_config import get_claude_model_for_agent
        if agent_name:
            return get_claude_model_for_agent(agent_name)
        return "claude-sonnet-4-20250514", "Anthropic"
    
    # Fall back to OpenAI
    return "gpt-4.1", "OpenAI"


def get_agent_model_config(state, agent_name):
    """
    Get model configuration for a specific agent from the state.
    Falls back to global model configuration if agent-specific config is not available.
    When using Claude, automatically selects the appropriate tier for each agent.
    """
    from src.llm.claude_code import is_claude_code_available, get_model_for_agent
    
    request = state.get("metadata", {}).get("request")
    
    if request and hasattr(request, 'get_agent_model_config'):
        model_name, model_provider = request.get_agent_model_config(agent_name)
        if model_name and model_provider:
            return model_name, model_provider.value if hasattr(model_provider, 'value') else str(model_provider)
    
    # Fall back to global configuration from metadata
    model_name = state.get("metadata", {}).get("model_name")
    model_provider = state.get("metadata", {}).get("model_provider")
    
    # Normalize provider
    provider_str = str(model_provider).upper() if model_provider else ""
    
    # If using Claude (via CLI or API) and we have an agent name, use tiered selection
    if provider_str in ("ANTHROPIC", "CLAUDE", "CLAUDECODE", "CLAUDE_CODE"):
        if is_claude_code_available():
            model_tier = get_model_for_agent(agent_name)
            return model_tier, "ClaudeCode"
        else:
            from src.llm.claude_config import get_claude_model_for_agent
            return get_claude_model_for_agent(agent_name)
    
    # Use explicit config if provided
    if model_name and model_provider:
        if hasattr(model_provider, 'value'):
            model_provider = model_provider.value
        return model_name, model_provider
    
    # Fall back to defaults
    return get_default_model(agent_name)


def create_default_response(model_class: type[BaseModel]) -> BaseModel:
    """Creates a safe default response based on the model's fields."""
    default_values = {}
    for field_name, field in model_class.model_fields.items():
        if field.annotation == str:
            default_values[field_name] = "Error in analysis, using default"
        elif field.annotation == float:
            default_values[field_name] = 0.0
        elif field.annotation == int:
            default_values[field_name] = 0
        elif hasattr(field.annotation, "__origin__") and field.annotation.__origin__ == dict:
            default_values[field_name] = {}
        else:
            if hasattr(field.annotation, "__args__"):
                default_values[field_name] = field.annotation.__args__[0]
            else:
                default_values[field_name] = None

    return model_class(**default_values)


def extract_json_from_response(content: str) -> dict | None:
    """Extracts JSON from markdown-formatted response."""
    try:
        json_start = content.find("```json")
        if json_start != -1:
            json_text = content[json_start + 7 :]
            json_end = json_text.find("```")
            if json_end != -1:
                json_text = json_text[:json_end].strip()
                return json.loads(json_text)
    except Exception as e:
        print(f"Error extracting JSON from response: {e}")
    return None
