# core/loader.py

import importlib
import traceback
from pathlib import Path
from core.logger import get_logger

log = get_logger("LOADER")

MODULES_PATH = Path("modules")

# 🔥 ADD THIS GLOBAL STATE
LOADED_MODULES = []
FAILED_MODULES = []


async def load_modules(client):
    global LOADED_MODULES, FAILED_MODULES

    LOADED_MODULES.clear()
    FAILED_MODULES.clear()

    loaded = 0
    failed = 0

    for file in MODULES_PATH.glob("*.py"):
        if file.name.startswith("_"):
            continue

        module_name = file.stem

        try:
            module = importlib.import_module(f"modules.{module_name}")
            if hasattr(module, "register"):
                module.register(client)
                log.info(f"[✓] Loaded: {file.name}")
                LOADED_MODULES.append(module_name)
                loaded += 1
            else:
                log.warning(f"[!] No register(): {file.name}")
                FAILED_MODULES.append(module_name)
                failed += 1

        except Exception:
            log.error(f"[✗] Failed: {file.name}\n{traceback.format_exc()}")
            FAILED_MODULES.append(module_name)
            failed += 1

    log.info(f"Modules Loaded: {loaded} | Failed: {failed}")