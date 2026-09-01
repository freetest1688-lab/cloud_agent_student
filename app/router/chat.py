from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from schemas.chat import ChatRequest
from service.chat_service import stream_chat

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Handle a multi-agent chat request and stream the response via SSE.

    If the L1 semantic cache hits, the cached answer is returned directly;
    otherwise the request enters the agent graph workflow.
    """
    return StreamingResponse(
        stream_chat(request.query, request.user_id, request.session_id),
        media_type="text/event-stream"
    )
