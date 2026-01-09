from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

# ================= CONFIG =================
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN") or "PASTE_ACCESS_TOKEN"
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID") or "958320700693461"
VERIFY_TOKEN = "verify_123"

BUSINESS_NAME = "Jasper's Market"

# ================= HEALTH =================
@app.get("/health")
def health():
    return {"status": "ok"}

# ================= WEBHOOK VERIFY =================
@app.get("/webhook")
def verify_webhook(request: Request):
    params = request.query_params
    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == VERIFY_TOKEN
    ):
        return int(params.get("hub.challenge"))
    return "Verification failed", 403

# ================= WEBHOOK RECEIVE =================
@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    print("📩 INCOMING:", data)

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        from_number = message["from"]
        text = message["text"]["body"].strip().lower()
    except Exception:
        return {"status": "ignored"}

    # ===== BOT LOGIC =====
    if text == "hi":
        send_text(
            from_number,
            f"👋 Hi! Welcome to {BUSINESS_NAME}\nReply MENU to see items"
        )

    elif text == "menu":
        send_text(
            from_number,
            "🛒 Available items:\n1️⃣ Fruits\n2️⃣ Vegetables\nReply ITEM <name>"
        )

    elif text.startswith("item"):
        item = text.replace("item", "").strip()
        send_text(
            from_number,
            f"👍 You selected {item}\nReply ORDER {item} to confirm"
        )

    elif text.startswith("order"):
        item = text.replace("order", "").strip()
        send_text(
            from_number,
            f"✅ Order confirmed for {item}\nThank you!"
        )

    else:
        send_text(
            from_number,
            "❓ I didn’t understand.\nTry: HI, MENU, ITEM Apple"
        )

    return {"status": "ok"}

# ================= SEND TEXT =================
def send_text(to, body):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }

    r = requests.post(url, headers=headers, json=payload)
    print("📤 SENT:", r.text)
