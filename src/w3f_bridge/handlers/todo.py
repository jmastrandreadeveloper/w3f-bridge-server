"""
Todo List handler — add, toggle, clear done items.

PageBuilder setup:
  - Button → bindId: "add-todo"      (label: "Add")
  - Button → bindId: "clear-done"    (label: "Clear done")
  - Chip   → bindId: "todo-count"    (shows "3 items, 1 done")
  - Chip   → bindId: "todo-item-1"   (first item)
  - Chip   → bindId: "todo-item-2"   (second item)
  - Chip   → bindId: "todo-item-3"   (third item)
  - Bridge URL: ws://localhost:8767

The handler pre-populates 3 demo tasks on connect.
Click a todo-item chip to toggle done. Click clear-done to remove completed.
"""

from __future__ import annotations

from ..handler import Handler, on
from ..bridge import ServerBridge, BridgeEvent


MAX_VISIBLE_ITEMS = 5


class TodoHandler(Handler):
    id = "todo-list"
    name = "Todo List"

    def __init__(self):
        self.todos: list[dict] = []
        self.next_id = 1

    async def on_connect(self, bridge: ServerBridge) -> None:
        # Pre-populate demo tasks
        for text in ["Learn W3F Bridge", "Build a dashboard", "Deploy to production"]:
            self.todos.append({"id": self.next_id, "text": text, "done": False})
            self.next_id += 1
        await self._sync(bridge)

    @on("click", "add-todo")
    async def add_todo(self, bridge: ServerBridge, event: BridgeEvent) -> None:
        todo_id = self.next_id
        self.next_id += 1
        self.todos.append({"id": todo_id, "text": f"New task #{todo_id}", "done": False})
        await self._sync(bridge)

    @on("click", "clear-done")
    async def clear_done(self, bridge: ServerBridge, event: BridgeEvent) -> None:
        self.todos = [t for t in self.todos if not t["done"]]
        await self._sync(bridge)

    # Click on any todo-item-N toggles its done state
    @on("click", "todo-item-1")
    @on("click", "todo-item-2")
    @on("click", "todo-item-3")
    @on("click", "todo-item-4")
    @on("click", "todo-item-5")
    async def toggle_item(self, bridge: ServerBridge, event: BridgeEvent) -> None:
        # Extract item index from bindId: "todo-item-2" → index 1
        try:
            idx = int(event.source.split("-")[-1]) - 1
        except (ValueError, IndexError):
            return
        if 0 <= idx < len(self.todos):
            self.todos[idx]["done"] = not self.todos[idx]["done"]
        await self._sync(bridge)

    async def _sync(self, bridge: ServerBridge) -> None:
        total = len(self.todos)
        done = sum(1 for t in self.todos if t["done"])

        await bridge.set("todo-count", f"{total} items, {done} done")

        # Update visible item chips
        for i in range(MAX_VISIBLE_ITEMS):
            bind_id = f"todo-item-{i + 1}"
            if i < len(self.todos):
                todo = self.todos[i]
                prefix = "✓ " if todo["done"] else "○ "
                await bridge.set(bind_id, f"{prefix}{todo['text']}")
                await bridge.show(bind_id)
                if todo["done"]:
                    await bridge.style(bind_id, {"opacity": "0.5", "textDecoration": "line-through"})
                else:
                    await bridge.style(bind_id, {"opacity": "1", "textDecoration": "none"})
            else:
                await bridge.hide(bind_id)

        # Enable/disable clear button
        if done > 0:
            await bridge.enable("clear-done")
        else:
            await bridge.disable("clear-done")

        await bridge.set_state({
            "todos": self.todos,
            "totalCount": total,
            "doneCount": done,
        })
