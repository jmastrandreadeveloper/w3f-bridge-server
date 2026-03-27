"""
Hello World handler.

PageBuilder setup:
  - Button  → bindId: "hello-btn"
  - Chip    → bindId: "message-display"
  - Bridge URL: ws://localhost:8767
"""

from __future__ import annotations

import random
from datetime import datetime

from ..handler import Handler, on
from ..bridge import ServerBridge, BridgeEvent


GREETINGS = [
    "Hello from Python! 🐍",
    "Greetings from the server side!",
    "Python says hi! The time is {time}",
    "Message #{count} — powered by Python",
    "Server response at {time} ✓",
    "Backend connected! Random: {rand}",
]


class HelloHandler(Handler):
    id = "hello-world"
    name = "Hello World"

    def __init__(self):
        self.click_count = 0

    async def on_connect(self, bridge: ServerBridge) -> None:
        await bridge.set("message-display", "Click the button!")

    @on("click", "hello-btn")
    async def handle_click(self, bridge: ServerBridge, event: BridgeEvent) -> None:
        self.click_count += 1
        now = datetime.now().strftime("%H:%M:%S")
        template = random.choice(GREETINGS)
        message = template.format(
            time=now,
            count=self.click_count,
            rand=random.randint(100, 999),
        )

        await bridge.set("message-display", message)
        await bridge.set_state({
            "lastMessage": message,
            "clickCount": self.click_count,
            "timestamp": now,
        })
