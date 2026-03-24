# modules/acc.py

import asyncio
import aiohttp

from pyrogram import filters
from pyrogram.handlers import MessageHandler

from modules.help import help_dict
from utils.style import success, error, info, safe_edit

__MODULE__ = "acc"


# =========================
# CORE FETCH
# =========================
async def fetch(session, method, url, **kwargs):
    try:
        async with session.request(method, url, **kwargs) as resp:
            return await resp.text()
    except Exception:
        return None


# =========================
# CHECK LOGIC
# =========================
async def check_gmail(session, username):
    url = f"https://mail.google.com/mail/gxlu?email={username}"
    data = await fetch(session, "GET", url)

    if not data:
        return "❌ Request failed"

    return "✅ Available" if "is available" in data.lower() else "❌ Taken"


async def check_aol(session, username):
    url = f"https://login.aol.com/account/module/create?validateField=yid&yid={username}"
    data = await fetch(session, "GET", url)

    if not data:
        return "❌ Request failed"

    return "❌ Taken" if "error" in data.lower() else "✅ Available"


async def check_instagram(session, value):
    url = "https://www.instagram.com/api/v1/web/accounts/login/ajax/"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-Requested-With": "XMLHttpRequest"
    }

    payload = {
        "username": value,
        "enc_password": "#PWD_INSTAGRAM_BROWSER:0:0:password"
    }

    try:
        async with session.post(url, headers=headers, data=payload) as resp:
            text = await resp.text()
    except Exception:
        return "❌ Request failed"

    if "user" in text:
        return "✅ Exists"
    return "❌ Not found"


# =========================
# UNIFIED COMMAND 🔥
# =========================
async def acc_cmd(client, message):
    args = message.command[1:]

    if len(args) < 2:
        return await safe_edit(
            message,
            error("Usage: .acc <gmail/aol/ig/all> <username>")
        )

    mode = args[0].lower()
    username = args[1]

    await safe_edit(message, info(f"Checking `{username}` on `{mode}`..."))

    async with aiohttp.ClientSession() as session:

        if mode == "gmail":
            result = await check_gmail(session, username)

        elif mode == "aol":
            result = await check_aol(session, username)

        elif mode == "ig":
            result = await check_instagram(session, username)

        elif mode == "all":
            gmail, aol, ig = await asyncio.gather(
                check_gmail(session, username),
                check_aol(session, username),
                check_instagram(session, username)
            )

            text = (
                f"🔍 Results for `{username}`\n\n"
                f"📧 Gmail → {gmail}\n"
                f"📮 AOL → {aol}\n"
                f"📸 Instagram → {ig}"
            )

            return await safe_edit(message, text)

        else:
            return await safe_edit(message, error("Invalid type"))

    await safe_edit(message, success(f"{mode.upper()} `{username}` → {result}"))


# =========================
# REGISTER
# =========================
def register(app):
    app.add_handler(
        MessageHandler(acc_cmd, filters.command("acc", ".") & filters.me)
    )

    help_dict[__MODULE__] = {
        "acc gmail <user>": "Check Gmail availability",
        "acc aol <user>": "Check AOL availability",
        "acc ig <user>": "Check Instagram existence",
        "acc all <user>": "Check all services"
    }