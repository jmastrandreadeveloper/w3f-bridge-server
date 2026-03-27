#!/usr/bin/env python3
"""
Minimal example — Hello World handler only.

    python examples/run_hello.py

PageBuilder:
  1. Add a Button (bindId: "hello-btn") and a Chip (bindId: "message-display")
  2. Set Bridge URL to ws://localhost:8767
  3. Open Runtime → click the button
"""

from w3f_bridge import BridgeServer
from w3f_bridge.handlers import HelloHandler

server = BridgeServer(port=8767)
server.register(HelloHandler)
server.run()
