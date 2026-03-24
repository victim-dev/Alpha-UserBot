# modules/userinfo.py

import asyncio

from pyrogram import filters
from pyrogram.handlers import MessageHandler
from pyrogram.enums import UserStatus

from modules.help import help_dict
from utils.style import success, error, info, safe_edit, safe_send, title, divider

__MODULE__ = "userinfo"


# ================= HELPER =================
def get_target(message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    if len(message.command) > 1:
        return message.command[1]
    return None


# ================= STATUS =================
def format_status(user):
    if user.status == UserStatus.ONLINE:
        return "🟢 Online"
    elif user.status == UserStatus.OFFLINE:
        return "⚫ Offline"
    elif user.status == UserStatus.RECENTLY:
        return "🕒 Recently"
    elif user.status == UserStatus.LAST_WEEK:
        return "📅 Last week"
    elif user.status == UserStatus.LAST_MONTH:
        return "📆 Last month"
    return "Unknown"


# ================= SANGMATA =================
async def get_sangmata(client, user_id):
    try:
        bot = "SangMata_BOT"

        await client.send_message(bot, str(user_id))
        await asyncio.sleep(2)

        async for m in client.get_chat_history(bot, limit=1):
            if m.text:
                return m.text

        return "No history found"

    except Exception:
        return "Failed to fetch"


# ================= INFO =================
async def info_cmd(client, message):
    target = get_target(message)

    if not target:
        return await safe_edit(message, error("Reply or give username"))

    await safe_edit(message, info("Fetching user info..."))

    try:
        user = await client.get_users(target)
    except Exception as e:
        return await safe_edit(message, error(str(e)))

    # profile photo count (fast)
    photos = 0
    async for _ in client.get_chat_photos(user.id, limit=1):
        photos += 1

    sang = await get_sangmata(client, user.id)

    text = (
        f"{title('User Info')}\n"
        f"{divider()}\n\n"

        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        f"👤 <b>Name:</b> {user.first_name or ''} {user.last_name or ''}\n"
        f"🔗 <b>Username:</b> @{user.username or 'none'}\n\n"

        f"📊 <b>Status:</b> {format_status(user)}\n"
        f"🖼 <b>Photos:</b> {photos}\n\n"

        f"⚙️ <b>Flags</b>\n"
        f"• Premium: {'Yes' if user.is_premium else 'No'}\n"
        f"• Verified: {'Yes' if user.is_verified else 'No'}\n"
        f"• Scam: {'Yes' if user.is_scam else 'No'}\n\n"

        f"📝 <b>Bio</b>\n<code>{user.bio or 'None'}</code>\n\n"

        f"🧬 <b>SangMata</b>\n"
        f"<code>{sang[:1500]}</code>"
    )

    await safe_send(client, message.chat.id, text)


# ================= REGISTER =================
def register(app):
    owner = filters.user(app.owner_id)

    app.add_handler(MessageHandler(info_cmd, filters.command("info", ".") & owner))

    help_dict[__MODULE__] = {
        "info [user/reply]": "Full user info + SangMata"
    }