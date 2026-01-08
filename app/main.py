from fastapi import FastAPI, Request
import requests

app = FastAPI()

# ===============================
# CONFIG (DO NOT CHANGE STRUCTURE)
# ===============================
WHATSAPP_TOKEN = "PASTE_YOUR_ACCESS_TOKEN_HERE"
PHONE_NUMBER_ID = "958320700693461"
VERIFY_TOKEN = "verify_123"

RESTAURANT_NAME = "Jasper's Market"

# ===============================
# HEALTH CHECK
# ===============================
@app.get("/health")
def health():
    return {"status": "ok"}

# ===============================
# WEBHOOK VERIFICATION
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
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
        phone = msg["from"]
        text = msg["text"]["body"].strip().lower()
    except Exception:
        return {"status": "ignored"}

    # ---------------- DEMO LOGIC ----------------
    if text in ["hi", "hello"]:
        send_text(
            phone,
            f"👋 Welcome to {RESTAURANT_NAME}!\n\nReply:\nMENU – see menu\nORDER PIZZA – order item"
        )

    elif text == "menu":
        send_text(
            phone,
            "🍕 MENU\n\n1. Pizza\n2. Burger\n3. Sandwich\n\nReply:\nORDER PIZZA"
        )

    elif text.startswith("order"):
        item = text.replace("order", "").strip().title()
        send_text(
            phone,
            f"✅ Your order for {item} is confirmed!\nThank you for choosing {RESTAURANT_NAME} 🙌"
        )

    else:
        send_text(
            phone,
            "❓ I didn’t understand.\nReply:\nHI\nMENU\nORDER PIZZA"
        )

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
