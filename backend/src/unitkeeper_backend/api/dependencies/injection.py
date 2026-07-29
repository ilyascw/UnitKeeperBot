"""Typed default used for Dishka-injected FastAPI parameters.

Dishka replaces these values before endpoint execution. Keeping the runtime
default as ``None`` lets FastAPI build the signature, while the explicit
``Any`` type prevents an artificial ``Optional`` from leaking into handlers.
"""

from typing import Any

INJECTED: Any = None
