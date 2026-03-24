# modules/chat_control.py

from pyrogram import filters
from pyrogram.handlers import MessageHandler

from utils.db import get, set
from utils.style import success, error, safe_edit
from modules.help import help_dict

__MODULE__ = "chat_control"

COLLECTION = "control"
KEY = "blocked_chats"


# ================= HELPERS =================
async def get_blocked():
    return await get(COLLECTION, KEY, [])


async def is_blocked(chat_id):
    return chat_id in await get_blocked()


# ================= COMMANDS =================
async def blockchat_cmd(client, message):
    chat_id = message.chat.id
    data = await get_blocked()

    if chat_id not in data:
        data.append(chat_id)
        await set(COLLECTION, KEY, data)

    await safe_edit(message, success("🚫 Chat blocked"))


async def unblockchat_cmd(client, message):
    chat_id = message.chat.id
    data = await get_blocked()

    if chat_id in data:
        data.remove(chat_id)
        await set(COLLECTION, KEY, data)

    await safe_edit(message, success("✅ Chat unblocked"))


async def blocked_cmd(client, message):
    data = await get_blocked()

    if not data:
        return await safe_edit(message, "No blocked chats")

    text = "🚫 <b>Blocked Chats</b>\n────────────\n\n"
    for cid in data:
        text += f"• <code>{cid}</code>\n"

    await safe_edit(message, text)


# ================= REGISTER =================
def register(app):
    owner = filters.user(app.owner_id)

    app.add_handler(MessageHandler(blockchat_cmd, filters.command("blockchat", ".") & owner))
    app.add_handler(MessageHandler(unblockchat_cmd, filters.command("unblockchat", ".") & owner))
    app.add_handler(MessageHandler(blocked_cmd, filters.command("blocked", ".") & owner))

    help_dict[__MODULE__] = {
        "blockchat": "Disable bot in this chat",
        "unblockchat": "Enable bot in this chat",
        "blocked": "List blocked chats"
    }