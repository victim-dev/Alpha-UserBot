# modules/purge.py

import asyncio
from pyrogram import filters
from pyrogram.handlers import MessageHandler

from modules.help import help_dict
from utils.style import success, error, info, safe_edit

__MODULE__ = "purge"


# ================= DELETE SINGLE =================
async def del_msg(client, message):
    if not message.reply_to_message:
        return await safe_edit(message, error("Reply to delete"))

    try:
        await message.reply_to_message.delete()
        await message.delete()
    except Exception as e:
        await safe_edit(message, error(str(e)))


# ================= PURGE =================
async def purge(client, message):
    if not message.reply_to_message:
        return await safe_edit(message, error("Reply to start purge"))

    start_id = message.reply_to_message.id
    await safe_edit(message, info("Purging..."))

    chunk = []

    async for m in client.get_chat_history(message.chat.id):
        if m.id < start_id:
            break

        chunk.append(m.id)

        if len(chunk) >= 100:
            await client.delete_messages(message.chat.id, chunk)
            chunk.clear()
            await asyncio.sleep(0.4)  # slightly faster

    if chunk:
        await client.delete_messages(message.chat.id, chunk)

    await message.delete()


# ================= DELETE ALL =================
async def allme(client, message):
    if len(message.command) < 2 or message.command[1] != "confirm":
        return await safe_edit(
            message,
            "⚠️ <b>This will delete ALL your messages.</b>\n"
            "Use: <code>.allme confirm</code>"
        )

    await safe_edit(message, info("Scanning..."))

    ids = []

    async for m in client.get_chat_history(message.chat.id):
        if m.outgoing:
            ids.append(m.id)

    total = len(ids)
    await safe_edit(message, info(f"Deleting {total} messages..."))

    chunk = []

    for i in ids:
        chunk.append(i)

        if len(chunk) >= 100:
            await client.delete_messages(message.chat.id, chunk)
            chunk.clear()
            await asyncio.sleep(0.4)

    if chunk:
        await client.delete_messages(message.chat.id, chunk)

    await message.delete()


# ================= REGISTER =================
def register(app):
    f = filters.user(app.owner_id)

    app.add_handler(MessageHandler(del_msg, filters.command("del", ".") & f))
    app.add_handler(MessageHandler(purge, filters.command("purge", ".") & f))
    app.add_handler(MessageHandler(allme, filters.command("allme", ".") & f))

    help_dict[__MODULE__] = {
        "del [reply]": "Delete message",
        "purge [reply]": "Delete messages from reply",
        "allme confirm": "Delete ALL your messages"
    }