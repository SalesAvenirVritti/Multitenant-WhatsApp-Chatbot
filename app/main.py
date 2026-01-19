from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

# ===============================
# CONFIG
# ===============================
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = "verify_123"

RESTAURANT_NAME = "Jasper's Market"

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
    return {"error": "Verification failed"}

# ===============================
# WEBHOOK RECEIVER
# ===============================
@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    print("INCOMING:", data)

    try:
        value = data["entry"][0]["changes"][0]["value"]

        # Ignore delivery/status events
        if "messages" not in value:
            return {"status": "ignored"}

        message = value["messages"][0]
        phone = message["from"]
        text = message.get("text", {}).get("body", "").strip().lower()

    except Exception as e:
        print("ERROR:", e)
        return {"status": "error"}

    # ===============================
    # BOT LOGIC
    # ===============================
    if text in ["hi", "hello", "hey"]:
        send_text(phone, f"👋 Welcome to {RESTAURANT_NAME}!\nReply MENU to see items.")

    elif text == "menu":
        send_text(
            phone,
            "🛒 Available items:\n1️⃣ Apples\n2️⃣ Milk\n\nReply ITEM Apples"
        )

    elif text.startswith("item"):
        item = text.replace("item", "").strip()
        send_text(phone, f"✅ You selected {item}\nReply ORDER {item}")

    elif text.startswith("order"):
        item = text.replace("order", "").strip()
        send_text(phone, f"🎉 Order confirmed for {item}!\nThank you 😊")

    else:
        send_text(phone, "Please reply:\nHI\nMENU\nITEM Apples")

    return {"status": "ok"}

# ===============================
# SEND TEXT MESSAGE
# ===============================
def send_text(to: str, text: str):
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

    response = requests.post(url, headers=headers, json=payload)
    print("SEND:", response.status_code, response.text)
