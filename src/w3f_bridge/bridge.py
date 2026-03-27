"""
W3F Bridge — ServerBridge (per-connection API).

Each WebSocket connection gets its own ServerBridge instance.
Handlers use this to send commands, read values, and listen to events.
"""

from __future__ import annotations

import json
import asyncio
import logging
from typing import Any, Callable, Awaitable

from .types import BridgeEvent, BridgeCommand

logger = logging.getLogger("w3f_bridge")

# Type for event callbacks — can be sync or async
EventCallback = Callable[["ServerBridge", BridgeEvent], Any]


class ServerBridge:
    """Per-connection bridge API — mirrors BridgeAPI from @w3f/shared."""

    def __init__(self, websocket: Any) -> None:
        self._ws = websocket
        self._listeners: dict[str, list[EventCallback]] = {}
        self._values: dict[str, Any] = {}
        self._state: dict[str, Any] = {}
        self._closed = False

    # ── Listener management ───────────────────────────────────────

    @staticmethod
    def _key(event_type: str, bind_id: str) -> str:
        return f"{event_type}::{bind_id}"

    def on(self, event_type: str, bind_id: str, callback: EventCallback) -> Callable[[], None]:
        """Subscribe to events. Returns an unsubscribe function."""
        key = self._key(event_type, bind_id)
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(callback)

        def unsub() -> None:
            try:
                self._listeners[key].remove(callback)
            except (ValueError, KeyError):
                pass

        return unsub

    def off(self, event_type: str, bind_id: str, callback: EventCallback) -> None:
        """Remove a specific listener."""
        key = self._key(event_type, bind_id)
        try:
            self._listeners[key].remove(callback)
        except (ValueError, KeyError):
            pass

    def once(self, event_type: str, bind_id: str, callback: EventCallback) -> Callable[[], None]:
        """Subscribe to a single event, then auto-unsubscribe."""
        unsub: Callable[[], None] | None = None

        async def wrapper(bridge: ServerBridge, event: BridgeEvent) -> None:
            if unsub:
                unsub()
            result = callback(bridge, event)
            if asyncio.iscoroutine(result):
                await result

        unsub = self.on(event_type, bind_id, wrapper)
        return unsub

    # ── Dispatch incoming events to listeners ─────────────────────

    async def dispatch(self, event: BridgeEvent) -> None:
        """Route an incoming event to matching listeners."""
        # Exact match: event_type::bind_id
        exact_key = self._key(event.type, event.source)
        # Wildcard: event_type::*
        wild_key = self._key(event.type, "*")
        # Global wildcard: *::*
        global_key = self._key("*", "*")

        for key in (exact_key, wild_key, global_key):
            for cb in list(self._listeners.get(key, [])):
                try:
                    result = cb(self, event)
                    if asyncio.iscoroutine(result) or asyncio.isfuture(result):
                        await result
                except Exception:
                    logger.exception(f"Error in listener for {key}")

    # ── Send commands to UI ───────────────────────────────────────

    async def _send(self, msg: dict[str, Any]) -> None:
        """Send a raw JSON message to the client."""
        if self._closed:
            return
        try:
            await self._ws.send(json.dumps(msg))
        except Exception:
            logger.debug("Failed to send message (connection closed?)")

    async def emit(self, command: BridgeCommand | dict[str, Any]) -> None:
        """Send a BridgeCommand to the UI."""
        if isinstance(command, BridgeCommand):
            cmd_dict = command.to_dict()
        else:
            cmd_dict = command
        await self._send({"type": "command", "command": cmd_dict})

    async def set(self, bind_id: str, value: Any) -> None:
        """Set a component's value (sends a 'set' command)."""
        self._values[bind_id] = value
        await self.emit(BridgeCommand(
            action="set",
            target=bind_id,
            payload={"value": value},
        ))

    async def show(self, bind_id: str) -> None:
        """Show a hidden component."""
        await self.emit(BridgeCommand(action="show", target=bind_id))

    async def hide(self, bind_id: str) -> None:
        """Hide a component."""
        await self.emit(BridgeCommand(action="hide", target=bind_id))

    async def enable(self, bind_id: str) -> None:
        """Enable a disabled component."""
        await self.emit(BridgeCommand(action="enable", target=bind_id))

    async def disable(self, bind_id: str) -> None:
        """Disable a component."""
        await self.emit(BridgeCommand(action="disable", target=bind_id))

    async def toggle(self, bind_id: str) -> None:
        """Toggle component visibility."""
        await self.emit(BridgeCommand(action="toggle", target=bind_id))

    async def style(self, bind_id: str, styles: dict[str, str]) -> None:
        """Apply inline styles to a component."""
        await self.emit(BridgeCommand(action="style", target=bind_id, payload=styles))

    async def add_class(self, bind_id: str, class_name: str) -> None:
        """Add a CSS class to a component."""
        await self.emit(BridgeCommand(action="addClass", target=bind_id, payload={"class": class_name}))

    async def remove_class(self, bind_id: str, class_name: str) -> None:
        """Remove a CSS class from a component."""
        await self.emit(BridgeCommand(action="removeClass", target=bind_id, payload={"class": class_name}))

    async def set_state(self, data: dict[str, Any]) -> None:
        """Update shared state (broadcast to all listeners)."""
        self._state.update(data)
        await self.emit(BridgeCommand(action="setState", target="*", payload=data))

    # ── Value / State access ──────────────────────────────────────

    def get(self, bind_id: str) -> Any:
        """Get last known value for a component."""
        return self._values.get(bind_id)

    def get_state(self) -> dict[str, Any]:
        """Get the full shared state."""
        return dict(self._state)

    def get_state_key(self, key: str) -> Any:
        """Get a specific key from shared state."""
        return self._state.get(key)

    # ── Lifecycle ─────────────────────────────────────────────────

    def destroy(self) -> None:
        """Clean up resources."""
        self._closed = True
        self._listeners.clear()
        self._values.clear()
        self._state.clear()
