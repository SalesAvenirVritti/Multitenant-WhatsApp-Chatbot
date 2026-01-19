from fastapi import FastAPI, Request, Query
import requests
import os

app = FastAPI()

# =====================
# CONFIG
# =====================
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = "verify_123"

# =====================
# HEALTH
# =====================
@app.get("/health")
def health():
    return {"status": "ok"}

# =====================
# WEBHOOK VERIFY (FIXED)
# =====================
@app.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: int = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return hub_challenge
    return "Verification failed", 403

# =====================
# WEBHOOK RECEIVE
# =====================
@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    print("INCOMING:", data)

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        phone = message["from"]
        text = message["text"]["body"]
    except Exception as e:
        print("IGNORE:", e)
        return {"status": "ignored"}

    reply_text = f"✅ BOT WORKING!\nYou said: {text}"

    send_text(phone, reply_text)
    return {"status": "ok"}

# =====================
# SEND TEXT MESSAGE
# =====================
def send_text(to, text):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

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

    res = requests.post(url, headers=headers, json=payload)
    print("SEND STATUS:", res.text)
