"""Translation service with LLM native and Azure Translator fallback."""
from __future__ import annotations
from typing import Any, Dict, Optional, Tuple
import os
import httpx
import json

try:
    import openai
except Exception:
    openai = None


def translate_with_llm(text: str, target_language: str, source_language: Optional[str] = None) -> str:
    """Translate text using LLM (OpenAI GPT).
    
    Args:
        text: Text to translate
        target_language: Target language code (e.g., 'en', 'es', 'fr')
        source_language: Optional source language code
    
    Returns:
        Translated text
    """
    if not openai:
        raise ValueError("OpenAI client not available")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    
    client = openai.OpenAI(api_key=api_key)
    
    # Map language codes to full names for better LLM understanding
    language_map = {
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "ru": "Russian",
        "ar": "Arabic",
    }
    
    target_name = language_map.get(target_language.lower(), target_language)
    source_name = language_map.get(source_language.lower(), source_language) if source_language else "auto-detect"
    
    prompt = f"Translate the following text from {source_name} to {target_name}. Return only the translated text, no explanations:\n\n{text}"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use cheaper model for translation
            messages=[
                {"role": "system", "content": "You are a professional translator. Translate accurately and preserve meaning."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise ValueError(f"LLM translation failed: {str(e)}")


def translate_with_azure(
    text: str,
    target_language: str,
    source_language: Optional[str] = None,
) -> str:
    """Translate text using Azure Translator API.
    
    Args:
        text: Text to translate
        target_language: Target language code (e.g., 'en', 'es')
        source_language: Optional source language code
    
    Returns:
        Translated text
    """
    subscription_key = os.getenv("AZURE_TRANSLATOR_KEY")
    endpoint = os.getenv("AZURE_TRANSLATOR_ENDPOINT", "https://api.cognitive.microsofttranslator.com")
    region = os.getenv("AZURE_TRANSLATOR_REGION", "")
    
    if not subscription_key:
        raise ValueError("AZURE_TRANSLATOR_KEY not set")
    
    path = "/translate"
    constructed_url = endpoint + path
    
    params = {
        "api-version": "3.0",
        "to": target_language,
    }
    if source_language:
        params["from"] = source_language
    
    headers = {
        "Ocp-Apim-Subscription-Key": subscription_key,
        "Content-Type": "application/json",
    }
    if region:
        headers["Ocp-Apim-Subscription-Region"] = region
    
    body = [{"text": text}]
    
    try:
        response = httpx.post(
            constructed_url,
            params=params,
            headers=headers,
            json=body,
            timeout=10.0,
        )
        response.raise_for_status()
        result = response.json()
        return result[0]["translations"][0]["text"]
    except Exception as e:
        raise ValueError(f"Azure translation failed: {str(e)}")


def translate(
    text: str,
    target_language: str,
    source_language: Optional[str] = None,
    provider: str = "llm",
    fallback: str = "azure",
    user_settings: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str]:
    """Translate text using specified provider with fallback.
    
    Args:
        text: Text to translate
        target_language: Target language code
        source_language: Optional source language code
        provider: Primary provider ("llm" or "azure")
        fallback: Fallback provider if primary fails
        user_settings: Optional user settings for translation rules
    
    Returns:
        Tuple of (translated_text, provider_used)
    """
    # Try primary provider first
    try:
        if provider == "llm":
            translated = translate_with_llm(text, target_language, source_language)
            return (translated, "llm")
        elif provider == "azure":
            translated = translate_with_azure(text, target_language, source_language)
            return (translated, "azure")
        else:
            raise ValueError(f"Unknown provider: {provider}")
    except Exception:
        # Fallback to secondary provider
        try:
            if fallback == "azure":
                translated = translate_with_azure(text, target_language, source_language)
                return (translated, "azure")
            elif fallback == "llm":
                translated = translate_with_llm(text, target_language, source_language)
                return (translated, "llm")
            else:
                raise ValueError(f"Unknown fallback: {fallback}")
        except Exception as e:
            raise ValueError(f"Both translation providers failed. Last error: {str(e)}")


def should_translate(
    direction: str,
    is_internal: bool,
    user_settings: Dict[str, Any],
) -> Tuple[bool, bool]:
    """Determine if translation should occur based on rules.
    
    Args:
        direction: "inbound" or "outbound"
        is_internal: Whether the communication is internal (same organization)
        user_settings: User translation settings
    
    Returns:
        Tuple of (should_translate, requires_prompt)
    """
    translation_settings = user_settings.get("translation", {})
    rules = translation_settings.get("rules", {})
    
    if is_internal:
        rule = rules.get("internal", "off")
    else:
        rule = rules.get("external", "off")
    
    # Also check direction-specific rule if exists
    direction_rule = rules.get(direction, rule)
    
    if direction_rule == "off":
        return (False, False)
    elif direction_rule == "auto":
        return (True, False)
    elif direction_rule == "prompt":
        return (True, True)
    else:
        # Default to auto if rule is unclear
        return (True, False)

