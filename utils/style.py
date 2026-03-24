# utils/style.py

import asyncio
from typing import List

# =========================
# MODULE EMOJIS
# =========================
MODULE_EMOJIS = {
    "account_checker": "🔍",
    "admin": "🛡️",
    "alive": "⚙️",
    "alpha": "🧠",
    "ask": "🤖",
    "chat_control": "🚫",
    "command_list": "📜",
    "deobf": "🧬",
    "dev": "💀",
    "instareset": "🔐",
    "module_manager": "🧩",
    "purge": "🧹",
    "spam": "📣",
    "userinfo": "👤",
    "zerox": "🧬",
}

DIVIDER = "────────────"

# =========================
# COMMAND EMOJI LOGIC
# =========================
def get_cmd_emoji(cmd: str) -> str:
    cmd = cmd.lower()

    if any(x in cmd for x in ["ban", "kick", "mute"]):
        return "🚫"
    if "check" in cmd:
        return "🔎"
    if "spam" in cmd:
        return "📣"
    if any(x in cmd for x in ["purge", "del"]):
        return "🧹"
    if any(x in cmd for x in ["save", "store"]):
        return "💾"
    if any(x in cmd for x in ["load", "get"]):
        return "📥"
    if "reset" in cmd:
        return "♻️"
    if any(x in cmd for x in ["ask", "ai", "alpha"]):
        return "🧠"
    if any(x in cmd for x in ["eval", "sh"]):
        return "💻"
    if any(x in cmd for x in ["info", "id"]):
        return "👤"
    if any(x in cmd for x in ["backup"]):
        return "📦"
    if any(x in cmd for x in ["restart"]):
        return "🔄"

    return "⚡"

# =========================
# BASIC UI
# =========================
def title(text: str) -> str:
    return f"<b>✨ {text}</b>"

def divider() -> str:
    return f"<code>{DIVIDER}</code>"

def success(text: str) -> str:
    return f"✅ {text}"

def error(text: str) -> str:
    return f"❌ <b>{text}</b>"

def info(text: str) -> str:
    return f"ℹ️ {text}"

# =========================
# HELP PANEL (MAIN)
# =========================
def format_main_help(modules: List[str]) -> str:
    lines = [
        title("Help Panel"),
        "",
        "📦 <b>Modules</b>",
    ]

    for mod in sorted(modules):
        emoji = MODULE_EMOJIS.get(mod, "📦")
        lines.append(f"{emoji} <code>{mod}</code>")

    lines.extend([
        "",
        divider(),
        "💡 Use <code>.help module</code>"
    ])

    return "\n".join(lines)

# =========================
# MODULE HELP
# =========================
def format_module_help(module_name: str, commands: dict) -> str:
    emoji = MODULE_EMOJIS.get(module_name, "📦")

    lines = [
        f"{emoji} <b>{module_name}</b>",
        divider(),
        ""
    ]

    for cmd, desc in commands.items():
        cmd_emoji = get_cmd_emoji(cmd)
        lines.append(f"{cmd_emoji} <code>.{cmd}</code>")
        lines.append(f"   {desc}\n")

    return "\n".join(lines)

# =========================
# SAFE EDIT
# =========================
async def safe_edit(message, text: str):
    try:
        return await message.edit(text)
    except:
        try:
            return await message.reply(text)
        except:
            return None

# =========================
# SAFE SEND (LONG TEXT)
# =========================
async def safe_send(client, chat_id, text: str):
    if not text:
        return

    if len(text) < 4000:
        return await client.send_message(chat_id, text)

    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(text.encode())
        path = f.name

    try:
        await client.send_document(chat_id, path, caption="Output too long")
    finally:
        import os
        os.unlink(path)

# =========================
# LOADING ANIMATION
# =========================
async def loading_animation(interval: float = 0.2):
    chars = ["⏳", "⌛", "⏳", "⌛"]
    i = 0
    while True:
        yield chars[i % len(chars)]
        await asyncio.sleep(interval)
        i += 1

# =========================
# AI FORMATTER (FINAL)
# =========================
def format_ai_output(text: str) -> str:
    if not text:
        return text

    # remove markdown
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("`", "")

    lines = text.splitlines()
    cleaned = []

    for line in lines:
        line = line.strip()

        # remove markdown headings
        if line.startswith("#"):
            line = line.lstrip("#").strip()

        # convert lists
        if line.startswith(("-", "*")):
            line = "• " + line[1:].strip()

        # highlight key-value
        if ":" in line and len(line) < 80:
            parts = line.split(":", 1)
            key = parts[0].strip()
            val = parts[1].strip()
            if key and val:
                line = f"<b>{key}:</b> {val}"

        cleaned.append(line)

    text = "\n".join(cleaned)

    # remove excessive blank lines
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")

    return text.strip()

# =========================
# ALPHA HEADER (OPTIONAL)
# =========================
def alpha_header(text: str) -> str:
    return f"🧠 <b>Alpha</b>\n{DIVIDER}\n\n{text}"