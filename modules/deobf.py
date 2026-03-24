# modules/deobf.py

import base64, zlib, gzip, bz2, lzma, marshal, re, ast, asyncio, os, tempfile
from openai import OpenAI

from pyrogram import filters
from pyrogram.handlers import MessageHandler

from modules.help import help_dict
from utils.style import safe_edit, safe_send, error, info

__MODULE__ = "deobf"

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)

MAX_DEPTH = 20


# ================= SAFE =================
def safe(fn):
    def wrap(d):
        try: return fn(d)
        except: return None
    return wrap


# ================= DECODERS =================
@safe
def reverse(d): return d[::-1]

@safe
def b64(d): return base64.b64decode(d)

@safe
def zlib_d(d): return zlib.decompress(d)

@safe
def gzip_d(d): return gzip.decompress(d)

@safe
def bz2_d(d): return bz2.decompress(d)

@safe
def lzma_d(d): return lzma.decompress(d)

@safe
def marshal_d(d):
    obj = marshal.loads(d)
    return str(obj).encode()

DECODERS = [
    ("reverse", reverse),
    ("base64", b64),
    ("zlib", zlib_d),
    ("gzip", gzip_d),
    ("bz2", bz2_d),
    ("lzma", lzma_d),
    ("marshal", marshal_d),
]


# ================= EXEC INTERCEPT =================
def extract_exec(text):
    patterns = [
        r"exec\((.+)\)",
        r"eval\((.+)\)",
        r"compile\((.+)\)",
    ]

    extracted = []

    for p in patterns:
        matches = re.findall(p, text, re.DOTALL)
        extracted.extend(matches)

    return extracted


# ================= AST CLEAN =================
def clean_ast(code):
    try:
        tree = ast.parse(code)

        class Cleaner(ast.NodeTransformer):
            def visit_Expr(self, node):
                # remove useless exec wrappers
                if isinstance(node.value, ast.Call):
                    if getattr(node.value.func, "id", "") in ["exec", "eval"]:
                        return node.value
                return node

        tree = Cleaner().visit(tree)
        return ast.unparse(tree)

    except:
        return code


# ================= SMART DECODE =================
def atomic_decode(data: bytes):
    current = data
    history = []

    for _ in range(MAX_DEPTH):
        changed = False

        for name, fn in DECODERS:
            result = fn(current)

            if result and result != current:
                current = result
                history.append(name)
                changed = True
                break

        if not changed:
            break

    return current, history


# ================= AI =================
async def ai_rebuild(code: str):
    try:
        def run():
            res = client.chat.completions.create(
                model="minimaxai/minimax-m2.5",
                messages=[{
                    "role": "user",
                    "content": f"""
Fully reverse engineer and clean this Python code.
Remove obfuscation, rename variables meaningfully, simplify logic.

Code:
{code}
"""
                }],
                temperature=0.3,
                max_tokens=4096
            )
            return res.choices[0].message.content

        return await asyncio.wait_for(asyncio.to_thread(run), timeout=40)

    except Exception as e:
        return f"AI Error: {e}"


# ================= INPUT =================
async def get_input(client, message):
    msg = message.reply_to_message
    if not msg:
        return None

    if msg.text:
        return msg.text.encode()

    if msg.document:
        path = await client.download_media(msg)
        with open(path, "rb") as f:
            data = f.read()
        os.remove(path)
        return data


# ================= OUTPUT =================
async def send_output(client, message, content):
    if len(content) < 3500:
        return await safe_edit(message, f"<code>{content}</code>")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
        f.write(content.encode())
        path = f.name

    try:
        await message.delete()
        await client.send_document(message.chat.id, path, caption="☢️ Deobf Output")
    finally:
        os.remove(path)


# ================= COMMAND =================
async def deobf_cmd(client, message):
    raw = await get_input(client, message)
    if not raw:
        return await safe_edit(message, error("Reply to file/text"))

    await safe_edit(message, info("☢️ Atomic decoding..."))

    decoded, layers = atomic_decode(raw)
    text = decoded.decode(errors="ignore")

    # extract hidden payloads
    extracted = extract_exec(text)

    for e in extracted:
        text += "\n\n# ===== EXTRACTED =====\n" + e

    text = clean_ast(text)

    await send_output(client, message, text)


async def deobfai_cmd(client, message):
    raw = await get_input(client, message)
    if not raw:
        return await safe_edit(message, error("Reply to file/text"))

    await safe_edit(message, info("🤖 AI reconstruction..."))

    decoded, _ = atomic_decode(raw)
    text = decoded.decode(errors="ignore")

    result = await ai_rebuild(text)

    await send_output(client, message, result)


# ================= REGISTER =================
def register(app):
    f = filters.user(app.owner_id)

    app.add_handler(MessageHandler(deobf_cmd, filters.command("deobf", ".") & f))
    app.add_handler(MessageHandler(deobfai_cmd, filters.command("deobfai", ".") & f))

    help_dict[__MODULE__] = {
        "deobf": "Atomic multi-layer decode",
        "deobfai": "AI full reverse engineering"
    }