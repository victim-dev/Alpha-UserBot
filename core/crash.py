import sys
import asyncio
import traceback
import os

from core.logger import get_logger

crash_logger = get_logger("CRASH")

# =========================
# SYNC EXCEPTION HANDLER
# =========================

def crash_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

    crash_logger.critical(
        f"\n💥 Unhandled Exception\n"
        f"Type: {exc_type.__name__}\n"
        f"Error: {exc_value}\n"
        f"Traceback:\n{tb}"
    )

    # Optional restart
    if os.getenv("AUTO_RESTART", "false").lower() == "true":
        crash_logger.warning("🔄 Restarting due to crash...")
        restart_bot()


# =========================
# ASYNC EXCEPTION HANDLER
# =========================

def async_exception_handler(loop, context):
    msg = context.get("exception", context["message"])

    crash_logger.error(
        f"\n⚠️ Async Exception:\n{msg}"
    )


# =========================
# RESTART LOGIC
# =========================

def restart_bot():
    python = sys.executable
    os.execv(python, [python] + sys.argv)


# =========================
# INSTALL HANDLERS
# =========================

def install_crash_handler():
    # Sync exceptions
    sys.excepthook = crash_handler

    # Async exceptions
    try:
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(async_exception_handler)
    except RuntimeError:
        pass