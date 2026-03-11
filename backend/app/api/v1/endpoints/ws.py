from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ....services.ws_manager import manager

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; we only send messages, no need to receive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
