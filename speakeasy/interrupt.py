from __future__ import annotations

import atexit
import os
import sys
import threading
from collections.abc import Callable

from .console import console


def start_interrupt_listener(on_interrupt: Callable[[], None]) -> None:
    if not sys.stdin.isatty():
        return

    import termios

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    atexit.register(termios.tcsetattr, fd, termios.TCSADRAIN, old_settings)

    new_settings = termios.tcgetattr(fd)
    new_settings[3] &= ~(termios.ICANON | termios.ECHO)
    new_settings[6][termios.VMIN] = 1
    new_settings[6][termios.VTIME] = 0

    def _listener() -> None:
        termios.tcsetattr(fd, termios.TCSADRAIN, new_settings)
        try:
            while True:
                ch = os.read(fd, 1)
                if ch == b"\x03":  # Ctrl-C
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                    console.print("\n[dim]Shutting down...[/dim]")
                    os._exit(0)
                on_interrupt()
        except OSError:
            pass

    thread = threading.Thread(target=_listener, daemon=True)
    thread.start()
