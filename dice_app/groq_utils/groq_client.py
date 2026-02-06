#!/usr/bin/env python3
"""
Groq Cloud API Client for Session Manager AI Agent

Features:
- OpenAI-compatible API format
- Automatic model fallback on rate limit
- Token usage tracking
- Error handling

Usage:
    from dice_app.utils.groq_client import call_groq_api, get_groq_config

    config = get_groq_config()
    response = call_groq_api(messages, config)
"""

import streamlit as st
import requests
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import time


class GroqModel(Enum):
    """Groq Cloud 免费 models"""

    LLAMA_3_3_70B = "llama-3.3-70b-versatile"
    MIXTRAL_8X7B = "mixtral-8x7b-32768"
    GEMMA_7B = "gemma-7b-it"
    LLAMA_3_70B = "llama-3-70b-8192"


@dataclass
class GroqConfig:
    """Groq API configuration"""

    api_url: str = "https://api.groq.com/openai/v1/chat/completions"
    api_key: str = ""
    primary_model: str = "llama-3.3-70b-versatile"
    secondary_model: str = "mixtral-8x7b-32768"
    fallback_model: str = "gemma-7b-it"
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: int = 60


@dataclass
class GroqResponse:
    """Groq API response wrapper"""

    content: str
    model: str
    tokens_used: int
    success: bool
    error: Optional[str] = None


def get_groq_config() -> GroqConfig:
    """Get Groq configuration from Streamlit secrets"""
    return GroqConfig(
        api_key=st.secrets.get("GROQ_API_KEY", ""),
        primary_model=st.secrets.get("GROQ_MODEL_PRIMARY", "llama-3.3-70b-versatile"),
        secondary_model=st.secrets.get("GROQ_MODEL_SECONDARY", "mixtral-8x7b-32768"),
        fallback_model=st.secrets.get("GROQ_MODEL_FALLBACK", "gemma-7b-it"),
        max_tokens=st.secrets.get("GROQ_MAX_TOKENS", 2000),
        temperature=st.secrets.get("GROQ_TEMPERATURE", 0.7),
    )


def _check_api_key(config: GroqConfig) -> tuple[bool, str]:
    """Validate API key"""
    if not config.api_key:
        return False, "GROQ_API_KEY not configured"
    if config.api_key == "YOUR_GROQ_API_KEY":
        return False, "Please set your Groq API key in secrets.toml"
    if not config.api_key.startswith("gsk_"):
        return False, "Invalid API key format (must start with 'gsk_')"
    return True, ""


def _build_headers(config: GroqConfig) -> Dict[str, str]:
    """Build request headers"""
    return {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }


def _build_payload(
    config: GroqConfig, messages: List[Dict[str, str]]
) -> Dict[str, Any]:
    """Build request payload"""
    return {
        "model": config.primary_model,
        "messages": messages,
        "max_tokens": config.max_tokens,
        "temperature": config.temperature,
    }


def _handle_rate_limit(
    config: GroqConfig, messages: List[Dict[str, str]], timeout: int
) -> GroqResponse:
    """
    Handle rate limit by trying fallback models
    Returns: GroqResponse
    """
    models_to_try = [
        config.primary_model,
        config.secondary_model,
        config.fallback_model,
    ]

    headers = _build_headers(config)

    for i, model in enumerate(models_to_try):
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
        }

        try:
            response = requests.post(
                config.api_url, headers=headers, json=payload, timeout=timeout
            )

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", 0)
                return GroqResponse(
                    content=content, model=model, tokens_used=tokens, success=True
                )

            elif response.status_code == 429:
                # Rate limited, try next model
                if i < len(models_to_try) - 1:
                    continue
                else:
                    return GroqResponse(
                        content="",
                        model="",
                        tokens_used=0,
                        success=False,
                        error="All models rate limited. Please try again later.",
                    )

            else:
                error_msg = f"API Error: {response.status_code}"
                return GroqResponse(
                    content="",
                    model=model,
                    tokens_used=0,
                    success=False,
                    error=error_msg,
                )

        except requests.exceptions.Timeout:
            return GroqResponse(
                content="",
                model=model,
                tokens_used=0,
                success=False,
                error=f"Request timeout after {timeout}s",
            )
        except Exception as e:
            if i < len(models_to_try) - 1:
                continue
            return GroqResponse(
                content="",
                model="",
                tokens_used=0,
                success=False,
                error=f"Request failed: {str(e)}",
            )

    return GroqResponse(
        content="", model="", tokens_used=0, success=False, error="All models failed"
    )


def call_groq_api(
    messages: List[Dict[str, str]],
    config: Optional[GroqConfig] = None,
    timeout: int = 60,
) -> GroqResponse:
    """
    Call Groq API with automatic fallback

    Args:
        messages: List of message dicts with 'role' and 'content'
        config: GroqConfig (optional, uses defaults if not provided)
        timeout: Request timeout in seconds

    Returns:
        GroqResponse with content, model, tokens_used, success, error
    """
    if config is None:
        config = get_groq_config()

    # Validate API key
    valid, error_msg = _check_api_key(config)
    if not valid:
        return GroqResponse(
            content="", model="", tokens_used=0, success=False, error=error_msg
        )

    # Handle rate limit with fallback
    return _handle_rate_limit(config, messages, timeout)


def test_groq_connection() -> tuple[bool, str]:
    """
    Test Groq API connection

    Returns:
        (success, message)
    """
    config = get_groq_config()

    valid, error_msg = _check_api_key(config)
    if not valid:
        return False, error_msg

    # Simple test request
    test_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'hello' in Korean."},
    ]

    response = call_groq_api(test_messages, config, timeout=30)

    if response.success:
        return (
            True,
            f"Connected! Model: {response.model}, Response: {response.content[:50]}...",
        )
    else:
        return False, response.error or "Unknown error"


if __name__ == "__main__":
    # Test connection when run directly
    print("Testing Groq API connection...")
    success, message = test_groq_connection()

    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
        print("\nTo configure, add to .streamlit/secrets.toml:")
        print('GROQ_API_KEY = "your_api_key_here"')
