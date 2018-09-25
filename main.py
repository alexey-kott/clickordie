import asyncio
import re
from typing import List

from bs4 import BeautifulSoup, Tag
from telethon import TelegramClient, events
from aiohttp import ClientSession
from telegraph import Telegraph

from config import (
    TG_API_ID, TG_API_HASH, PHONE,
    TELEGRAPH_USER_TOKEN, SOURCE_CHANNELS, DEST_CHANNELS,
)
import logging

logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='err.log')

client = TelegramClient(PHONE.strip('+'),
                        TG_API_ID,
                        TG_API_HASH)

# ['a', 'aside', 'b', 'blockquote', 'br', 'code', 'em', 'figcaption', 'figure', 'h3', 'h4', 'hr',
# 'i', 'iframe', 'img', 'li', 'ol', 'p', 'pre', 's', 'strong', 'u', 'ul', 'video']
AVAILABLE_TAGS = ['h1', 'h2', 'h3', 'h4', 'hr', 'img', 'p', 'ul', 'ol']


def prepare_items(items: List[Tag]) -> str:
    for item in items:
        if item.name == 'h1':
            item.name = 'h3'
        if item.name == 'h2':
            item.name = 'h4'
        if item.span is not None:
            item.span.decompose()

    return ''.join([str(item) for item in items])


async def push_post_to_telegraph(message: str) -> str:
    post_links = re.findall(r'https://click-or-die.ru[\S]*', message)

    if len(post_links) == 0:
        return message

    telegraph = Telegraph(access_token=TELEGRAPH_USER_TOKEN)

    async with ClientSession() as session:
        async with session.get(post_links[0]) as response:
            page_source = await response.text()
            soup = BeautifulSoup(page_source, "lxml")
            content = soup.find_all(class_="post-inside")[0]
            items = content.find_all(AVAILABLE_TAGS)
            html_contents = prepare_items(items)

            title = soup.find('title').text.split('|')[0]
            telegraph_response = telegraph.create_page(title, html_content=''.join(html_contents))

            return f"{message}\n{telegraph_response['url']}"


@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    post_text = await push_post_to_telegraph(event.message.message)

    for dest_channel in DEST_CHANNELS:
        dest_channel = await client.get_entity(dest_channel)
        try:
            await client.send_message(dest_channel, post_text, file=event.message.media)
        except Exception as e:
            logging.error(e)
            await client.send_message(dest_channel, post_text)


async def main() -> None:
    await client.start()
    await client.run_until_disconnected()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
