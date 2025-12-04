from fastapi import APIRouter, HTTPException, Request
from typing import List

import os
import sys

from fastapi.responses import StreamingResponse
from httpcore import request
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.agent_service import TaleMachineAgentService
from models.MessageRequest import MessageRequest, ResumeMessageRequest

messages_router = APIRouter(prefix="/messages", tags=["messages"])

@messages_router.post("/send")
async def send_message(message_request: MessageRequest, request: Request):
    """Send a message"""
    async def generate():
        try:
            async for response in TaleMachineAgentService.run(message_request.messages, message_request.story_name, message_request.thread_id, message_request.story_id, request.app.state.db):
                yield response
        except Exception as e:
            yield f"Error: {str(e)}"
    return StreamingResponse(generate(), media_type="text/event-stream")

@messages_router.post("/resume_after_interrupt")
async def resume_after_interrupt(resume_request: ResumeMessageRequest, request: Request):
    """Resume after an interrupt with user approval or denial"""
    async def generate():
        try:
            async for response in TaleMachineAgentService.resume_after_interrupt(resume_request.thread_id, resume_request.approval, resume_request.story_name, resume_request.story_id, request.app.state.db, resume_request.chapter_id):
                yield response
        except Exception as e:
            yield f"Error: {str(e)}"
    return StreamingResponse(generate(), media_type="text/event-stream")