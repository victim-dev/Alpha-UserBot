modules/instareset.py

import re
import uuid
import random
import string
import aiohttp

from pyrogram import filters
from pyrogram.handlers import MessageHandler

from modules.help import help_dict
from utils.style import success, error, info, safe_edit

MODULE = "instareset"

================= HELPERS =================

def random_str(length=16):
return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def random_user_agent():
return f"Instagram 150.0.0.0 Android ({random_str()}; {random_str()}; en_GB;)"

def extract_csrf(html: str):
match = re.search(r'"csrf_token":"(.*?)"', html)
return match.group(1) if match else None

================= REQUEST RESET LINK =================

async def request_reset(session, target):
csrf_token = random_str(32)
device_id = str(uuid.uuid4())
guid = str(uuid.uuid4())

data = {  
    "_csrftoken": csrf_token,  
    "guid": guid,  
    "device_id": device_id  
}  

if "@" in target:  
    data["user_email"] = target  
else:  
    data["username"] = target  

headers = {  
    "User-Agent": random_user_agent(),  
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"  
}  

try:  
    async with session.post(  
        "https://i.instagram.com/api/v1/accounts/send_password_reset/",  
        headers=headers,  
        data=data  
    ) as resp:  
        if resp.status != 200:  
            return None, f"HTTP {resp.status}"  
        result = await resp.json()  
except Exception as e:  
    return None, str(e)  

if "obfuscated_email" in result:  
    return result["obfuscated_email"], None  
if "email" in result:  
    return result["email"], None  
return None, result.get("message", "Unknown error")

================= FULL RESET =================

async def full_reset(session, reset_link):
try:
# Step 1: Open reset page
async with session.get(reset_link) as resp:
html = await resp.text()

if "login" in html.lower():  
        return {"success": False, "error": "Invalid or expired link"}  

    # Step 2: Extract CSRF token  
    csrf = extract_csrf(html)  
    if not csrf:  
        return {"success": False, "error": "Failed to extract CSRF token"}  

    # Step 3: Try to extract username  
    username_match = re.search(r'"username":"(.*?)"', html)  
    username = username_match.group(1) if username_match else "unknown"  

    # Step 4: Generate new password  
    new_password = "Pass" + str(random.randint(1000, 9999))  

    # Step 5: Send reset request  
    payload = {  
        "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:0:{new_password}",  
        "csrfmiddlewaretoken": csrf  
    }  

    headers = {  
        "User-Agent": random_user_agent(),  
        "X-CSRFToken": csrf,  
        "Content-Type": "application/x-www-form-urlencoded"  
    }  

    async with session.post(  
        "https://www.instagram.com/accounts/account_recovery_send_ajax/",  
        data=payload,  
        headers=headers  
    ) as resp:  
        text = await resp.text()  

    # Step 6: Analyse response  
    if "ok" in text.lower() or "success" in text.lower():  
        return {  
            "success": True,  
            "username": username,  
            "password": new_password  
        }  

    return {  
        "success": False,  
        "error": "Reset attempt sent but response unclear"  
    }  

except Exception as e:  
    return {"success": False, "error": str(e)}

================= COMMANDS =================

async def instarequest_cmd(client, message):
if len(message.command) < 2:
return await safe_edit(message, error("Usage: .instarequest <username/email>"))

target = message.command[1]  
await safe_edit(message, info(f"Requesting reset for `{target}`..."))  

async with aiohttp.ClientSession() as session:  
    contact, err = await request_reset(session, target)  

if err:  
    return await safe_edit(message, error(err))  
await safe_edit(message, success(f"Reset link sent to `{contact}`"))

async def instareset_cmd(client, message):
if len(message.command) < 2:
return await safe_edit(message, error("Usage: .instareset <reset_link>"))

link = message.command[1]  
if not link.startswith("https://"):  
    return await safe_edit(message, error("Invalid reset link"))  

await safe_edit(message, info("Attempting password reset..."))  

async with aiohttp.ClientSession() as session:  
    result = await full_reset(session, link)  

if result.get("success"):  
    text = (  
        f"{success('Reset successful')}\n"  
        f"Username: `{result['username']}`\n"  
        f"Password: `{result['password']}`"  
    )  
    await safe_edit(message, text)  
else:  
    await safe_edit(message, error(result.get("error", "Failed")))

================= REGISTER =================

def register(app):
owner = filters.user(app.owner_id)

app.add_handler(MessageHandler(instarequest_cmd, filters.command("instarequest", ".") & owner))  
app.add_handler(MessageHandler(instareset_cmd, filters.command("instareset", ".") & owner))  

help_dict[__MODULE__] = {  
    "instarequest <user/email>": "Request password reset link",  
    "instareset <link>": "Perform password reset"  
}