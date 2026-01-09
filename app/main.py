from fastapi import FastAPI, Request, Query
import requests
import os

app = FastAPI()

# ===============================
# CONFIG (REPLACE THESE 3 ONLY)
# ===============================
WHATSAPP_TOKEN = "PASTE_YOUR_PERMANENT_TOKEN_HERE"
PHONE_NUMBER_ID = "958320700693461"
VERIFY_TOKEN = "verify_123"

# ===============================
# HEALTH CHECK
# ===============================
@app.get("/health")
def health():
    return {"status": "ok"}

# ===============================
# WEBHOOK VERIFICATION (META)
# ===============================
@app.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    return {"error": "Verification failed"}

# ===============================
# WEBHOOK RECEIVER (MESSAGE IN)
# ===============================
@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    print("INCOMING MESSAGE:", data)

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        phone = message["from"]
        text = message["text"]["body"].strip().upper()
    except Exception as e:
        print("IGNORED:", e)
        return {"status": "ignored"}

    # 🔥 FORCE BASIC REPLY (NO TEMPLATE YET)
    send_text(phone, "👋 Hi! Restaurant bot is LIVE. Reply MENU")

    return {"status": "ok"}

# ===============================
# SEND TEXT MESSAGE
# ===============================
def send_text(to, text):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }

    r = requests.post(url, headers=headers, json=payload)
    print("SEND TEXT:", r.text)
