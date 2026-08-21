"""
WebSocket connection manager for broadcasting real-time scan events.
"""
import json
from typing import Dict, List, Any
from fastapi import WebSocket
import structlog

logger = structlog.get_logger(__name__)


class WebSocketManager:
    """Manages WebSocket connections, organized by project/scan ID."""

    def __init__(self):
        # Map scan_id -> list of connected WebSockets
        self._connections: Dict[str, List[WebSocket]] = {}
        # Global subscribers (receive all events)
        self._global: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, channel: str = "global"):
        await websocket.accept()
        if channel == "global":
            self._global.append(websocket)
        else:
            self._connections.setdefault(channel, []).append(websocket)
        logger.info("ws_client_connected", channel=channel)

    def disconnect(self, websocket: WebSocket, channel: str = "global"):
        if channel == "global":
            self._global = [ws for ws in self._global if ws != websocket]
        else:
            self._connections[channel] = [
                ws for ws in self._connections.get(channel, []) if ws != websocket
            ]
        logger.info("ws_client_disconnected", channel=channel)

    async def broadcast(self, event: str, data: Any, channel: str = "global"):
        """Broadcast an event to all subscribers on a channel."""
        message = json.dumps({"event": event, "data": data})
        targets = self._global.copy()
        if channel != "global":
            targets += self._connections.get(channel, [])

        dead = []
        for ws in targets:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)

        # Clean up dead connections
        for ws in dead:
            if ws in self._global:
                self._global.remove(ws)
            for ch_list in self._connections.values():
                if ws in ch_list:
                    ch_list.remove(ws)

    async def send_to_channel(self, channel: str, event: str, data: Any):
        await self.broadcast(event, data, channel)


ws_manager = WebSocketManager()
