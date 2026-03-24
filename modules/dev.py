# modules/dev.py (ATOMIC)

import os
import sys
import asyncio
import zipfile
import aiohttp
import tempfile
from pathlib import Path

from pyrogram import filters
from pyrogram.handlers import MessageHandler

from utils.style import success, error, info, safe_edit, safe_send
from utils.db import get, set

__MODULE__ = "dev"

BASE = Path(".").resolve()
MODULES = (BASE / "modules").resolve()
UTILS = (BASE / "utils").resolve()

CRITICAL = {"dev.py", "alive.py", "ask.py"}
LOCK = "dev_lock"


# ================= SECURITY =================
async def is_unlocked(uid):
    return await get(LOCK, str(uid), False)

async def require(uid):
    return await is_unlocked(uid)


def safe_path(p: str):
    path = (BASE / p).resolve()
    if str(path).startswith(str(MODULES)) or str(path).startswith(str(UTILS)):
        return path
    return None


# ================= LOCK =================
async def devlock(client, m):
    pw = m.command[1] if len(m.command) > 1 else None
    if not pw:
        return await safe_edit(m, error("Usage: .devlock <pass>"))
    await set(LOCK, "pw", pw)
    await safe_edit(m, success("Locked"))

async def devunlock(client, m):
    pw = m.command[1] if len(m.command) > 1 else None
    saved = await get(LOCK, "pw", None)
    if pw != saved:
        return await safe_edit(m, error("Wrong password"))
    await set(LOCK, str(m.from_user.id), True)
    await safe_edit(m, success("Unlocked"))


# ================= FILE =================
async def ls_cmd(client, m):
    if not await require(m.from_user.id): return
    path = safe_path(m.command[1]) if len(m.command) > 1 else MODULES
    if not path: return await safe_edit(m, error("Invalid path"))

    text = "📂 Files\n────────\n\n"
    for f in path.iterdir():
        icon = "📁" if f.is_dir() else "📄"
        text += f"{icon} <code>{f.name}</code>\n"

    await safe_send(client, m.chat.id, text)


async def tree_cmd(client, m):
    if not await require(m.from_user.id): return

    def build(p, pre=""):
        out = []
        for x in p.iterdir():
            out.append(f"{pre}├─ {x.name}")
            if x.is_dir():
                out += build(x, pre + "│  ")
        return out

    tree = "\n".join(build(MODULES))
    await safe_send(client, m.chat.id, f"<code>{tree}</code>")


async def delete_cmd(client, m):
    if not await require(m.from_user.id): return
    if len(m.command) < 2:
        return await safe_edit(m, error("Usage: .delete path"))

    path = safe_path(m.command[1])
    if not path or not path.exists():
        return await safe_edit(m, error("Invalid"))

    if path.name in CRITICAL:
        return await safe_edit(m, error("Protected file"))

    path.unlink()
    await safe_edit(m, success("Deleted"))


async def read_cmd(client, m):
    if not await require(m.from_user.id): return
    path = safe_path(m.command[1])
    if not path:
        return await safe_edit(m, error("Invalid path"))

    data = path.read_text()[:4000]
    await safe_send(client, m.chat.id, f"<code>{data}</code>")


async def write_cmd(client, m):
    if not await require(m.from_user.id): return
    if not m.reply_to_message:
        return await safe_edit(m, error("Reply with content"))

    path = safe_path(m.command[1])
    if not path:
        return await safe_edit(m, error("Invalid path"))

    path.write_text(m.reply_to_message.text)
    await safe_edit(m, success("Written"))


# ================= SHELL =================
async def sh_cmd(client, m):
    if not await require(m.from_user.id): return
    if len(m.command) < 2:
        return await safe_edit(m, error("Usage: .sh cmd"))

    cmd = m.text.split(None, 1)[1]

    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=10)
    except asyncio.TimeoutError:
        proc.kill()
        return await safe_edit(m, error("Timeout"))

    res = (out + err).decode()[:4000] or "No output"
    await safe_send(client, m.chat.id, f"<code>{res}</code>")


# ================= EVAL =================
async def eval_cmd(client, m):
    if not await require(m.from_user.id): return
    if len(m.command) < 2:
        return await safe_edit(m, error("Usage: .eval code"))

    code = m.text.split(None, 1)[1]

    try:
        exec_locals = {}
        exec(code, {}, exec_locals)
        res = str(exec_locals)[:4000]
    except Exception as e:
        res = str(e)

    await safe_send(client, m.chat.id, f"<code>{res}</code>")


# ================= BACKUP =================
async def backup_cmd(client, m):
    if not await require(m.from_user.id): return

    z = "backup.zip"
    with zipfile.ZipFile(z, "w") as zipf:
        for root, _, files in os.walk(BASE):
            for f in files:
                zipf.write(os.path.join(root, f))

    await m.reply_document(z)


# ================= RESTART =================
async def restart_cmd(client, m):
    if not await require(m.from_user.id): return
    await safe_edit(m, success("Restarting"))
    os.execv(sys.executable, [sys.executable] + sys.argv)


# ================= REGISTER =================
def register(app):
    owner = filters.user(app.owner_id)

    cmds = [
        ("devlock", devlock),
        ("devunlock", devunlock),
        ("ls", ls_cmd),
        ("tree", tree_cmd),
        ("delete", delete_cmd),
        ("read", read_cmd),
        ("write", write_cmd),
        ("sh", sh_cmd),
        ("eval", eval_cmd),
        ("backup", backup_cmd),
        ("restart", restart_cmd),
    ]

    for name, func in cmds:
        app.add_handler(MessageHandler(func, filters.command(name, ".") & owner))