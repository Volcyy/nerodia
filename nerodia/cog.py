"""
Contains the command group
for the Discord Bot.
"""

import asyncio
import datetime
import discord
from typing import Optional

from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

from . import util
from .database import (
    add_dr_connection, remove_dr_connection,
    get_moderated_subreddits, get_reddit_name, get_subreddit_moderators,
    subreddit_exists
)
from .util import (
    remove_token,
    token_dict, token_lock,
    verify_dict, verify_lock
)


ALREADY_CONNECTED_EMBED = discord.Embed(
    title="Cannot connect accounts:",
    description="You already have a reddit account connected. "
                "Use the `disconnectreddit` command to disconnect "
                "your Discord account from your reddit account.",
    colour=discord.Colour.orange()
)
DM_ONLY_EMBED = discord.Embed(
    title="Cannot connect accounts:",
    description="For safety reasons, this command can "
                "only be used in private messages.",
    colour=discord.Colour.red()
)
NO_CONNECTION_EMBED = discord.Embed(
    title="Failed to run command:",
    description="This command requires you to have a reddit account "
                "connected through the `connectreddit` command.",
    colour=discord.Colour.red()
)
NO_PM_IN_TIME_EMBED = discord.Embed(
    title="Failed to verify:",
    description="No verification PM was received in time.",
    colour=discord.Colour.red()
)
PM_URL = "https://www.reddit.com/message/compose?to=Botyy&subject=verification&message="

# The timeout for the reddit verification, in minutes
VERIFY_TIMEOUT = 5


def create_instructions(token: str) -> discord.Embed:
    """
    Creates an Embed containing the disclaimer
    for adding a Reddit account to your Discord account.
    This should be used for adding a field with the token
    which the user should send to the bot via a direct message.

    Arguments:
        token (str): The token that should be appended to the reddit PM link.

    Returns:
        discord.Embed: An embed with a disclaimer about user data.
    """

    return discord.Embed(
        title="Connect your Reddit Account",
        colour=discord.Colour.blue(),
        timestamp=datetime.datetime.now()
    ).add_field(
        name="Disclaimer",
        value="By connecting your account, you agree that your "
              "**Discord ID is stored unencrypted for an indefinite "
              "time, along with your reddit name, and this information "
              "may appear in the bot's log messages**. You can "
              "disconnect a connected account at any time.",
        inline=False
    ).add_field(
        name="Warning",
        value="**Do not share this link!**"
    ).add_field(
        name="Instructions",
        value=f"Send me a [Reddit Message]({PM_URL + token}) by clicking on "
              f"the link and clicking `send` to connect your reddit account.",
    ).set_footer(
        text="⏲ You have five minutes of time before the token expires."
    )


async def wait_for_add(user_id: str, timeout: int = VERIFY_TIMEOUT) -> Optional[str]:
    """
    Waits for the given user to add his reddit
    account. It is highly recommended to set
    a timeout, this defaults to five minutes.
    The dictionary which contains data about
    verification is checked in intervals,
    accomplished by sleeping for five seconds
    between checking the dictionary.

    Arguments:
        user_id (str):
            The Discord user ID for the user
            who wants to add his reddit account.
        timeout (int):
            The timeout (in minutes) after which
            `None` should be returned indicating
            that the user did not send a direct
            message for adding his reddit account
            in time. The user is removed from the
            verification dictionary. Defaults to
            the value of `VERIFY_TIMEOUT`.

    Returns:
        Optional[str]:
            The reddit name of the user if successful,
            `None` if no valid direct message containing
            the token was received in time.
    """

    timeout_ctr = timeout * 60
    while timeout_ctr > 0:
        await asyncio.sleep(5)
        timeout_ctr -= 5
        with verify_lock:
            user = verify_dict.get(user_id)

        if user is not None:
            with verify_lock:
                del verify_dict[user_id]

            return user

    return None


