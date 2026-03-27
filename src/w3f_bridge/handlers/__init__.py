"""Built-in handlers for common use cases."""

from .hello import HelloHandler
from .counter import CounterHandler
from .todo import TodoHandler
from .dashboard import DashboardHandler

__all__ = [
    "HelloHandler",
    "CounterHandler",
    "TodoHandler",
    "DashboardHandler",
]
