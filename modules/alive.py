# modules/alive.py

import platform
import time
import psutil

from pyrogram import filters
from pyrogram.handlers import MessageHandler

from modules.help import help_dict
from utils.style import safe_edit

# 🔥 IMPORT LOADER STATE
from core.loader import LOADED_MODULES, FAILED_MODULES

__MODULE__ = "alive"

START_TIME = time.time()


# ================= SYSTEM INFO =================
def get_uptime():
    seconds = int(time.time() - START_TIME)
    mins, sec = divmod(seconds, 60)
    hrs, mins = divmod(mins, 60)
    return f"{hrs}h {mins}m {sec}s"


def get_system():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    return cpu, ram


# ================= ALIVE PANEL =================
async def alive_cmd(client, message):
    me = await client.get_me()

    uptime = get_uptime()
    cpu, ram = get_system()

    total = len(LOADED_MODULES) + len(FAILED_MODULES)

    # 🔥 Format failed modules nicely
    failed_text = (
        ", ".join(FAILED_MODULES)
        if FAILED_MODULES else "None"
    )

    text = (
        f"<b>🤖 {me.first_name} is alive</b>\n"
        f"<code>────────────</code>\n\n"

        f"👤 <b>User:</b> @{me.username or 'none'}\n"
        f"🆔 <b>ID:</b> <code>{me.id}</code>\n\n"

        f"⚙️ <b>System</b>\n"
        f"• OS: <code>{platform.system()}</code>\n"
        f"• Python: <code>{platform.python_version()}</code>\n\n"

        f"📊 <b>Stats</b>\n"
        f"• CPU: <code>{cpu}%</code>\n"
        f"• RAM: <code>{ram}%</code>\n"
        f"• Uptime: <code>{uptime}</code>\n\n"

        f"📦 <b>Modules</b>\n"
        f"• Loaded: <code>{len(LOADED_MODULES)}</code>\n"
        f"• Failed: <code>{len(FAILED_MODULES)}</code>\n"
        f"• Total: <code>{total}</code>\n"
        f"• Failed Names: <code>{failed_text}</code>\n\n"

        f"✨ <i>System running smoothly</i>"
    )

    await safe_edit(message, text)


# ================= EXTRA COMMAND =================
async def sys_cmd(client, message):
    cpu, ram = get_system()

    text = (
        f"<b>⚙️ System Info</b>\n"
        f"<code>────────────</code>\n\n"

        f"💻 OS: <code>{platform.platform()}</code>\n"
        f"🐍 Python: <code>{platform.python_version()}</code>\n\n"

        f"📊 CPU: <code>{cpu}%</code>\n"
        f"📊 RAM: <code>{ram}%</code>\n"
    )

    await safe_edit(message, text)


# ================= REGISTER =================
def register(app):
    owner = filters.user(app.owner_id)

    app.add_handler(MessageHandler(alive_cmd, filters.command("alive", ".") & owner))
    app.add_handler(MessageHandler(sys_cmd, filters.command("sys", ".") & owner))

    help_dict[__MODULE__] = {
        "alive": "Show system dashboard + module status",
        "sys": "Detailed system info"
    }