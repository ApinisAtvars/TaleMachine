from fastapi import APIRouter, HTTPException
from typing import List

import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.services.agent_service import TaleMachineAgentService

messages_router = APIRouter(prefix="/messages", tags=["messages"])

@messages_router.post("/send")
async def send_message(messages: List[dict], story_name: str, thread_id: str, story_id: int):
    """Send a message"""
    try:
        async for response in TaleMachineAgentService.run(messages, story_name, thread_id, story_id):
            yield response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@messages_router.post("/resume_after_interrupt")
async def resume_after_interrupt(thread_id: str, approval: bool, story_name: str, story_id: int):
    """Resume after an interrupt with user approval or denial"""
    try:
        async for response in TaleMachineAgentService.resume_after_interrupt(thread_id, approval, story_name, story_id):
            yield response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))