"""
Counter handler — increment / decrement / reset.

PageBuilder setup:
  - Button → bindId: "counter-inc"    (label: "+")
  - Button → bindId: "counter-dec"    (label: "−")
  - Button → bindId: "counter-reset"  (label: "Reset")
  - Chip   → bindId: "counter-display"
  - Bridge URL: ws://localhost:8767
"""

from __future__ import annotations

from ..handler import Handler, on
from ..bridge import ServerBridge, BridgeEvent


class CounterHandler(Handler):
    id = "counter"
    name = "Counter"

    def __init__(self):
        self.count = 0

    async def on_connect(self, bridge: ServerBridge) -> None:
        await self._sync(bridge)

    @on("click", "counter-inc")
    async def increment(self, bridge: ServerBridge, event: BridgeEvent) -> None:
        self.count += 1
        await self._sync(bridge)

    @on("click", "counter-dec")
    async def decrement(self, bridge: ServerBridge, event: BridgeEvent) -> None:
        self.count -= 1
        await self._sync(bridge)

    @on("click", "counter-reset")
    async def reset(self, bridge: ServerBridge, event: BridgeEvent) -> None:
        self.count = 0
        await self._sync(bridge)

    async def _sync(self, bridge: ServerBridge) -> None:
        await bridge.set("counter-display", f"Count: {self.count}")
        await bridge.set_state({"count": self.count})

        # Disable decrement at 0 for a nice UX touch
        if self.count <= 0:
            await bridge.disable("counter-dec")
        else:
            await bridge.enable("counter-dec")
