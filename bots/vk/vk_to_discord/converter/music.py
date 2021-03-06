from typing import List
from urllib.parse import quote

import disnake as discord
from spotipy2 import Spotify
from spotipy2.auth import ClientCredentialsFlow
from spotipy2.types import Track
from vkbottle_types.objects import AudioAudio

from config import spotify_client_id, spotify_client_secret

YOUTUBE_SEARCH = 'https://www.youtube.com/results?search_query={}'


async def get_spotify_track_link_by_name(song_name):
    spotify = Spotify(
        ClientCredentialsFlow(
            client_id=spotify_client_id,
            client_secret=spotify_client_secret
        )
    )

    async with spotify:
        tracks = await spotify.search(song_name, types=Track)
        if tracks:
            return tracks[0].external_urls['spotify']


async def format_spotify_track_link(song_name):
    track_link = await get_spotify_track_link_by_name(song_name)
    if track_link:
        return f'[Spotify Track]({track_link}) | '
    else:
        return ''


async def process_audios(audios: List[AudioAudio], embed: discord.Embed):
    for audio in audios:
        title = f'{audio.artist} {audio.title}'
        url_title = quote(title)
        vk_track_url = f'https://vk.com/audio{audio.owner_id}_{audio.id}'

        audios_description = (
            f'{audio.artist} - {audio.title}\n'
            f'{await format_spotify_track_link(song_name=title)}'
            f'[VK Track]({vk_track_url}) | '
            f'[Search Youtube]({YOUTUBE_SEARCH.format(url_title)})'
        )

        embed.add_field(
            name='Аудиозапись',
            value=audios_description
        )

    return embed