class Nerodia:
    """
    Commands for interacting with the Nerodia reddit bot.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("[DISCORD] Loaded Commands.")

    @commands.command(name="connectreddit")
    @commands.cooldown(rate=2, per=5. * 60, type=BucketType.user)
    async def connect_reddit(self, ctx):
        """
        Connects your Discord account to your reddit account.
        Please make sure to carefully read through the
        disclaimer and  the instructions that this
        command sends upon invocation.

        If you already have a reddit account connected,
        please use the `disconnectreddit` command to
        remove your reddit account from the database.

        This command can only be used in private messages
        to prevent other people connecting their reddit account
        to your Discord ID, for whatever reason.
        """

        if not isinstance(ctx.message.channel, discord.abc.PrivateChannel):
            return await ctx.send(embed=DM_ONLY_EMBED)
        elif get_reddit_name(ctx.message.author.id) is not None:
            return await ctx.send(embed=ALREADY_CONNECTED_EMBED)

        token = util.random_string()
        await ctx.send(embed=create_instructions(token))

        author_id = str(ctx.message.author.id)
        with token_lock:
            token_dict[author_id] = token

        reddit_name = await wait_for_add(author_id)
        remove_token(author_id)

        if reddit_name is None:
            await ctx.send(embed=NO_PM_IN_TIME_EMBED)
        else:
            add_dr_connection(ctx.message.author.id, reddit_name)
            await ctx.send(embed=discord.Embed(
                title="Verified successfully:",
                description=f"Your reddit name is {reddit_name}!",
                colour=discord.Colour.green()
            ))

    @commands.command()
    async def disconnectreddit(self, ctx):
        """
        Disconnects your reddit account from
        your Discord account, if connected.
        """

        if get_reddit_name(ctx.message.author.id) is None:
            return await ctx.send(embed=discord.Embed(
                title="Failed to disconnect:",
                description="You do not have an account connected.",
                colour=discord.Colour.red()
            ))
        else:
            remove_dr_connection(ctx.message.author.id)
            return await ctx.send(embed=discord.Embed(
                title="Disconnected!",
                description="Your reddit account was successfully "
                            "disconnected from your Discord ID.",
                colour=discord.Colour.green()
            ))

    @commands.group(aliases=["db"])
    async def dashboard(self, ctx, subreddit_name: str=None):
        """
        Displays a dashboard for all information
        about a connected reddit account, such as
        which subreddits you moderate.

        To get a dashboard on a per-subreddit basis,
        use `db subname`, for example `db askreddit`.

        This command requires you to have a reddit
        account connected to your Discord ID through
        the `connectreddit` command.
        """

        reddit_name = get_reddit_name(ctx.message.author.id)
        if reddit_name is None:
            await ctx.send(embed=NO_CONNECTION_EMBED)
        elif subreddit_name is not None:
            if subreddit_exists(subreddit_name):
                await ctx.send(embed=discord.Embed(
                    colour=discord.Colour.blue()
                ).set_author(
                    name=f"Dashboard for {subreddit_name}",
                    url=f"https://reddit.com/r/{subreddit_name}"
                ).add_field(
                    name="Subreddit Moderators",
                    value='• ' + '\n• '.join(r.name for r in get_subreddit_moderators(subreddit_name))
                ))
        else:
            moderated_subs = '\n'.join(get_moderated_subreddits(reddit_name))
            await ctx.send(embed=discord.Embed(
                colour=discord.Colour.blue()
            ).set_author(
                name=f"Dashboard for {reddit_name}",
                url=f"https://reddit.com/u/{reddit_name}",
                icon_url=ctx.message.author.avatar_url
            ).add_field(
                name="Moderated Subreddits",
                value=('• ' + moderated_subs) if moderated_subs else "*No known moderated Subreddits* :(",
                inline=False
            ))


def setup(bot: commands.Bot):
    """
    Adds the nerodia command
    group to the discord bot.
    """

    bot.add_cog(Nerodia(bot))
