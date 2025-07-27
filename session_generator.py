from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv
import os

load_dotenv()

API_ID = int(os.getenv("28786465"))
API_HASH = os.getenv("0e1a7da683b229cffd9b0614fb6d8ed0")

clients = {}  # Temporarily store clients by user_id


async def start_login(user_id, phone):
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.connect()
    try:
        await client.send_code_request(phone)
        clients[user_id] = (client, phone)
        return True
    except Exception as e:
        return str(e)


async def complete_login(user_id, otp_code):
    if user_id not in clients:
        return "Session expired or invalid."

    client, phone = clients[user_id]
    try:
        await client.sign_in(phone, otp_code)
        string = client.session.save()
        await client.disconnect()
        del clients[user_id]
        return string
    except Exception as e:
        return f"Failed to login: {e}"
