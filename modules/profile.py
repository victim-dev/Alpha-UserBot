# modules/profile.py

import os
import tempfile
import base64

from pyrogram import filters
from pyrogram.handlers import MessageHandler
from pyrogram.raw import functions

from utils.db import get, set
from modules.help import help_dict
from utils.style import success, error, safe_edit

__MODULE__ = "profile"

COLLECTION = "profiles"


# ================= SAVE PROFILE =================
async def save_current_profile(client, key="default"):
    me = await client.get_me()

    full = await client.invoke(
        functions.users.GetFullUser(id=await client.resolve_peer(me.id))
    )

    photo_bytes = None

    async for photo in client.get_chat_photos("me"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            await client.download_media(photo.file_id, tmp.name)

        with open(tmp.name, "rb") as f:
            photo_bytes = base64.b64encode(f.read()).decode()

        os.remove(tmp.name)
        break

    data = {
        "first_name": me.first_name or "",
        "last_name": me.last_name or "",
        "bio": full.full_user.about or "",
        "photo": photo_bytes
    }

    await set(COLLECTION, key, data)


# ================= LOAD PROFILE =================
async def load_profile(client, data):
    try:
        await client.update_profile(
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            bio=data.get("bio", "")
        )

        current = [p async for p in client.get_chat_photos("me")]
        if current:
            await client.delete_profile_photos([p.file_id for p in current])

        if data.get("photo"):
            photo_bytes = base64.b64decode(data["photo"])

            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                tmp.write(photo_bytes)

            await client.set_profile_photo(photo=tmp.name)
            os.remove(tmp.name)

        return True

    except Exception as e:
        return str(e)


# ================= COMMANDS =================
async def saveop(client, message):
    slot = message.command[1] if len(message.command) > 1 else "default"

    await save_current_profile(client, slot)
    await safe_edit(message, success(f"Saved → {slot}"))


async def loadop(client, message):
    if len(message.command) < 2:
        return await safe_edit(message, error("Usage: .loadop <slot>"))

    data = await get(COLLECTION, message.command[1])

    if not data:
        return await safe_edit(message, error("No saved profile"))

    result = await load_profile(client, data)

    if result is True:
        await safe_edit(message, success("Profile loaded"))
    else:
        await safe_edit(message, error(result))


async def revert(client, message):
    data = await get(COLLECTION, "default")

    if not data:
        return await safe_edit(message, error("No default backup"))

    result = await load_profile(client, data)

    if result is True:
        await safe_edit(message, success("Reverted"))
    else:
        await safe_edit(message, error(result))


# ================= REGISTER =================
def register(app):
    owner = filters.user(app.owner_id)

    app.add_handler(MessageHandler(saveop, filters.command("saveop", ".") & owner))
    app.add_handler(MessageHandler(loadop, filters.command("loadop", ".") & owner))
    app.add_handler(MessageHandler(revert, filters.command("revert", ".") & owner))

    help_dict[__MODULE__] = {
        "saveop [slot]": "Save current profile",
        "loadop <slot>": "Load saved profile",
        "revert": "Restore default profile"
    }