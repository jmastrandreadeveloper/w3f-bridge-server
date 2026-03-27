#!/usr/bin/env python3
"""
Custom handler example — inline decorator style.

    python examples/run_custom.py

Shows how to create handlers without separate files.
"""

from w3f_bridge import BridgeServer, on
from datetime import datetime

server = BridgeServer(port=8767, name="Custom App Server")


@server.handler("color-picker")
class ColorPicker:
    """Cycle through colors on button click."""

    COLORS = ["#ef4444", "#f97316", "#eab308", "#22c55e", "#3b82f6", "#8b5cf6", "#ec4899"]

    def __init__(self):
        self.index = 0

    async def on_connect(self, bridge):
        await bridge.set("color-label", self.COLORS[self.index])
        await bridge.style("color-preview", {
            "background": self.COLORS[self.index],
        })

    @on("click", "next-color")
    async def next_color(self, bridge, event):
        self.index = (self.index + 1) % len(self.COLORS)
        color = self.COLORS[self.index]
        await bridge.set("color-label", color)
        await bridge.style("color-preview", {"background": color})

    @on("click", "prev-color")
    async def prev_color(self, bridge, event):
        self.index = (self.index - 1) % len(self.COLORS)
        color = self.COLORS[self.index]
        await bridge.set("color-label", color)
        await bridge.style("color-preview", {"background": color})


# You can also use function-style handlers
@server.on("click", "timestamp-btn")
async def show_timestamp(bridge, event):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await bridge.set("timestamp-display", now)


server.run()
