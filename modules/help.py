from pyrogram import filters
from pyrogram.handlers import MessageHandler

from utils.style import (
    format_main_help,
    format_module_help,
    error,
    safe_edit
)

__MODULE__ = "help"

# Global dictionary
help_dict = {}


# =========================
# FIND MODULE (SMART MATCH 🔥)
# =========================
def find_module(name: str):
    name = name.lower()

    # exact match
    if name in help_dict:
        return name

    # partial match
    matches = [m for m in help_dict if name in m]

    if len(matches) == 1:
        return matches[0]

    return None


# =========================
# HELP COMMAND
# =========================
async def help_command(client, message):
    args = message.command[1:] if len(message.command) > 1 else []

    # =========================
    # MAIN HELP
    # =========================
    if not args:
        modules = sorted(help_dict.keys())
        text = format_main_help(modules)
        return await safe_edit(message, text)

    # =========================
    # MODULE HELP
    # =========================
    query = args[0].lower()
    module_name = find_module(query)

    if module_name:
        text = format_module_help(module_name, help_dict[module_name])
        return await safe_edit(message, text)

    # =========================
    # NOT FOUND (SMART UX 🔥)
    # =========================
    suggestions = [m for m in help_dict if query in m]

    if suggestions:
        text = "❌ <b>Module not found</b>\n\nDid you mean:\n"
        for s in suggestions[:5]:
            text += f"• <code>{s}</code>\n"
    else:
        text = error(f"Module '{query}' not found")

    await safe_edit(message, text)


# =========================
# REGISTER
# =========================
def register(app):
    app.add_handler(
        MessageHandler(
            help_command,
            filters.command("help", prefixes=".") & filters.user(app.owner_id)
        )
    )