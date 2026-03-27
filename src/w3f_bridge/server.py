"""
W3F Bridge — BridgeServer (core).

Manages WebSocket connections, handler lifecycle, and protocol compliance.
"""

from __future__ import annotations

import json
import asyncio
import signal
import logging
import inspect
from typing import Any, Callable

import websockets

from .bridge import ServerBridge, EventCallback
from .handler import Handler
from .types import BridgeEvent
from .logger import print_banner

logger = logging.getLogger("w3f_bridge")


class BridgeServer:
    """
    The main server. Register handlers, then call run().

    Usage:
        server = BridgeServer(port=8767)
        server.register(MyHandler)
        server.run()
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8767,
        name: str = "W3F Bridge Server",
        version: str = "1.0.0",
        debug: bool = False,
    ) -> None:
        self._host = host
        self._port = port
        self._name = name
        self._version = version
        self._debug = debug

        self._handler_classes: list[type[Handler]] = []
        self._function_handlers: list[tuple[str, str, EventCallback]] = []
        self._connections: set[ServerBridge] = set()

        if debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO, format="  %(message)s")

    # ── Handler registration ──────────────────────────────────────

    def register(self, handler_class: type[Handler]) -> None:
        """Register a handler class. One instance is created per connection."""
        self._handler_classes.append(handler_class)

    def handler(self, handler_id: str, name: str | None = None):
        """
        Class decorator to register a handler inline.

        Usage:
            @server.handler("my-module")
            class MyHandler:
                async def on_connect(self, bridge):
                    await bridge.set("status", "Ready")
        """

        def decorator(cls):
            cls.id = handler_id
            cls.name = name or handler_id
            # Ensure it has the Handler interface
            if not hasattr(cls, "on_connect"):
                cls.on_connect = Handler.on_connect
            if not hasattr(cls, "on_disconnect"):
                cls.on_disconnect = Handler.on_disconnect
            self._handler_classes.append(cls)
            return cls

        return decorator

    def on(self, event_type: str, bind_id: str):
        """
        Function decorator for quick event handlers.

        Usage:
            @server.on("click", "my-btn")
            async def handle_click(bridge, event):
                await bridge.set("label", "Clicked!")
        """

        def decorator(fn):
            self._function_handlers.append((event_type, bind_id, fn))
            return fn

        return decorator

    # ── WebSocket connection handler ──────────────────────────────

    async def _handle_client(self, websocket: Any) -> None:
        bridge = ServerBridge(websocket)
        self._connections.add(bridge)
        instances: list[Handler] = []

        try:
            logger.info("Client connected")

            # Instantiate handlers and wire @on() decorated methods
            for cls in self._handler_classes:
                instance = cls()
                self._wire_handler(instance, bridge)
                instances.append(instance)

            # Wire function-based handlers
            for event_type, bind_id, fn in self._function_handlers:
                bridge.on(event_type, bind_id, self._wrap_fn_handler(fn))

            # Send hello handshake
            module_ids = [cls.id for cls in self._handler_classes if hasattr(cls, "id")]
            await bridge._send({
                "type": "hello",
                "modules": module_ids,
                "server": self._name,
                "version": self._version,
            })

            # Call on_connect for each handler
            for instance in instances:
                result = instance.on_connect(bridge)
                if asyncio.iscoroutine(result):
                    await result

            # Message loop
            async for raw in websocket:
                try:
                    msg = json.loads(raw)
                    msg_type = msg.get("type")

                    if msg_type == "event" and "event" in msg:
                        event = BridgeEvent.from_dict(msg["event"])
                        if self._debug:
                            logger.debug(f"← Event: {event.type} from {event.source}")
                        await bridge.dispatch(event)

                    # Store values from change events
                    if msg_type == "event":
                        event_data = msg.get("event", {})
                        if event_data.get("type") == "change" and event_data.get("payload"):
                            source = event_data.get("source", "")
                            value = event_data["payload"].get("value")
                            if source and value is not None:
                                bridge._values[source] = value

                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON: {str(raw)[:100]}")
                except Exception:
                    logger.exception("Error processing message")

        except websockets.ConnectionClosed:
            pass
        except Exception:
            logger.exception("Connection error")
        finally:
            logger.info("Client disconnected")

            # Call on_disconnect for each handler
            for instance in instances:
                try:
                    result = instance.on_disconnect(bridge)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception:
                    logger.exception("Error in on_disconnect")

            bridge.destroy()
            self._connections.discard(bridge)

    def _wire_handler(self, instance: Handler, bridge: ServerBridge) -> None:
        """Discover @on() decorated methods and wire them to the bridge."""
        for attr_name in dir(instance):
            if attr_name.startswith("_"):
                continue
            method = getattr(instance, attr_name, None)
            if method is None or not callable(method):
                continue
            bindings = getattr(method, "_bridge_bindings", None)
            if not bindings:
                continue

            for event_type, bind_id in bindings:
                # Create a closure that calls the method with (bridge, event)
                bound_method = method
                if inspect.iscoroutinefunction(bound_method):
                    async def make_async_cb(m):
                        async def cb(b: ServerBridge, e: BridgeEvent):
                            await m(b, e)
                        return cb
                    # Use immediate binding to capture method reference
                    bridge.on(event_type, bind_id, self._make_async_cb(bound_method))
                else:
                    bridge.on(event_type, bind_id, self._make_sync_cb(bound_method))

    @staticmethod
    def _make_async_cb(method) -> EventCallback:
        async def cb(bridge: ServerBridge, event: BridgeEvent):
            await method(bridge, event)
        return cb

    @staticmethod
    def _make_sync_cb(method) -> EventCallback:
        async def cb(bridge: ServerBridge, event: BridgeEvent):
            result = method(bridge, event)
            if asyncio.iscoroutine(result):
                await result
        return cb

    @staticmethod
    def _wrap_fn_handler(fn) -> EventCallback:
        """Wrap a function-style handler to match EventCallback signature."""
        if inspect.iscoroutinefunction(fn):
            async def wrapper(bridge: ServerBridge, event: BridgeEvent):
                await fn(bridge, event)
        else:
            async def wrapper(bridge: ServerBridge, event: BridgeEvent):
                result = fn(bridge, event)
                if asyncio.iscoroutine(result):
                    await result
        return wrapper

    # ── Server lifecycle ──────────────────────────────────────────

    def run(self) -> None:
        """Start the server (blocking). Press Ctrl+C to stop."""
        try:
            asyncio.run(self._run())
        except KeyboardInterrupt:
            print("\n  Server stopped.")

    async def _run(self) -> None:
        # Print banner
        handlers = [
            (cls.id, getattr(cls, "name", cls.id))
            for cls in self._handler_classes
            if hasattr(cls, "id")
        ]
        print_banner(self._name, self._host, self._port, handlers, self._version)

        # Start WebSocket server
        async with websockets.serve(
            self._handle_client,
            self._host,
            self._port,
        ):
            # Wait forever (or until cancelled)
            stop = asyncio.get_event_loop().create_future()

            # Handle SIGINT/SIGTERM on Unix
            try:
                loop = asyncio.get_event_loop()
                for sig in (signal.SIGINT, signal.SIGTERM):
                    loop.add_signal_handler(sig, stop.set_result, None)
            except (NotImplementedError, AttributeError):
                # Windows doesn't support add_signal_handler — rely on KeyboardInterrupt
                pass

            try:
                await stop
            except asyncio.CancelledError:
                pass

        # Clean up all connections
        for bridge in list(self._connections):
            bridge.destroy()
