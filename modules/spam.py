# modules/spam.py

import asyncio
from pyrogram import filters
from pyrogram.handlers import MessageHandler
from pyrogram.errors import FloodWait

from modules.help import help_dict
from utils.style import error, success, info, safe_edit
from modules.chat_control import is_blocked  # 🔥 LINKED

__MODULE__ = "spam"

MAX_SPAM = 50
ACTIVE_SPAM = {}
COOLDOWN = {}


# ================= HELPERS =================
def get_text(message):
    if message.reply_to_message:
        return message.reply_to_message.text or message.reply_to_message.caption

    if len(message.command) > 2:
        return " ".join(message.command[2:])

    return None


def get_limit(chat_type):
    if chat_type in ["group", "supergroup"]:
        return 20
    return MAX_SPAM


# ================= CORE =================
async def _spam_base(client, message, delay):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # 🔥 chat control
    if await is_blocked(chat_id):
        return await safe_edit(message, error("This chat is blocked"))

    # 🔥 cooldown
    if user_id in COOLDOWN:
        return await safe_edit(message, error("Cooldown active"))

    if len(message.command) < 2:
        return await safe_edit(message, error("Usage: .spam [count] text"))

    try:
        count = int(message.command[1])
    except:
        return await safe_edit(message, error("Invalid count"))

    limit = get_limit(message.chat.type)

    if not (1 <= count <= limit):
        return await safe_edit(message, error(f"Limit: {limit}"))

    text = get_text(message)
    if not text:
        return await safe_edit(message, error("Provide text"))

    ACTIVE_SPAM[user_id] = True
    COOLDOWN[user_id] = True

    status = await safe_edit(message, info("Starting spam..."))

    sent = 0

    for i in range(count):
        if not ACTIVE_SPAM.get(user_id):
            break

        try:
            await client.send_message(chat_id, text)
            sent += 1

        except FloodWait as e:
            await asyncio.sleep(e.value)

        except Exception:
            break

        if (i + 1) % 5 == 0 or (i + 1) == count:
            percent = int(((i + 1) / count) * 100)
            await safe_edit(status, info(f"{percent}%"))

        await asyncio.sleep(delay)

    ACTIVE_SPAM[user_id] = False

    await safe_edit(status, success(f"Done → {sent}/{count}"))

    await asyncio.sleep(5)
    COOLDOWN.pop(user_id, None)


# ================= COMMANDS =================
async def spam_cmd(client, message):
    await _spam_base(client, message, 0.3)


async def fastspam_cmd(client, message):
    await _spam_base(client, message, 0.05)


async def slowspam_cmd(client, message):
    await _spam_base(client, message, 0.9)


async def statspam_cmd(client, message):
    if await is_blocked(message.chat.id):
        return await safe_edit(message, error("Chat blocked"))

    if len(message.command) < 2:
        return await safe_edit(message, error("Usage: .statspam count text"))

    try:
        count = int(message.command[1])
    except:
        return await safe_edit(message, error("Invalid count"))

    text = get_text(message)
    if not text:
        return await safe_edit(message, error("Provide text"))

    status = await safe_edit(message, info("Stat spam..."))

    for _ in range(count):
        try:
            m = await client.send_message(message.chat.id, text)
            await asyncio.sleep(0.15)
            await m.delete()
        except FloodWait as e:
            await asyncio.sleep(e.value)

    await safe_edit(status, success("Done"))


async def stopspam_cmd(client, message):
    ACTIVE_SPAM[message.from_user.id] = False
    await safe_edit(message, success("Stopped"))


# ================= REGISTER =================
def register(app):
    f = filters.me

    app.add_handler(MessageHandler(spam_cmd, filters.command("spam", ".") & f))
    app.add_handler(MessageHandler(fastspam_cmd, filters.command("fastspam", ".") & f))
    app.add_handler(MessageHandler(slowspam_cmd, filters.command("slowspam", ".") & f))
    app.add_handler(MessageHandler(statspam_cmd, filters.command("statspam", ".") & f))
    app.add_handler(MessageHandler(stopspam_cmd, filters.command("stopspam", ".") & f))

    help_dict[__MODULE__] = {
        "spam": "Normal spam",
        "fastspam": "Fast spam",
        "slowspam": "Slow spam",
        "statspam": "Send & delete spam",
        "stopspam": "Stop spam"
    }