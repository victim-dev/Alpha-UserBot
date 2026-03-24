import os
from pyrogram import Client
from pyrogram.enums import ParseMode
from dotenv import load_dotenv

# =========================
# LOAD ENV
# =========================

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME", "my_userbot")

# =========================
# VALIDATION
# =========================

if not API_ID or not API_HASH:
    raise RuntimeError("❌ API_ID and API_HASH must be set in .env")

try:
    API_ID = int(API_ID)
except ValueError:
    raise RuntimeError("❌ API_ID must be an integer")

# =========================
# CLIENT CONFIG
# =========================

app = Client(
    name=SESSION_NAME,
    api_id=API_ID,
    api_hash=API_HASH,
    parse_mode=ParseMode.HTML,
    workdir=".",

    # 🔥 performance tweaks
    sleep_threshold=60,
    workers=8,
    in_memory=False
)

# =========================
# EXTRA ATTRIBUTES
# =========================

# Will be set dynamically in main.py
app.owner_id = None
app.start_time = None