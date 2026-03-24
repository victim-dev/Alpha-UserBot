# modules/module_manager.py
import os
import asyncio
import aiohttp
from pathlib import Path

from pyrogram import filters
from pyrogram.handlers import MessageHandler

from modules.help import help_dict
from utils.style import success, error, safe_edit

__MODULE__ = "module_manager"

MODULES_DIR = Path("modules")
CRITICAL_MODULES = {"help", "alive", "module_manager"}


# =========================
# RESTART SYSTEM
# =========================
async def _restart_bot():
    """Restart the bot process."""
    import sys
    print("🔄 Restarting bot...")
    await asyncio.sleep(1)
    os.execv(sys.executable, [sys.executable] + sys.argv)


async def _restart_after(message, text):
    """Send message then restart."""
    await safe_edit(message, text)
    await _restart_bot()


# =========================
# UPLOAD MODULE
# =========================
async def upload_module(client, message):
    args = message.command[1:] if len(message.command) > 1 else []
    url = args[0] if args else None
    reply = message.reply_to_message

    # 📥 FROM FILE
    if reply and reply.document and reply.document.file_name.endswith(".py"):
        name = reply.document.file_name.replace(".py", "")

        if name in CRITICAL_MODULES:
            return await safe_edit(message, error("Cannot overwrite core module"))

        await safe_edit(message, "📥 Uploading module...")

        file_path = await reply.download()
        dest = MODULES_DIR / reply.document.file_name
        os.replace(file_path, dest)

        return await _restart_after(
            message,
            success(f"Module `{reply.document.file_name}` uploaded ⚙️\nRestarting...")
        )

    # 🌐 FROM URL
    if url:
        if not (url.endswith(".py") or "raw.githubusercontent.com" in url):
            return await safe_edit(message, error("Invalid Python file URL"))

        await safe_edit(message, "🌐 Downloading module...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return await safe_edit(
                            message,
                            error(f"Failed to fetch URL (status {resp.status})")
                        )
                    content = await resp.text()
        except Exception as e:
            return await safe_edit(message, error(f"Download error: {e}"))

        filename = args[1] if len(args) > 1 else url.split("/")[-1]
        if not filename.endswith(".py"):
            filename = "module.py"

        name = filename.replace(".py", "")

        if name in CRITICAL_MODULES:
            return await safe_edit(message, error("Cannot overwrite core module"))

        dest = MODULES_DIR / filename
        dest.write_text(content, encoding="utf-8")

        return await _restart_after(
            message,
            success(f"Module `{filename}` saved ⚙️\nRestarting...")
        )

    await safe_edit(message, error("Reply to a .py file or provide a raw URL"))


# =========================
# UNLOAD MODULE
# =========================
async def unload_module(client, message):
    args = message.command[1:] if len(message.command) > 1 else []

    if not args:
        return await safe_edit(message, error("Usage: .unloadmodule <module_name>"))

    name = args[0].replace(".py", "")

    if name in CRITICAL_MODULES:
        return await safe_edit(message, error("Cannot unload core module"))

    file_path = MODULES_DIR / f"{name}.py"

    if not file_path.exists():
        return await safe_edit(message, error(f"Module `{name}.py` not found"))

    os.remove(file_path)

    return await _restart_after(
        message,
        success(f"Module `{name}` deleted 🗑️\nRestarting...")
    )


# =========================
# LIST MODULES
# =========================
async def list_modules(client, message):
    files = [f.name for f in MODULES_DIR.glob("*.py") if not f.name.startswith("_")]

    if not files:
        return await safe_edit(message, "No modules found.")

    import sys
    loaded = [m for m in sys.modules if m.startswith("modules.")]
    loaded_names = [m.split(".")[-1] + ".py" for m in loaded]

    text = "📦 <b>Modules</b>\n────────────\n\n"

    for f in sorted(files):
        if f in loaded_names:
            text += f"🟢 <code>{f}</code>\n"
        else:
            text += f"⚪ <code>{f}</code>\n"

    await safe_edit(message, text)


# =========================
# REGISTER
# =========================
def register(app):
    owner = filters.user(app.owner_id)

    app.add_handler(MessageHandler(upload_module, filters.command("uploadmodule", ".") & owner))
    app.add_handler(MessageHandler(unload_module, filters.command("unloadmodule", ".") & owner))
    app.add_handler(MessageHandler(list_modules, filters.command("listmodules", ".") & owner))

    help_dict[__MODULE__] = {
        "uploadmodule <reply/url>": "Upload a module and restart",
        "unloadmodule <module>": "Delete a module and restart",
        "listmodules": "List all modules"
    }