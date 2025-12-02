from fastapi import APIRouter, HTTPException, Request
from typing import List

import os
import sys

from fastapi.responses import StreamingResponse
from httpcore import request
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.agent_service import TaleMachineAgentService

messages_router = APIRouter(prefix="/messages", tags=["messages"])

@messages_router.post("/send")
async def send_message(messages: List[dict], story_name: str, thread_id: str, story_id: int,  request: Request):
    """Send a message"""
    async def generate():
        try:
            async for response in TaleMachineAgentService.run(messages, story_name, thread_id, story_id, request.app.state.db):
                yield response
        except Exception as e:
            yield f"Error: {str(e)}"
    return StreamingResponse(generate(), media_type="text/event-stream")

@messages_router.post("/resume_after_interrupt")
async def resume_after_interrupt(thread_id: str, approval: bool, story_name: str, story_id: int, request: Request):
    """Resume after an interrupt with user approval or denial"""
    async def generate():
        try:
            async for response in TaleMachineAgentService.resume_after_interrupt(thread_id, approval, story_name, story_id, request.app.state.db):
                yield response
        except Exception as e:
            yield f"Error: {str(e)}"
    return StreamingResponse(generate(), media_type="text/event-stream")