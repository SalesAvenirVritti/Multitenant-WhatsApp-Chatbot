from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

# ===============================
# CONFIG
# ===============================
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN") or "PASTE_ACCESS_TOKEN"
PHONE_NUMBER_ID = "958320700693461"
VERIFY_TOKEN = "verify_123"

# ===============================
# HEALTH
# ===============================
@app.get("/health")
def health():
    return {"status": "ok"}

# ===============================
# WEBHOOK VERIFY (META)
# ===============================
@app.get("/webhook")
def verify(
    hub_mode: str = None,
    hub_challenge: str = None,
    hub_verify_token: str = None,
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    return "Verification failed", 403

# ===============================
# RECEIVE MESSAGE
# ===============================
@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    print("INCOMING:", data)

    try:
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
        phone = msg["from"]
        text = msg["text"]["body"].strip().upper()
    except Exception:
        return {"status": "ignored"}

    if text == "HI":
        send_text(phone, "👋 Hi! Restaurant bot is LIVE.\nReply MENU")

    elif text == "MENU":
        send_text(phone, "🍕 MENU:\n1️⃣ Pizza\nReply ITEM PIZZA")

    elif text.startswith("ITEM"):
        send_text(phone, "✅ You selected PIZZA\nReply ORDER PIZZA")

    elif text.startswith("ORDER"):
        send_text(phone, "🎉 Order confirmed!\nThanks for ordering 🍕")

    else:
        send_text(phone, "Reply:\nHI\nMENU\nITEM PIZZA\nORDER PIZZA")

    return {"status": "ok"}

# ===============================
# SEND TEXT
# ===============================
def send_text(to, body):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }
    r = requests.post(url, headers=headers, json=payload)
    print("SEND:", r.text)
