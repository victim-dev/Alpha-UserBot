# modules/alpha.py

import asyncio
import time

from pyrogram import filters
from pyrogram.handlers import MessageHandler

from modules.help import help_dict
from utils.style import success, error, info, format_ai_output, alpha_header
from utils.db import get, set
from modules.ask import generate_reply
from modules.chat_control import is_blocked

# 🧬 long-term memory
from utils.alpha_memory import add_memory, extract_facts, get_memory

__MODULE__ = "alpha"

COL = "alpha"


# ================= DEFAULT =================
DEFAULT = {
    "dm": False,
    "mention": True,
    "groups": False,
    "personality": "default",
    "cooldown": 5
}


# ================= STATE =================
async def get_state(uid):
    data = await get(COL, str(uid), {})
    return {**DEFAULT, **data}


async def save_state(uid, data):
    await set(COL, str(uid), data)


# ================= PERSONALITY =================
def apply_personality(text, mode):
    if mode == "savage":
        return f"😏 {text}"
    if mode == "formal":
        return f"📘 {text}"
    if mode == "friendly":
        return f"😊 {text}"
    return text


# ================= COMMAND =================
async def alpha_cmd(client, message):
    uid = message.from_user.id
    state = await get_state(uid)

    if len(message.command) == 1:
        mem = await get_memory(uid)

        return await message.edit(
            f"🧠 <b>Alpha System</b>\n────────────\n\n"
            f"DM: {state['dm']}\n"
            f"Mention: {state['mention']}\n"
            f"Groups: {state['groups']}\n"
            f"Personality: {state['personality']}\n"
            f"Cooldown: {state['cooldown']}s\n"
            f"Memory: {len(mem)} items\n\n"
            f"Usage:\n"
            f".alpha dm on/off\n"
            f".alpha mention on/off\n"
            f".alpha groups on/off\n"
            f".alpha personality [default/savage/friendly/formal]\n"
            f".alpha cooldown <sec>"
        )

    key = message.command[1].lower()

    # toggles
    if key in ["dm", "mention", "groups"]:
        val = message.command[2].lower()
        if val not in ["on", "off"]:
            return await message.edit(error("Use on/off"))

        state[key] = val == "on"
        await save_state(uid, state)
        return await message.edit(success(f"{key} → {val}"))

    # personality
    if key == "personality":
        val = message.command[2].lower()
        state["personality"] = val
        await save_state(uid, state)
        return await message.edit(success(f"Personality → {val}"))

    # cooldown
    if key == "cooldown":
        try:
            sec = int(message.command[2])
        except:
            return await message.edit(error("Invalid number"))

        state["cooldown"] = max(1, sec)
        await save_state(uid, state)
        return await message.edit(success(f"Cooldown → {sec}s"))

    return await message.edit(error("Invalid option"))


# ================= RUNTIME =================
LAST_REPLY = {}


async def alpha_handler(client, message):
    if not message.from_user or not message.text:
        return

    uid = client.owner_id
    state = await get_state(uid)

    # ignore self
    if message.from_user.id == uid:
        return

    # blocked chat
    if await is_blocked(message.chat.id):
        return

    # ================= MODE =================
    if message.chat.type == "private":
        if not state["dm"]:
            return

    elif message.chat.type in ["group", "supergroup"]:
        if not state["groups"]:
            return

        if state["mention"] and not message.mentioned:
            return

    # ================= COOLDOWN =================
    now = time.time()
    last = LAST_REPLY.get(message.chat.id, 0)

    if now - last < state["cooldown"]:
        return

    LAST_REPLY[message.chat.id] = now

    # ================= MEMORY LEARNING =================
    fact = extract_facts(message.text)
    if fact:
        await add_memory(uid, fact)

    # ================= AI =================
    try:
        reply = await asyncio.wait_for(
            generate_reply(uid, message.text),
            timeout=25
        )
    except:
        return

    if not reply:
        return

    # personality
    reply = apply_personality(reply, state["personality"])

    # formatting
    reply = format_ai_output(reply)
    reply = alpha_header(reply)

    if len(reply) > 4000:
        reply = reply[:3900] + "\n\n⚠️ truncated"

    try:
        await message.reply(reply)
    except:
        pass


# ================= REGISTER =================
def register(app):
    owner = filters.user(app.owner_id)

    app.add_handler(
        MessageHandler(alpha_cmd, filters.command("alpha", ".") & owner)
    )

    app.add_handler(
        MessageHandler(alpha_handler, filters.text & ~filters.me)
    )

    help_dict[__MODULE__] = {
        "alpha": "Control Alpha system",
        "alpha dm on/off": "Enable DM replies",
        "alpha mention on/off": "Reply on mention",
        "alpha groups on/off": "Enable in groups",
        "alpha personality": "Set personality",
        "alpha cooldown": "Set delay"
    }