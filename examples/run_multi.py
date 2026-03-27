#!/usr/bin/env python3
"""
Multi-handler example — all built-in handlers on one server.

    python examples/run_multi.py

All handlers share the same WebSocket connection.
Use different bindIds for each handler's components.
"""

from w3f_bridge import BridgeServer
from w3f_bridge.handlers import (
    HelloHandler,
    CounterHandler,
    TodoHandler,
    DashboardHandler,
)

server = BridgeServer(
    port=8767,
    name="W3F Multi-Handler Server",
)

server.register(HelloHandler)
server.register(CounterHandler)
server.register(TodoHandler)
server.register(DashboardHandler)

server.run()
