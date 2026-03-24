import asyncio
import time
import traceback

from pyrogram import idle

from core.client import app
from core.logger import log
from core.crash import install_crash_handler
from core.loader import load_modules


# =========================
# MAIN
# =========================

async def main():
    print("🚀 Starting Userbot...")

    # crash handler
    install_crash_handler()

    # start client
    await app.start()

    me = await app.get_me()
    app.owner_id = me.id
    app.start_time = time.time()  # 🔥 useful later

    log.info(f"Logged in as: {me.first_name} (@{me.username}) [{me.id}]")

    # load modules
    await load_modules(app)

    print("✅ Bot is running...")
    await idle()

    # graceful shutdown
    await app.stop()
    print("🛑 Bot stopped.")


# =========================
# ENTRY
# =========================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Stopped manually.")
    except Exception:
        print("💥 Fatal error:\n", traceback.format_exc())