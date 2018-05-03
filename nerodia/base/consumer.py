import asyncio
from abc import ABCMeta, abstractmethod
from typing import Iterable

# from nerodia.base import Module
from nerodia.core import Nerodia
from nerodia.twitch import TwitchClient, TwitchStream, TwitchUser


class Consumer(metaclass=ABCMeta):
    """The base class for all consumers.

    Defines a common interface that all consumers must implement.
    This is used once an update is received by a producer.
    """

    @abstractmethod
    def __init__(self, twitch_client: TwitchClient, nerodia: Nerodia):
        """Set up the consumer and its attributes.

        Args:
            twitch_client (TwitchClient):
                An instance of the application's Twitch client.
            nerodia (Nerodia):
                An instance of the central nerodia class managing the application.
        """

    @property
    @abstractmethod
    def name(self):
        """Return the name of this consumer. Must be identical to the package name."""

    @abstractmethod
    async def initialize(self, loop: asyncio.AbstractEventLoop):
        """Run any code that is required to run before the polling starts.

        Args:
            loop (asyncio.AbstractEventLoop):
                The event loop that is currently in use.
        """

    @abstractmethod
    async def cleanup(self):
        """Run any code that is required to run before nerodia exits."""

    @abstractmethod
    async def stream_online(self, stream: TwitchStream, user: TwitchUser):
        """
        Called when the given stream changes state to online.

        Args:
            stream (TwitchStream):
                The stream that just went online.
            user (TwitchUser):
                The user that is streaming.
        """

    @abstractmethod
    async def stream_offline(self, user: TwitchUser):
        """
        Called when the given user's stream goes offline.

        Args:
            user (TwitchUser):
                The user whose stream just went offline.
        """

    @abstractmethod
    async def get_all_follows(self) -> Iterable[str]:
        """
        Get an iterable of all followed streamers that are known to this consumer.

        Returns:
            Iterable[str]:
                An iterable of stream names that are
                being followed on this consumer.
        """

    @abstractmethod
    async def load_module(self, module: "Module"):
        """
        Load the specified consumer-specific module.

        Args:
            module (Module):
                The module to load. This method should
                then call `await module.attach(self)`
                to attach the module to the consumer instance.
        """

    @abstractmethod
    async def unload_module(self, module_name: str):
        """
        Unload the specified consumer-specific module.

        Args:
            module_name (str):
                The module to unload. This method should
                find the module within its loaded modules
                and detach the module from the consumer instance.

        Raises:
            ValueError:
                If the given module could not be found
                within the loaded modules, this method
                should raise a `ValueError`.
        """
