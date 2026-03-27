"""
W3F Bridge Server — Python framework for W3F Platform backends.

Usage:
    from w3f_bridge import BridgeServer, Handler, on

    server = BridgeServer(port=8767)

    @server.handler("my-app")
    class MyApp:
        async def on_connect(self, bridge):
            await bridge.set("status", "Ready")

        @on("click", "my-btn")
        async def handle_click(self, bridge, event):
            await bridge.set("status", "Clicked!")

    server.run()
"""

from .server import BridgeServer
from .bridge import ServerBridge
from .handler import Handler, on
from .types import BridgeEvent, BridgeCommand

__all__ = [
    "BridgeServer",
    "ServerBridge",
    "Handler",
    "on",
    "BridgeEvent",
    "BridgeCommand",
]

__version__ = "1.0.0"
