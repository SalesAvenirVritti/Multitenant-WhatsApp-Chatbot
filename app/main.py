from fastapi import FastAPI, Request
import requests
from app.deps import get_db
from app.models import Tenant

VERIFY_TOKEN = "verify_123"
WHATSAPP_TOKEN = "YOUR_PERMANENT_OR_TEMP_TOKEN"
PHONE_NUMBER_ID = "958320700693461"

app = FastAPI()

# -------------------------------------------------
# Webhook verification (Meta calls this FIRST)
# -------------------------------------------------
@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = None,
    hub_challenge: str = None,
    hub_verify_token: str = None
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    return {"error": "verification failed"}

# -------------------------------------------------
# Incoming WhatsApp messages
# -------------------------------------------------
@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    print("🔥 WEBHOOK RECEIVED:", data)

    try:
        value = data["entry"][0]["changes"][0]["value"]
        message = value["messages"][0]
        phone = message["from"]
        text = message["text"]["body"]
    except Exception:
        return {"status": "ignored"}

    db = next(get_db())
    tenant = db.query(Tenant).first()

    reply = f"You said: {text}"

    send_whatsapp_message(phone, reply)
    return {"status": "sent"}

# -------------------------------------------------
def send_whatsapp_message(to: str, text: str):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    requests.post(url, headers=headers, json=payload)
