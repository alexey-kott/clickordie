import asyncio
import json
import re
from collections import defaultdict
from typing import Union

from bs4 import BeautifulSoup
from telethon import TelegramClient, events
from telethon.tl.types import PeerChannel, PeerChat, PeerUser
from googletrans import Translator
from aiohttp import ClientSession
from telegraph import Telegraph

from config import TG_API_ID, TG_API_HASH, PHONE, TELEGRAPH_USER_TOKEN
from forwarding_schema import FORWARDING_SCHEMA
import logging

logging.basicConfig(level=logging.ERROR)
translator = Translator()
forwarding_schema = []

client = TelegramClient(PHONE.strip('+'),
                        TG_API_ID,
                        TG_API_HASH)


AVAILABLE_TAGS = ['a', 'aside', 'b', 'blockquote', 'br', 'code', 'em', 'figcaption', 'figure', 'h3', 'h4', 'hr', 'i',
                  'iframe', 'img', 'li', 'ol', 'p', 'pre', 's', 'strong', 'u', 'ul', 'video']

def init_forwarding_schema():
    for forwarding_item in FORWARDING_SCHEMA:
        item = defaultdict(set)
        for direction, names in forwarding_item.items():
            entities = {search_entities(name) for name in names if search_entities(name)}
            item[direction] = entities
        if forwarding_item.get("TRANSLATE"):
            item['TRANSLATE'] = forwarding_item['TRANSLATE']
        forwarding_schema.append(item)


def search_entities(name: str) -> int:
    for dialog in user_dialogs:
        if name.startswith('@'):
            if getattr(dialog.entity, 'username', None) == name.strip('@'):
                return dialog.entity.id
        else:
            if getattr(dialog.entity, 'title', None) == name:
                return dialog.entity.id
            if dialog.name == name:
                return dialog.entity.id


def get_message_text(addressee: str,
                     msg_text: str, translate_schema=None) -> str:
    if translate_schema is None:
        return f"{msg_text}"
    else:
        translate = translator.translate(msg_text,
                                         src=translate_schema.get("FROM"),
                                         dest=translate_schema.get('TO'))
        return f"{addressee}\n {msg_text}\n\n{translate.text}"


def get_dialog(peer_entity: Union[PeerChannel, PeerChat, PeerUser]):
    try:
        entity_id = peer_entity.channel_id
    except AttributeError:
        entity_id = peer_entity.chat_id

    for dialog in user_dialogs:
        if dialog.entity.id == entity_id:
            return dialog.entity


@client.on(events.NewMessage(chats=('https://t.me/clickordie', '@memotronadminchannel')))
async def handler(event):
    # print(event.message.message)
    link = re.findall(r'https:\/\/click-or-die.ru[\S]*', event.message.message)[0]

    telegraph = Telegraph(access_token=TELEGRAPH_USER_TOKEN)

    async with ClientSession() as session:
        async with session.get(link) as response:
            page_source = await response.text()

            soup = BeautifulSoup(page_source, "lxml")
            content = soup.find_all(class_="post-inside")[0]

            items = content.find_all(['img'])

            for item in items:
                print(item['src'])

            html_contents = [str(item) for item in items]

            # print(telegraph.create_page('Test article', html_content=''.join(html_contents)))

            # with open("page.html", "w") as file:
            #     file.write(page_source)


async def main() -> None:
    global user_dialogs



    await client.start()

    # user_dialogs = await client.get_dialogs()
    # init_forwarding_schema()

    await client.run_until_disconnected()


if __name__ == "__main__":
    # import requests as req
    #
    # params = {
    #     "access_token": TELEGRAPH_USER_TOKEN,
    #     "title": "Test article",
    #     "return_content": True,
    #     "content":
    # }
    #
    # response = req.get("https://api.telegra.ph/createPage", params=params)
    # # print(str(response.text, 'utf-8', errors='replace'))
    #
    # data = json.loads(response.text, encoding='utf-8')
    #
    # print(data)
    # # pages = data['result']['pages']
    #
    # # for page in pages:
    # #     print(page['description'])
    #
    # with open("telegraph_pages.json", "w", encoding='utf-8') as file:
    #     file.write(response.text)
    #
    # exit()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
