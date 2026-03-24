# modules/ask.py

import os
import asyncio
from openai import OpenAI

from pyrogram import filters
from pyrogram.handlers import MessageHandler

from modules.help import help_dict
from utils.style import success, error, info, safe_edit, format_ai_output
from utils.db import get, set, delete

__MODULE__ = "ask"

# ================= CONFIG =================
API_KEY = os.getenv("NVIDIA_API_KEY")
API_BASE = os.getenv("API_BASE", "https://integrate.api.nvidia.com/v1")
MODEL = os.getenv("MODEL", "minimaxai/minimax-m2.5")

if not API_KEY:
    raise RuntimeError("NVIDIA_API_KEY not set")

client = OpenAI(base_url=API_BASE, api_key=API_KEY)

MAX_MEMORY = 10
REQUEST_TIMEOUT = 30

AI_COLLECTION = "ai_memory"


# ================= MEMORY =================
async def get_memory(user_id):
    return await get(AI_COLLECTION, str(user_id), [])


async def save_memory(user_id, memory):
    trimmed = memory[-MAX_MEMORY:]
    await set(AI_COLLECTION, str(user_id), trimmed)


async def clear_memory(user_id):
    await delete(AI_COLLECTION, str(user_id))


# ================= AI CORE =================
async def generate_reply(user_id, prompt):
    memory = await get_memory(user_id)

    # 🧠 SYSTEM PROMPT (Alpha identity)
    messages = [
        {
            "role": "system",
            "content": (
                "You are Alpha, a smart and adaptive AI assistant. "
                "Respond clearly, concisely, and naturally. "
                "Do NOT use markdown like **, __, #, or code blocks. "
                "Use simple structured text with short paragraphs or lists."
            )
        }
    ] + memory + [
        {"role": "user", "content": prompt}
    ]

    try:
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model=MODEL,
            messages=messages,
            temperature=0.6,
            max_tokens=1000
        )

        reply = response.choices[0].message.content.strip()
        reply = format_ai_output(reply)

    except Exception as e:
        return f"❌ AI Error: {str(e)[:100]}"

    # 🧠 save memory
    messages.append({"role": "assistant", "content": reply})
    await save_memory(user_id, messages)

    return reply


# ================= COMMAND =================
async def ask_cmd(client_app, message):
    if len(message.command) < 2:
        return await safe_edit(message, error("Usage: .ask <question>"))

    prompt = message.text.split(None, 1)[1].strip()
    if not prompt:
        return await safe_edit(message, error("Empty query"))

    status = await safe_edit(message, info("🧠 Alpha thinking..."))

    try:
        reply = await asyncio.wait_for(
            generate_reply(message.from_user.id, prompt),
            timeout=REQUEST_TIMEOUT
        )
    except asyncio.TimeoutError:
        return await safe_edit(status, error("AI timeout"))

    if len(reply) > 4000:
        reply = reply[:3900] + "\n\n⚠️ truncated"

    await safe_edit(status, f"🧠 <b>Alpha</b>\n────────────\n\n{reply}")


# ================= RESET =================
async def resetai_cmd(client_app, message):
    await clear_memory(message.from_user.id)
    await safe_edit(message, success("Memory cleared"))


# ================= REGISTER =================
def register(app):
    owner = filters.user(app.owner_id)

    app.add_handler(
        MessageHandler(ask_cmd, filters.command("ask", ".") & owner)
    )

    app.add_handler(
        MessageHandler(resetai_cmd, filters.command("resetai", ".") & owner)
    )

    help_dict[__MODULE__] = {
        "ask <text>": "Ask Alpha (memory enabled)",
        "resetai": "Clear Alpha memory"
    }