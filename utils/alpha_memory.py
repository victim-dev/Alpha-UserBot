# utils/alpha_memory.py

from utils.db import get, set

COL = "alpha_memory"


async def get_memory(uid):
    return await get(COL, str(uid), [])


async def add_memory(uid, text):
    data = await get_memory(uid)

    if text not in data:
        data.append(text)

    # limit memory
    data = data[-20:]

    await set(COL, str(uid), data)


def extract_facts(text: str):
    keywords = ["i like", "i love", "i hate", "my", "i am"]

    text_l = text.lower()

    for k in keywords:
        if k in text_l:
            return text.strip()

    return None