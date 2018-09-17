from collections import defaultdict

from telethon import TelegramClient, events

from config import TG_API_ID, TG_API_HASH, PHONE, FORWARDING_SCHEMA
import logging
logging.basicConfig(level=logging.ERROR)


def get_forwarding_schema():
    forwarding_schema = []
    for forwarding_item in FORWARDING_SCHEMA:
        item = defaultdict(set)
        for direction, names in forwarding_item.items():
            entities = {search_entities(name) for name in names if search_entities(name)}
            item[direction] = entities
        forwarding_schema.append(item)

    return forwarding_schema


def search_entities(name):
    name = name.strip('@')
    for dialog in user_dialogs:
        if dialog.name == name:
            return dialog.entity
    for dialog in user_dialogs:
        if getattr(dialog.entity, 'username', None) == name:
            return dialog.entity
        if getattr(dialog.entity, 'title', None) == name:
            return dialog.entity


def get_dialog_by_id(entity_id):
    for dialog in user_dialogs:
        if dialog.entity.id == entity_id:
            return dialog.entity


def main():
    global client
    global user_dialogs
    client = TelegramClient(PHONE.strip('+'),
                            TG_API_ID,
                            TG_API_HASH,
                            proxy=None,
                            update_workers=4,
                            spawn_read_thread=False)

    client.start()

    if not client.is_user_authorized():
        client.send_code_request(PHONE)
        client.sign_in(PHONE, input("Enter code: "))

    user_dialogs = client.get_dialogs()

    group = search_entities("Bmsklad")
    for participant in client.get_participants(group):
        print(f"{participant.username}, {participant.first_name} {participant.last_name}")


if __name__ == '__main__':
    main()