"""
WebSocket endpoint for real-time scan event streaming.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.websocket_manager import ws_manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_global(websocket: WebSocket):
    """Global WebSocket: receives all scan events."""
    await ws_manager.connect(websocket, "global")
    try:
        while True:
            # Keep connection alive; messages are server-push only
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, "global")


@router.websocket("/ws/scans/{scan_id}")
async def websocket_scan(scan_id: str, websocket: WebSocket):
    """Per-scan WebSocket: receives events for a specific scan."""
    await ws_manager.connect(websocket, f"scan:{scan_id}")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, f"scan:{scan_id}")
