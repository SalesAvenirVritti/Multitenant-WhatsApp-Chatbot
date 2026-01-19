from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

# ===============================
# CONFIG (ENV FROM systemd)
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
# WEBHOOK VERIFICATION (META)
# ===============================
@app.get("/webhook")
def verify_webhook(
    hub_mode: str = None,
    hub_challenge: str = None,
    hub_verify_token: str = None
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    return ("Verification failed", 403)

# ===============================
# WEBHOOK RECEIVER
# ===============================
@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    print("INCOMING:", data)

    try:
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
        phone = msg["from"]
        text = msg["text"]["body"].strip().lower()
    except Exception as e:
        print("IGNORED:", e)
        return {"status": "ignored"}

    # 🔥 ALWAYS USE TEMPLATE (DEMO SAFE)
    if text == "hi":
        send_template(
            phone,
            "restaurant_welcome",   # EXACT TEMPLATE NAME
            ["Jasper's Market"]
        )

    return {"status": "ok"}

# ===============================
# SEND TEMPLATE MESSAGE
# ===============================
def send_template(to, template_name, variables):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "en_US"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": v} for v in variables
                    ]
                }
            ]
        }
    }

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    r = requests.post(url, headers=headers, json=payload)
    print("META RESPONSE:", r.text)
