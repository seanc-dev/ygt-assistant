from __future__ import annotations
from typing import Any, Dict
from fastapi import APIRouter
from services.calendar import CalendarService

router = APIRouter()

@router.post("/calendar/plan-today")
async def calendar_plan_today() -> Dict[str, Any]:
    c = CalendarService()
    plan = c.list_today()
    card_text = "Plan for Today\n" + "\n".join([f"• {i.get('time','10:00')} {i.get('title','Focus block')}" for i in plan])
    return {"plan": plan, "card": card_text}

@router.post("/calendar/reschedule")
async def calendar_reschedule(body: Dict[str, Any]) -> Dict[str, Any]:
    c = CalendarService()
    return c.create_or_update(body)
