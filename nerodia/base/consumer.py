import asyncio
from typing import Iterable
from abc import ABCMeta, abstractmethod

from nerodia.twitch import TwitchClient, TwitchStream, TwitchUser


class Consumer(metaclass=ABCMeta):
    """The base class for all consumers.

    Defines a common interface that all consumers must implement.
    This is used once an update is received by a producer.
    """

    @abstractmethod
    def __init__(self, twitch_client: TwitchClient):
        """Set up the consumer and its attributes."""

    @abstractmethod
    async def initialize(self, loop: asyncio.AbstractEventLoop):
        """Run any code that is required to run before the polling starts."""

    @abstractmethod
    async def cleanup(self):
        """Run any code that is required to run before nerodia exits."""

    @abstractmethod
    async def stream_online(self, stream: TwitchStream, user: TwitchUser):
        """Called when the given `stream` changes state to online."""

    @abstractmethod
    async def stream_offline(self, user: TwitchUser):
        """Called when the given `user`'s stream goes offline."""

    @abstractmethod
    async def get_all_follows(self) -> Iterable[str]:
        """Get an iterable of all followed streamers that are known to this consumer."""
