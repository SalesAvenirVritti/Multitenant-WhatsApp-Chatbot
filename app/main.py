from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import requests
import os
import json

app = FastAPI()

# ===============================
# CONFIG
# ===============================
VERIFY_TOKEN = "verify_123"
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# ===============================
# HEALTH CHECK
# ===============================
@app.get("/health")
def health():
    return {"status": "ok"}

# ===============================
# META WEBHOOK VERIFICATION
# ===============================
@app.get("/webhook", response_class=PlainTextResponse)
def verify_webhook(request: Request):
    params = request.query_params

    hub_mode = params.get("hub.mode")
    hub_verify_token = params.get("hub.verify_token")
    hub_challenge = params.get("hub.challenge")

    print("VERIFY REQUEST:", params)

    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return hub_challenge  # MUST be plain text

    return PlainTextResponse("Verification failed", status_code=403)

# ===============================
# WHATSAPP MESSAGE RECEIVER
# ===============================
@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    print("INCOMING MESSAGE:", json.dumps(data))

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        from_number = message["from"]
        text = message["text"]["body"]

        send_text(from_number, f"👋 Bot is LIVE! You said: {text}")

    except Exception as e:
        print("ERROR:", e)

    return {"status": "ok"}

# ===============================
# SEND TEXT MESSAGE
# ===============================
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
    print("SEND RESPONSE:", r.text)
