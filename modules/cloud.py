# modules/cloud.py

import os
import json
import asyncio
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

from pyrogram import filters
from pyrogram.handlers import MessageHandler

from utils.db import get, set
from modules.help import help_dict
from utils.style import success, error, info, safe_edit

__MODULE__ = "cloud"

load_dotenv()

GMAIL = os.getenv("GMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

COLLECTION = "config"
MODE_KEY = "storage_mode"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465


# ================= MODE =================
async def get_mode():
    return await get(COLLECTION, MODE_KEY, "both")


async def set_mode(mode):
    await set(COLLECTION, MODE_KEY, mode)


# ================= GMAIL SEND =================
async def send_email(subject, body):
    if not GMAIL or not APP_PASSWORD:
        return False, "Gmail not configured"

    msg = EmailMessage()
    msg["From"] = GMAIL
    msg["To"] = GMAIL
    msg["Subject"] = subject
    msg.set_content(body)

    def _send():
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as smtp:
            smtp.login(GMAIL, APP_PASSWORD)
            smtp.send_message(msg)

    try:
        await asyncio.to_thread(_send)
        return True, None
    except Exception as e:
        return False, str(e)


# ================= RETRY WRAPPER =================
async def send_with_retry(subject, body, retries=2):
    for attempt in range(retries + 1):
        ok, err = await send_email(subject, body)
        if ok:
            return True, None

        await asyncio.sleep(1)

    return False, err


# ================= CLOUD SAVE =================
async def cloud_save(name, data):
    mode = await get_mode()

    # skip if cloud disabled
    if mode not in ["cloud", "both"]:
        return True, "Cloud skipped"

    # structured payload
    payload = {
        "name": name,
        "data": data
    }

    subject = f"STORE::{name}"
    body = json.dumps(payload, indent=2)

    ok, err = await send_with_retry(subject, body)

    if not ok:
        return False, f"Gmail failed: {err}"

    return True, "Cloud synced"


# ================= COMMANDS =================
async def setmode_cmd(client, message):
    if len(message.command) < 2:
        return await safe_edit(message, error("Usage: .setmode <mongo/cloud/both>"))

    mode = message.command[1].lower()

    if mode not in ["mongo", "cloud", "both"]:
        return await safe_edit(message, error("Invalid mode"))

    await set_mode(mode)
    await safe_edit(message, success(f"Mode set → {mode}"))


async def mode_cmd(client, message):
    mode = await get_mode()
    await safe_edit(message, info(f"Current mode → {mode}"))


# ================= REGISTER =================
def register(app):
    owner = filters.user(app.owner_id)

    app.add_handler(MessageHandler(setmode_cmd, filters.command("setmode", ".") & owner))
    app.add_handler(MessageHandler(mode_cmd, filters.command("mode", ".") & owner))

    help_dict[__MODULE__] = {
        "setmode <mongo/cloud/both>": "Set storage backend",
        "mode": "Show current storage mode"
    }