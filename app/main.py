from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import requests
import json
import os

app = FastAPI()

# ===============================
# CONFIG
# ===============================
VERIFY_TOKEN = "verify_123"

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

GRAPH_URL = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

# ===============================
# HEALTH
# ===============================
@app.get("/health")
def health():
    return {"status": "ok"}

# ===============================
# WEBHOOK VERIFY (GET)
# ===============================
@app.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(request: Request):
    params = request.query_params

    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == VERIFY_TOKEN
    ):
        return params.get("hub.challenge")

    return PlainTextResponse("Verification failed", status_code=403)

# ===============================
# WEBHOOK RECEIVE (POST)
# ===============================
@app.post("/webhook")
async def receive_webhook(request: Request):
    print("🔥 META WEBHOOK HIT 🔥")

    data = await request.json()
    print(json.dumps(data, indent=2))

    try:
        value = data["entry"][0]["changes"][0]["value"]

        if "messages" not in value:
            return {"status": "ignored"}

        message = value["messages"][0]
        from_number = message["from"]

        if message["type"] == "text":
            user_text = message["text"]["body"].lower().strip()

            if user_text in ["hi", "hello", "hey"]:
                send_text(
                    from_number,
                    "👋 Welcome to *Spice Villa Restaurant* 🍽️\n\n"
                    "Reply with:\n"
                    "1️⃣ Menu\n"
                    "2️⃣ Order\n"
                    "3️⃣ Location"
                )

    except Exception as e:
        print("❌ ERROR:", e)

    return {"status": "ok"}

# ===============================
# SEND MESSAGE
# ===============================
def send_text(to, text):
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

    r = requests.post(GRAPH_URL, json=payload, headers=headers)
    print("📤 SEND STATUS:", r.status_code)
    print("📤 SEND RESPONSE:", r.text)
