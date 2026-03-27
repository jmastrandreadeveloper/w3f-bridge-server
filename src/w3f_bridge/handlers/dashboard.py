"""
Dashboard handler — periodic data updates + manual refresh.

PageBuilder setup:
  - Chip   → bindId: "status-badge"     (connection status)
  - Chip   → bindId: "total-users"      (user count)
  - Chip   → bindId: "total-orders"     (order count)
  - Chip   → bindId: "revenue"          (revenue figure)
  - Chip   → bindId: "last-update"      (timestamp)
  - Button → bindId: "refresh-btn"      (manual refresh)
  - Bridge URL: ws://localhost:8767

Updates every 5 seconds with simulated metrics.
"""

from __future__ import annotations

import random
import asyncio
from datetime import datetime

from ..handler import Handler, on
from ..bridge import ServerBridge, BridgeEvent


class DashboardHandler(Handler):
    id = "data-dashboard"
    name = "Data Dashboard"

    def __init__(self):
        self._task: asyncio.Task | None = None
        self._users = 0
        self._orders = 0
        self._revenue = 0.0

    async def on_connect(self, bridge: ServerBridge) -> None:
        await bridge.set("status-badge", "● Online")
        self._generate_data()
        await self._push_data(bridge)

        # Start auto-refresh
        self._task = asyncio.create_task(self._auto_refresh(bridge))

    async def on_disconnect(self, bridge: ServerBridge) -> None:
        if self._task:
            self._task.cancel()
            self._task = None

    @on("click", "refresh-btn")
    async def manual_refresh(self, bridge: ServerBridge, event: BridgeEvent) -> None:
        await bridge.set("refresh-btn", "Refreshing...")
        await bridge.disable("refresh-btn")
        await asyncio.sleep(0.3)

        self._generate_data()
        await self._push_data(bridge)

        await bridge.set("refresh-btn", "Refresh")
        await bridge.enable("refresh-btn")

    async def _auto_refresh(self, bridge: ServerBridge) -> None:
        try:
            while True:
                await asyncio.sleep(5)
                self._generate_data()
                await self._push_data(bridge)
        except asyncio.CancelledError:
            pass

    def _generate_data(self) -> None:
        self._users += random.randint(1, 15)
        self._orders += random.randint(0, 5)
        self._revenue += round(random.uniform(10, 250), 2)

    async def _push_data(self, bridge: ServerBridge) -> None:
        now = datetime.now().strftime("%H:%M:%S")

        await bridge.set("total-users", f"{self._users:,} users")
        await bridge.set("total-orders", f"{self._orders:,} orders")
        await bridge.set("revenue", f"${self._revenue:,.2f}")
        await bridge.set("last-update", f"Updated {now}")

        await bridge.set_state({
            "users": self._users,
            "orders": self._orders,
            "revenue": self._revenue,
            "lastUpdate": now,
        })
