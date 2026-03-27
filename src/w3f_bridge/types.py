"""
W3F Bridge — Type definitions.

Mirrors the TypeScript types from @w3f/shared/bridge.types.ts.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any


# ── Event types (UI → Server) ────────────────────────────────────────

EVENT_TYPES = frozenset({
    "click", "change", "submit", "focus", "blur",
    "hover", "leave", "keydown", "scroll",
    "mount", "unmount", "custom",
})

# ── Command actions (Server → UI) ────────────────────────────────────

COMMAND_ACTIONS = frozenset({
    "set", "get", "show", "hide",
    "enable", "disable", "toggle",
    "style", "addClass", "removeClass", "setProps",
    "navigate", "focus", "scrollTo",
    "emit", "setState",
})


@dataclass
class BridgeEvent:
    """An event dispatched from the UI to the server."""

    type: str
    source: str
    timestamp: float = 0.0
    payload: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"type": self.type, "source": self.source, "timestamp": self.timestamp}
        if self.payload is not None:
            d["payload"] = self.payload
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BridgeEvent:
        return cls(
            type=data.get("type", "custom"),
            source=data.get("source", ""),
            timestamp=data.get("timestamp", 0.0),
            payload=data.get("payload"),
        )


@dataclass
class BridgeCommand:
    """A command sent from the server to the UI."""

    action: str
    target: str
    payload: dict[str, Any] | None = None
    source: str = "server"

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"action": self.action, "target": self.target, "source": self.source}
        if self.payload is not None:
            d["payload"] = self.payload
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BridgeCommand:
        return cls(
            action=data.get("action", "set"),
            target=data.get("target", "*"),
            payload=data.get("payload"),
            source=data.get("source", "server"),
        )
