from fastapi import FastAPI, Request
import requests
import os

# =================================================
# CONFIG (SET THESE)
# =================================================
VERIFY_TOKEN = "verify_123"   # MUST match Meta dashboard
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")  # set in EC2 env
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")  # set in EC2 env

app = FastAPI(title="Multitenant WhatsApp Chatbot")

# =================================================
# HEALTH CHECK
# =================================================
@app.get("/health")
def health():
    return {"status": "ok"}

# =================================================
# META WEBHOOK VERIFICATION
# =================================================
@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = None,
    hub_challenge: str = None,
    hub_verify_token: str = None
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        print("✅ Webhook verified")
        return int(hub_challenge)

    return {"error": "Verification failed"}

# =================================================
# RECEIVE WHATSAPP MESSAGES
# =================================================
@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    print("🔥 INCOMING WEBHOOK:", data)

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        phone = message["from"]
        text = message["text"]["body"]
    except Exception as e:
        print("❌ Ignored payload:", e)
        return {"status": "ignored"}

    reply_text = f"You said: {text}"

    send_whatsapp_message(phone, reply_text)
    return {"status": "sent"}

# =================================================
# SEND MESSAGE TO WHATSAPP
# =================================================
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

    response = requests.post(url, headers=headers, json=payload)
    print("📤 WhatsApp API response:", response.text)
