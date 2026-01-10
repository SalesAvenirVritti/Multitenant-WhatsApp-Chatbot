from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

# ===============================
# CONFIG (READ FROM ENV)
# ===============================
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = "verify_123"

# ===============================
# HEALTH CHECK
# ===============================
@app.get("/health")
def health():
    return {"status": "ok"}

# ===============================
# META WEBHOOK VERIFICATION
# ===============================
@app.get("/webhook")
def verify_webhook(
    hub_mode: str = None,
    hub_challenge: str = None,
    hub_verify_token: str = None
):
    print("VERIFY TOKEN RECEIVED:", hub_verify_token)

    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)

    return "Verification failed", 403

# ===============================
# WEBHOOK RECEIVER (WHATSAPP MSG)
# ===============================
@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    print("INCOMING MESSAGE:", data)

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        phone = message["from"]
        text = message["text"]["body"].strip().lower()
    except Exception as e:
        print("IGNORE:", e)
        return {"status": "ignored"}

    # ✅ SIMPLE DEMO REPLY (GUARANTEED)
    send_text(phone, "✅ Bot is LIVE! You said: " + text)

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

    response = requests.post(url, headers=headers, json=payload)
    print("SEND RESPONSE:", response.text)
