# modules/store.py

from pyrogram import filters
from pyrogram.handlers import MessageHandler

from utils.db import get, set, delete
from modules.help import help_dict
from utils.style import success, error, info, safe_edit, safe_send

# 🔥 cloud integration
from modules.cloud import cloud_save, get_mode

__MODULE__ = "store"

COLLECTION = "storage"
KEY_INDEX = "_keys"


# ================= HELPERS =================
async def get_keys():
    return await get(COLLECTION, KEY_INDEX, [])


async def add_key(name):
    keys = await get_keys()
    if name not in keys:
        keys.append(name)
        await set(COLLECTION, KEY_INDEX, keys)


async def remove_key(name):
    keys = await get_keys()
    if name in keys:
        keys.remove(name)
        await set(COLLECTION, KEY_INDEX, keys)


# ================= STORE =================
async def store_cmd(client, message):
    if len(message.command) < 2:
        return await safe_edit(message, error("Usage: .store <name>"))

    name = message.command[1]
    reply = message.reply_to_message

    if not reply:
        return await safe_edit(message, error("Reply to something to store"))

    existing = await get(COLLECTION, name)
    if existing:
        return await safe_edit(message, error("Name already exists"))

    data = {"type": None, "content": None}

    # ================= TEXT =================
    if reply.text or reply.caption:
        data["type"] = "text"
        data["content"] = reply.text or reply.caption

    # ================= MEDIA =================
    elif reply.media:
        data["type"] = "media"

        if reply.document:
            data["content"] = reply.document.file_id
        elif reply.photo:
            data["content"] = reply.photo.file_id
        elif reply.video:
            data["content"] = reply.video.file_id
        elif reply.audio:
            data["content"] = reply.audio.file_id
        else:
            return await safe_edit(message, error("Unsupported media"))

    else:
        return await safe_edit(message, error("Unsupported message"))

    # ================= SAVE (ALWAYS LOCAL) =================
    await set(COLLECTION, name, data)
    await add_key(name)

    # ================= CLOUD SYNC =================
    mode = await get_mode()

    if mode in ["cloud", "both"]:
        ok, result = await cloud_save(name, data)

        if not ok:
            return await safe_edit(message, error(f"Saved locally, cloud failed: {result}"))

    await safe_edit(message, success(f"Saved → {name}"))


# ================= GET =================
async def get_cmd(client, message):
    if len(message.command) < 2:
        return await safe_edit(message, error("Usage: .get <name>"))

    name = message.command[1]
    data = await get(COLLECTION, name)

    if not data:
        return await safe_edit(message, error("Not found"))

    if data["type"] == "text":
        return await safe_send(client, message.chat.id, data["content"])

    elif data["type"] == "media":
        return await client.send_cached_media(
            message.chat.id,
            data["content"]
        )


# ================= LIST =================
async def list_cmd(client, message):
    keys = await get_keys()

    if not keys:
        return await safe_edit(message, info("No stored items"))

    text = "📦 <b>Stored Items</b>\n────────────\n\n"
    for k in keys:
        text += f"• <code>{k}</code>\n"

    await safe_send(client, message.chat.id, text)


# ================= DELETE =================
async def delete_cmd(client, message):
    if len(message.command) < 2:
        return await safe_edit(message, error("Usage: .delstore <name>"))

    name = message.command[1]

    data = await get(COLLECTION, name)
    if not data:
        return await safe_edit(message, error("Not found"))

    await delete(COLLECTION, name)
    await remove_key(name)

    await safe_edit(message, success(f"Deleted → {name}"))


# ================= REGISTER =================
def register(app):
    owner = filters.user(app.owner_id)

    app.add_handler(MessageHandler(store_cmd, filters.command("store", ".") & owner))
    app.add_handler(MessageHandler(get_cmd, filters.command("get", ".") & owner))
    app.add_handler(MessageHandler(list_cmd, filters.command("storelist", ".") & owner))
    app.add_handler(MessageHandler(delete_cmd, filters.command("delstore", ".") & owner))

    help_dict[__MODULE__] = {
        "store <name>": "Save text or media",
        "get <name>": "Retrieve item",
        "storelist": "List stored items",
        "delstore <name>": "Delete item"
    }