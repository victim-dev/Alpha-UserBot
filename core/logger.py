import logging
import sys
from pathlib import Path

# =========================
# SETUP
# =========================

LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

LOG_FILE = LOGS_DIR / "bot.log"

# =========================
# FORMATTER
# =========================

FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATEFMT = "%Y-%m-%d %H:%M:%S"

formatter = logging.Formatter(FORMAT, DATEFMT)

# =========================
# ROOT LOGGER
# =========================

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# 🚫 Prevent duplicate handlers (VERY IMPORTANT)
if not root_logger.handlers:

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)

    # File handler
    file = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file.setFormatter(formatter)

    root_logger.addHandler(console)
    root_logger.addHandler(file)

# =========================
# FACTORY
# =========================

def get_logger(name: str):
    return logging.getLogger(name)


# Default logger
log = get_logger("main")