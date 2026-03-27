# W3F Bridge Server

Python framework for building **W3F Platform** backends. Write handler classes that respond to UI events and send commands back to the browser — all over WebSocket.

## Install

```bash
pip install websockets
pip install -e .
```

## Quick Start

```python
from w3f_bridge import BridgeServer, on

server = BridgeServer(port=8767)

@server.handler("my-app")
class MyApp:
    async def on_connect(self, bridge):
        await bridge.set("status", "Ready!")

    @on("click", "action-btn")
    async def handle_click(self, bridge, event):
        await bridge.set("status", "Button clicked!")

server.run()
```

Then in **W3F Studio → PageBuilder**:
1. Add a **Button** with `bindId: "action-btn"`
2. Add a **Chip** with `bindId: "status"`
3. Set **Bridge URL** to `ws://localhost:8767` (Inspector → Bridge section)
4. Open **Runtime** (rocket icon) → click the button

## Concepts

### Handlers

A handler is a class that manages a piece of backend logic. Each WebSocket connection gets its own handler instance, so `self` holds per-client state.

```python
from w3f_bridge import Handler, on

class CounterHandler(Handler):
    id = "counter"
    name = "Counter"

    def __init__(self):
        self.count = 0

    async def on_connect(self, bridge):
        await bridge.set("counter-display", "0")

    @on("click", "inc-btn")
    async def increment(self, bridge, event):
        self.count += 1
        await bridge.set("counter-display", str(self.count))
```

### The `@on` decorator

Binds a method to a specific event type + bindId:

```python
@on("click", "my-button")     # click events from "my-button"
@on("change", "my-input")     # change events from "my-input"
@on("click", "*")             # click events from ANY component
@on("*", "*")                 # ALL events from ALL components
```

### ServerBridge API

Each handler receives a `bridge` object with these methods:

| Method | Description |
|--------|-------------|
| `await bridge.set(bindId, value)` | Set a component's display value |
| `await bridge.show(bindId)` | Show a hidden component |
| `await bridge.hide(bindId)` | Hide a component |
| `await bridge.enable(bindId)` | Enable a disabled component |
| `await bridge.disable(bindId)` | Disable a component |
| `await bridge.toggle(bindId)` | Toggle visibility |
| `await bridge.style(bindId, {...})` | Apply inline styles |
| `await bridge.add_class(bindId, cls)` | Add a CSS class |
| `await bridge.remove_class(bindId, cls)` | Remove a CSS class |
| `await bridge.set_state({...})` | Update shared state |
| `bridge.get(bindId)` | Get last known value (sync) |
| `bridge.get_state()` | Get full shared state (sync) |
| `await bridge.emit(command)` | Send a raw BridgeCommand |

### Registration styles

**Class-based** (recommended for stateful logic):
```python
server = BridgeServer(port=8767)
server.register(MyHandler)
```

**Decorator-based** (inline definition):
```python
@server.handler("my-module")
class MyModule:
    ...
```

**Function-based** (quick one-offs):
```python
@server.on("click", "my-btn")
async def handle_click(bridge, event):
    await bridge.set("label", "Clicked!")
```

## Built-in Handlers

| Handler | ID | Components needed |
|---------|----|--------------------|
| `HelloHandler` | `hello-world` | Button `hello-btn` + Chip `message-display` |
| `CounterHandler` | `counter` | Buttons `counter-inc`, `counter-dec`, `counter-reset` + Chip `counter-display` |
| `TodoHandler` | `todo-list` | Buttons `add-todo`, `clear-done` + Chips `todo-count`, `todo-item-1`..`todo-item-5` |
| `DashboardHandler` | `data-dashboard` | Button `refresh-btn` + Chips `status-badge`, `total-users`, `total-orders`, `revenue`, `last-update` |

Run all at once:
```bash
python examples/run_multi.py
```

## Protocol

The Bridge protocol uses JSON over WebSocket:

**UI → Server** (events):
```json
{
  "type": "event",
  "event": {
    "type": "click",
    "source": "hello-btn",
    "timestamp": 1711432800000,
    "payload": {}
  }
}
```

**Server → UI** (commands):
```json
{
  "type": "command",
  "command": {
    "action": "set",
    "target": "message-display",
    "payload": { "value": "Hello!" },
    "source": "server"
  }
}
```

**Handshake** (server sends on connect):
```json
{
  "type": "hello",
  "modules": ["hello-world", "counter"],
  "server": "W3F Bridge Server",
  "version": "1.0.0"
}
```

## Examples

```bash
python examples/run_hello.py     # Minimal: hello world
python examples/run_multi.py     # All 4 handlers
python examples/run_custom.py    # Inline decorator style
```

## License

MIT
