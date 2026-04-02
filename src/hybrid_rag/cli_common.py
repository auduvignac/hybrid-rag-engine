"""Shared helpers for user-facing command-line interfaces."""

from __future__ import annotations

import argparse
import sys
import traceback
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def add_debug_argument(parser: argparse.ArgumentParser) -> None:
    """Register the shared debug flag on a CLI parser."""

    parser.add_argument(
        "-v",
        "--debug",
        action="store_true",
        help="Enable verbose debug output with full tracebacks on errors.",
    )


def run_cli_action(
    action: Callable[[], T],
    *,
    operation_name: str,
    debug: bool,
    cancel_message: str,
) -> tuple[int, T | None]:
    """Run a CLI action with shared user-facing error handling."""

    try:
        return 0, action()
    except KeyboardInterrupt:
        print(cancel_message, file=sys.stderr)
        return 130, None
    except Exception as error:
        print(f"{operation_name} failed: {error}", file=sys.stderr)
        if debug:
            print("\nFull traceback (debug mode enabled):", file=sys.stderr)
            traceback.print_exc()
        return 1, None
