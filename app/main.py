from fastapi import FastAPI, Request, Query
import requests
import os

app = FastAPI()

# ===============================
# CONFIG
# ===============================
WHATSAPP_TOKEN = "PASTE_YOUR_ACCESS_TOKEN_HERE"
PHONE_NUMBER_ID = "958320700693461"   # your phone number ID
VERIFY_TOKEN = "verify_123"

# ===============================
# HEALTH CHECK
# ===============================
@app.get("/health")
def health():
    return {"status": "ok"}

# ===============================
# WEBHOOK VERIFICATION (GET)
# ===============================
@app.get("/webhook")
def verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    return "Verification failed", 403

# ===============================
# WEBHOOK RECEIVER (POST)
# ===============================
@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    print("INCOMING MESSAGE:", data)

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        phone = message["from"]
        text = message["text"]["body"]
    except Exception as e:
        print("NO MESSAGE FOUND:", e)
        return {"status": "ignored"}

    # 🔥 GUARANTEED REPLY
    send_text(phone, "✅ Bot is LIVE! You said: " + text)

    return {"status": "ok"}

# ===============================
# SEND TEXT MESSAGE
# ===============================
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

    r = requests.post(url, headers=headers, json=payload)
    print("SEND RESPONSE:", r.text)
