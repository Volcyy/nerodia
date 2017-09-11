"""
An asynchronous interface to the Twitch API.
"""

import asyncio
from typing import Optional, NamedTuple, Union

import aiohttp


BASE_URL = 'https://api.twitch.tv/kraken/'


class TwitchUser(NamedTuple):
    name: str
    id: str
    bio: Optional[str]
    created_at: str
    updated_at: str
    logo: Optional[str]
    display_name: str


class TwitchStream(NamedTuple):
    game: str
    viewers: int
    created_at: str
    status: str
    logo: str
    video_banner: str
    followers: int
    views: int


class TwitchClient:
    def __init__(self, client_id: str):
        self._headers = {
            'Accept': "application/vnd.twitchtv.v5+json",
            'Client-ID': client_id
        }
        self._cs = None

    def __del__(self):
        self.close()

    async def init(self):
        self._cs = aiohttp.ClientSession()

    def close(self):
        if self._cs is not None:
            self._cs.close()

    async def _request_get(self, route: str, *, attempt=1) -> dict:
        if self._cs is None:
            await self.init()

        async with self._cs.get(BASE_URL + route, headers=self._headers) as res:
            if res.status >= 500:
                await asyncio.sleep(0.5 * attempt)
                return await self._request_get(route, attempt + 1)

            return await res.json()

    async def translate_username_to_id(self, name) -> Optional[TwitchUser]:
        resp = await self._request_get(f'users?login={name}')
        if resp['_total'] == 0:
            return None

        user = resp['users'][0]
        return TwitchUser(name=user['name'], id=user['_id'], bio=user['bio'],
                          created_at=user['created_at'], updated_at=user['updated_at'],
                          logo=user['logo'], display_name=user['display_name'])

    async def get_stream_by_user(self, user_id: Union[str, int]):
        resp = await self._request_get(f'streams/{user_id}')
        stream = resp['stream']
        if stream is None:
            return None

        channel = stream['channel']
        return TwitchStream(game=stream['game'], viewers=stream['viewers'],
                            created_at=stream['created_at'], status=stream['channel']['status'],
                            logo=channel['logo'], video_banner=channel['video_banner'],
                            followers=channel['followers'], views=channel['views'])
