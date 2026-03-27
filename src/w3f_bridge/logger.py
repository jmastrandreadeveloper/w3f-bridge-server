"""
W3F Bridge — Styled console output.
"""

from __future__ import annotations


def print_banner(
    name: str,
    host: str,
    port: int,
    handlers: list[tuple[str, str]],
    version: str = "1.0.0",
) -> None:
    """Print a styled server banner to the console."""

    url = f"ws://{host}:{port}"
    handler_count = len(handlers)

    # Calculate box width
    inner_lines = [
        f"  {name} v{version}",
        f"  Bridge WS → {url}",
        f"  Handlers: {handler_count}",
    ]
    for hid, hname in handlers:
        inner_lines.append(f"    ▸ {hname} ({hid})")

    max_len = max(len(line) for line in inner_lines) + 2
    w = max(max_len, 40)

    print()
    print(f"  ╔{'═' * w}╗")
    for line in inner_lines[:3]:
        print(f"  ║{line.ljust(w)}║")
    if handlers:
        print(f"  ╠{'─' * w}╣")
        for line in inner_lines[3:]:
            print(f"  ║{line.ljust(w)}║")
    print(f"  ╚{'═' * w}╝")
    print()
    print("  Waiting for connections...")
    print(f"  (Set Bridge URL in PageBuilder Inspector to {url})")
    print()
