"""
Imports various modules from
this package so that relative
imports work properly.

Additionally, sets the asyncio
event loop policy to the one
from the `uvloop` package, which
is a lot faster than the standard
asyncio implementation, and will
(hopefully) speed up our app.
"""

# flake8: noqa

try:
    import uvloop
except ImportError:
    pass
else:
    import asyncio
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

from . import (
    database,
    bot, cog, clients, database, handlers,
    util, workers
)

__all__ = [
    "database",
    "bot", "cog", "clients", "database", "handlers",
    "util", "workers"
]
