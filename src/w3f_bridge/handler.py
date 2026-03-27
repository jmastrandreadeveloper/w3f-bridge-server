"""
W3F Bridge — Handler base class and @on decorator.

Handlers encapsulate business logic that responds to UI events.
Each WebSocket connection gets its own handler instance.
"""

from __future__ import annotations

from typing import Any

from .bridge import ServerBridge, BridgeEvent


def on(event_type: str, bind_id: str):
    """
    Decorator to mark a method as a bridge event handler.

    Usage:
        @on("click", "my-button")
        async def handle_click(self, bridge, event):
            await bridge.set("label", "Clicked!")
    """

    def decorator(fn):
        # Store metadata on the function for the server to discover
        if not hasattr(fn, "_bridge_bindings"):
            fn._bridge_bindings = []
        fn._bridge_bindings.append((event_type, bind_id))
        return fn

    return decorator


class Handler:
    """
    Base class for bridge handlers.

    Subclass and override on_connect / on_disconnect.
    Use @on() to register event handlers declaratively.

    Attributes:
        id:   Unique identifier for this handler (used in protocol 'hello')
        name: Human-readable name (shown in Bridge Inspector)
    """

    id: str = "unnamed"
    name: str = "Unnamed Handler"

    async def on_connect(self, bridge: ServerBridge) -> None:
        """Called when a client connects. Override to set initial state."""
        pass

    async def on_disconnect(self, bridge: ServerBridge) -> None:
        """Called when a client disconnects. Override for cleanup."""
        pass
