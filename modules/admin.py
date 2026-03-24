# modules/admin.py

from pyrogram import filters
from pyrogram.handlers import MessageHandler
from pyrogram.types import ChatPermissions

from modules.help import help_dict
from utils.style import success, error, safe_edit

__MODULE__ = "admin"


# ================= HELPER =================
def get_target(message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    return None


# ================= BAN =================
async def ban_user(client, message):
    user = get_target(message)
    if not user:
        return await safe_edit(message, error("Reply to a user"))

    try:
        await client.ban_chat_member(message.chat.id, user.id)
        await safe_edit(message, success(f"{user.first_name} banned"))
    except Exception as e:
        await safe_edit(message, error(str(e)))


# ================= KICK =================
async def kick_user(client, message):
    user = get_target(message)
    if not user:
        return await safe_edit(message, error("Reply to a user"))

    try:
        await client.ban_chat_member(message.chat.id, user.id)
        await client.unban_chat_member(message.chat.id, user.id)
        await safe_edit(message, success(f"{user.first_name} kicked"))
    except Exception as e:
        await safe_edit(message, error(str(e)))


# ================= MUTE =================
async def mute_user(client, message):
    user = get_target(message)
    if not user:
        return await safe_edit(message, error("Reply to a user"))

    try:
        await client.restrict_chat_member(
            message.chat.id,
            user.id,
            ChatPermissions(can_send_messages=False)
        )
        await safe_edit(message, success(f"{user.first_name} muted"))
    except Exception as e:
        await safe_edit(message, error(str(e)))


# ================= UNMUTE =================
async def unmute_user(client, message):
    user = get_target(message)
    if not user:
        return await safe_edit(message, error("Reply to a user"))

    try:
        await client.restrict_chat_member(
            message.chat.id,
            user.id,
            ChatPermissions(can_send_messages=True)
        )
        await safe_edit(message, success(f"{user.first_name} unmuted"))
    except Exception as e:
        await safe_edit(message, error(str(e)))


# ================= BLOCK (DM) =================
async def block_user(client, message):
    user = get_target(message)
    if not user:
        return await safe_edit(message, error("Reply to a user"))

    try:
        await client.block_user(user.id)
        await safe_edit(message, success(f"{user.first_name} blocked"))
    except Exception as e:
        await safe_edit(message, error(str(e)))


# ================= UNBLOCK =================
async def unblock_user(client, message):
    user = get_target(message)
    if not user:
        return await safe_edit(message, error("Reply to a user"))

    try:
        await client.unblock_user(user.id)
        await safe_edit(message, success(f"{user.first_name} unblocked"))
    except Exception as e:
        await safe_edit(message, error(str(e)))


# ================= REGISTER =================
def register(app):
    f = filters.user(app.owner_id)

    app.add_handler(MessageHandler(ban_user, filters.command("ban", ".") & f))
    app.add_handler(MessageHandler(kick_user, filters.command("kick", ".") & f))
    app.add_handler(MessageHandler(mute_user, filters.command("mute", ".") & f))
    app.add_handler(MessageHandler(unmute_user, filters.command("unmute", ".") & f))

    # 🔥 NEW
    app.add_handler(MessageHandler(block_user, filters.command("block", ".") & f))
    app.add_handler(MessageHandler(unblock_user, filters.command("unblock", ".") & f))

    help_dict[__MODULE__] = {
        "ban [reply]": "Ban user",
        "kick [reply]": "Kick user",
        "mute [reply]": "Mute user",
        "unmute [reply]": "Unmute user",
        "block [reply]": "Block user (DM)",
        "unblock [reply]": "Unblock user"
    }