from fastapi import FastAPI, Request, Query
import os
import requests

VERIFY_TOKEN = "verify_123"

# -------------------------------------------------
# WhatsApp Webhook Verification (FIXED)
# -------------------------------------------------
@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    print("VERIFY HIT:", hub_mode, hub_verify_token, hub_challenge)

    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)

    return {"error": "Verification failed"}

# -------------------------------------------------
# WhatsApp Incoming Messages
# -------------------------------------------------
@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    payload = await request.json()
    print("INCOMING PAYLOAD:", payload)

    try:
        value = payload["entry"][0]["changes"][0]["value"]
        message = value["messages"][0]
        phone = message["from"]
        text = message["text"]["body"]
    except Exception as e:
        print("IGNORED:", e)
        return {"status": "ignored"}

    reply = f"👋 Hello! You said: {text}"

    send_whatsapp_message(phone, reply)
    return {"status": "sent"}

# -------------------------------------------------
# Send WhatsApp message
# -------------------------------------------------
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

def send_whatsapp_message(to: str, text: str):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }

    res = requests.post(url, headers=headers, json=data)
    print("SEND STATUS:", res.status_code, res.text)
