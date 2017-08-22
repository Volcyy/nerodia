"""
Provides handlers for the various events
that are produced by the RedditProducer.
"""

from typing import Iterable, Optional, Tuple

import praw

from . import database as db
from .clients import reddit
from .util import stream_lock, stream_states, reddit_lock, token_dict, token_lock, verify_dict, verify_lock


def verify(msg: praw.models.Message):
    """
    Handles a message with the subject `verify`,
    which was usually sent by a Discord user in
    order to connect his reddit account to his
    Discord account for easy usage of other commands.
    """

    with token_lock:
        for key, val in token_dict.items():
            if msg.body == val:
                discord_id = key
                break
        else:
            discord_id = None

    if discord_id is not None:
        with verify_lock:
            verify_dict[discord_id] = msg.author.name
        with reddit_lock:
            msg.reply("You have connected your accounts successfully!")
    else:
        with reddit_lock:
            msg.reply(f"> {msg.body}\n\nFailed to connect accounts: Unknown token.")


def handle_message(event: Tuple[str, praw.models.Message]) -> None:
    """
    Handles the message Event and processes the new message.
    """

    _, msg = event
    print('New Message from', (msg.author or msg.subreddit).name, 'contents:', msg.body)

    if msg.subject == "verification":
        verify(msg)
    elif msg.body.startswith("**gadzooks!"):
        with reddit_lock:
            msg.subreddit.mod.accept_invite()
        print(f"Accepted a Moderator invitation to {msg.subreddit}.")


def handle_stream_update(stream_name: str):
    """
    Handles a Stream update.
    Dispatches a sidebar update
    event for every Subreddit
    that is following the stream
    at the time the update occurs.

    Arguments:
        stream_name (str):
            The stream which status changed from offline to online or the other way around.
    """

    following_subreddits = db.get_subreddits_following(stream_name)
    print("stream status update on", stream_name)
    print("Following:", following_subreddits)

    for sub in following_subreddits:
        notify_update(sub)


def notify_update(sub: str):
    """
    Notifies the given Subreddit about an
    update on any Stream.
    This will remove the old stream
    list from its sidebar, re-build it,
    and put it where it was before.

    Arguments:
        sub (str):
            The Subreddit on which the update should be performed.
    """

    with reddit_lock:
        mod_relationship = reddit.subreddit(sub).mod
        current_sidebar = mod_relationship.settings()["description"]
    print(current_sidebar)
    stream_start_idx = find_stream_start_idx(current_sidebar)
    print(stream_start_idx)
    if stream_start_idx is None:
        print(sub, "is following streams, but no header was found.")
        return
    clean_sidebar = remove_old_stream_list(current_sidebar)
    print(clean_sidebar)
    with stream_lock:
        sidebar_with_streams = add_stream_list(
            clean_sidebar,
            stream_start_idx,
            (stream for stream in db.get_subreddit_follows(sub) if stream_states[stream])
        )
        print(sidebar_with_streams)
        with reddit_lock:
            mod_relationship.update(description=sidebar_with_streams)


def find_stream_start_idx(sidebar: str) -> Optional[int]:
    """
    Attempts to find the character `s` of the
        "# Streams"
    header and returns the index of it.
    In the future, this could be improved by
    allowing subreddits to set a "stream-list-marker"
    for each subreddit and thus being able
    to further customize where the stream
    ilst gets written by the bot.

    Arguments:
        sidebar (str):
            The subreddit sidebar to search.

    Returns:
        Optional[int]:
            The index of character "s" of the `# Streams`
            header, or `None` if it could not be found.
    """

    index = sidebar.find("# Streams")
    if index == -1:
        return None
    return index + len("# Streams") - 1


def remove_old_stream_list(sidebar: str) -> str:
    """
    Removes the old stream list of a Subreddit,

    Arguments:
        sidebar (str): The current sidebar of the Subreddit.

    Returns:
        str: The sidebar without the old streams.
    """

    as_list = sidebar.splitlines()
    updated = as_list.copy()
    previous_line = ""

    for line in as_list:
        if previous_line == "# Streams" or previous_line.startswith(">"):
            if line.startswith(">"):
                updated.remove(line)
        previous_line = line

    return '\n'.join(updated)


def add_stream_list(sidebar: str, start_idx: int, streams: Iterable[str]) -> str:
    """
    Adds the stream list to the Subreddit.
    Make sure to remove the old streams list
    beforehand using `remove_old_stream_list`
    to ensure that no duplicate entries will
    be on the list.

    Streams are added into the following format:
        # Streams
        > stream_name
        > another_stream
        > more_streams
    The lines containing stream names end with
    two spaces to ensure that the formatting
    will not put them together onto a single line.

    Arguments:
        sidebar (str):
            The sidebar to which the streams list should be added.
            The original argument is not modified.
        start_idx (int):
            The index of the last character of the header, which
            is usually `s` (from `# Streams`).
            Can be obtained by using `find_stream_start_idx`.
        streams (Iterable[str]):
            An iterable of strings containing the names of the
            streams which should be put onto the subreddit's
            sidebar below the streams header.
            Can be a list, but it is recommended to use a
            generator (expression) for efficiency.

    Returns:
        str:
            The updated sidebar, containing a list of streams
            in quotes (prefixed with `> ` and with two spaces
            appended). Aside from adding the list of streams,
            this does not differ from the original sidebar.
    """

    # See format description above.
    streams_as_string = "\n> " + "  \n> ".join(streams) + "  \n"

    return sidebar[:start_idx + 1] + streams_as_string + sidebar[start_idx + 1:]
