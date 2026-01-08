from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

# =========================
# CONFIG (CHANGE ONLY THESE)
# =========================
VERIFY_TOKEN = "verify_123"

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN") or "PASTE_TEMP_TOKEN_HERE"
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID") or "958320700693461"

# =========================
# HEALTH CHECK
# =========================
@app.get("/health")
def health():
    return {"status": "ok"}

# =========================
# WEBHOOK VERIFICATION
# =========================
@app.get("/webhook")
def verify_webhook(
    hub_mode: str = None,
    hub_challenge: str = None,
    hub_verify_token: str = None,
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        print("✅ Webhook verified")
        return int(hub_challenge)

    return {"error": "Verification failed"}

# =========================
# RECEIVE WHATSAPP MESSAGE
# =========================
@app.post("/webhook")
async def receive_message(request: Request):
    payload = await request.json()
    print("📩 Incoming payload:", payload)

    try:
        message = payload["entry"][0]["changes"][0]["value"]["messages"][0]
        from_number = message["from"]
        text = message["text"]["body"]
    except Exception as e:
        print("⚠️ Ignored payload:", e)
        return {"status": "ignored"}

    reply_text = f"You said: {text}"

    send_whatsapp_message(from_number, reply_text)
    return {"status": "sent"}

# =========================
# SEND MESSAGE TO WHATSAPP
# =========================
def send_whatsapp_message(to: str, text: str):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

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

    response = requests.post(url, headers=headers, json=payload)
    print("📤 Send response:", response.status_code, response.text)
