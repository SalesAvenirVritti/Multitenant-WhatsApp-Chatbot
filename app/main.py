from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = "verify_123"

# --------------------
# Health Check
# --------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# --------------------
# Webhook Verification
# --------------------
@app.get("/webhook")
def verify_webhook(
    hub_mode: str = None,
    hub_challenge: str = None,
    hub_verify_token: str = None
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    return {"error": "Verification failed"}

# --------------------
# Webhook Receiver
# --------------------
@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    print("INCOMING:", data)

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        sender = message["from"]
        text = message["text"]["body"].strip().upper()
    except Exception:
        return {"status": "ignored"}

    if text == "HI":
        send_text(sender, "👋 Hi! Welcome to Jasper’s Market.\nReply MENU to see items.")

    elif text == "MENU":
        send_text(sender, "🛒 Available Items:\n1️⃣ Apples\n2️⃣ Milk\nReply ORDER <item>")

    elif text.startswith("ORDER"):
        item = text.replace("ORDER", "").strip()
        send_text(sender, f"✅ Order confirmed for {item}.\nThank you!")

    else:
        send_text(sender, "Please reply:\nHI\nMENU\nORDER Apples")

    return {"status": "ok"}

# --------------------
# Send Text
# --------------------
def send_text(to, text):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    r = requests.post(url, headers=headers, json=payload)
    print("SEND:", r.text)
