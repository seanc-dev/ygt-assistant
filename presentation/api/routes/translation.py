"""Translation endpoints."""
from __future__ import annotations
from typing import Any, Dict, Optional
from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel, Field
from presentation.api.routes.queue import _get_user_id
from presentation.api.repos import user_settings
from services.translation import translate, should_translate

router = APIRouter()


class TranslateRequest(BaseModel):
    text: str = Field(..., description="Text to translate")
    target_language: str = Field(..., description="Target language code (e.g., 'en', 'es')")
    source_language: Optional[str] = Field(None, description="Source language code (optional)")
    direction: str = Field(..., description="inbound or outbound")
    is_internal: bool = Field(default=False, description="Whether communication is internal")


@router.post("/api/translation/translate")
async def translate_text(
    body: TranslateRequest,
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Translate text using LLM native with Azure fallback.
    
    Respects user translation rules:
    - auto: Translate automatically
    - prompt: Require user confirmation
    - off: No translation
    
    Returns translated text and provider used.
    """
    settings = user_settings.get_settings(user_id)
    
    # Check if translation should occur
    should, requires_prompt = should_translate(
        body.direction,
        body.is_internal,
        settings,
    )
    
    if not should:
        return {
            "ok": True,
            "translated": body.text,
            "provider": "none",
            "reason": "Translation disabled by user settings",
        }
    
    if requires_prompt:
        # In future, this would trigger a prompt UI
        # For now, return the original text with a flag
        return {
            "ok": True,
            "translated": body.text,
            "provider": "none",
            "requires_prompt": True,
            "reason": "Translation requires user confirmation",
        }
    
    # Get provider settings
    translation_settings = settings.get("translation", {})
    provider = translation_settings.get("default", "llm")
    fallback = translation_settings.get("fallback", "azure")
    
    try:
        translated_text, provider_used = translate(
            body.text,
            body.target_language,
            body.source_language,
            provider=provider,
            fallback=fallback,
            user_settings=settings,
        )
        
        return {
            "ok": True,
            "translated": translated_text,
            "provider": provider_used,
            "original": body.text,
            "target_language": body.target_language,
            "source_language": body.source_language or "auto",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@router.post("/api/translation/check")
async def check_translation_needed(
    body: Dict[str, Any],
    request: Request,
    user_id: str = Depends(_get_user_id),
) -> Dict[str, Any]:
    """Check if translation is needed based on user rules.
    
    Returns whether translation should occur and if it requires prompt.
    """
    settings = user_settings.get_settings(user_id)
    
    direction = body.get("direction", "outbound")
    is_internal = body.get("is_internal", False)
    
    should, requires_prompt = should_translate(
        direction,
        is_internal,
        settings,
    )
    
    return {
        "ok": True,
        "should_translate": should,
        "requires_prompt": requires_prompt,
    }

