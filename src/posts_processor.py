"""
Post processing module responsible for parsing entities, shortening
links, and building formatted captions.
"""

from dataclasses import dataclass
import requests
from pathlib import Path
import logging
import telebot
from config import Config

logger = logging.getLogger(__name__)

@dataclass
class ProcessedPost:
    caption: str
    image_paths: list[Path]
    source_post_id: int

def extract_url(
        caption_entities:list[telebot.types.MessageEntity]
) -> str | None:
    """
    Extract the first text_link URL from Telegram message caption
    entities.
    """
    for entity in caption_entities:
        if entity.type == 'text_link':
            return entity.url

def shorten_url(long_url:str, token:str) -> str:
    """
    Shorten a URL using the TinyURL API.
    """
    response = requests.post(
        'https://api.tinyurl.com/create',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        },
        json={
            'url': long_url,
            'domain': 'tinyurl.com',
        },
        timeout=15,
    )

    response.raise_for_status()

    payload = response.json()
    return payload['data']['tiny_url']

def build_caption(
        caption:str,
        caption_entities:list[telebot.types.MessageEntity],
        settings:Config
):
    """
    Format a Telegram caption into a VK-compatible caption containing
    channel tags, source name, and shortened link.
    """
    message_tags_str = caption.split('\n')[0]

    message_tags = []
    for tag in message_tags_str.split(' '):
        message_tags.append(tag + '@' + settings.VK_GROUP_URL)

    source_username = caption.split('источник: ')[-1]

    long_url = extract_url(caption_entities)
    short_url = shorten_url(long_url, settings.TINYURL_TOKEN)
    short_url = short_url.replace('https://', '')

    return str(
        ' '.join(message_tags) +
        '\n\n' +
        'источник: ' +  source_username + ' (' + short_url + ')'
    )

