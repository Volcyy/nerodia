"""
The entry point for Nerodia.
Starts the `inbox_poller` task,
and afterwards, the Discord bot.
"""


import asyncio
import logging

from .bot import discord_bot
from .config import DISCORD_CFG


logging.basicConfig(
    format="%(asctime)s | %(name)18s | %(funcName)15s | %(levelname)8s | %(message)s",
    datefmt="%d.%m.%y %H:%M:%S",
    level=logging.INFO
)

log = logging.getLogger(__name__)
logging.getLogger('discord').setLevel(logging.ERROR)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    discord_bot.run(DISCORD_CFG['token'])
    log.info("Got SIGINT. Shutting down...")
    loop.close()
