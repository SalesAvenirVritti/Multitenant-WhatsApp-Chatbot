from fastapi import FastAPI, Request
import requests

app = FastAPI(title="Restaurant WhatsApp Bot")

# =====================================================
# CONFIG – REPLACE THESE WITH REAL VALUES
# =====================================================
WHATSAPP_TOKEN = "PASTE_YOUR_ACCESS_TOKEN_HERE"
PHONE_NUMBER_ID = "PASTE_PHONE_NUMBER_ID_HERE"
VERIFY_TOKEN = "verify_123"

RESTAURANT_NAME = "Food Plaza"

# =====================================================
# HEALTH CHECK
# =====================================================
@app.get("/health")
def health():
    return {"status": "ok"}

# =====================================================
# WEBHOOK VERIFICATION (META)
# =====================================================
@app.get("/webhook")
def verify_webhook(
    hub_mode: str = None,
    hub_challenge: str = None,
    hub_verify_token: str = None
):
    print("✅ VERIFY HIT")

    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)

    return {"error": "Verification failed"}

# =====================================================
# WEBHOOK RECEIVER (INCOMING MESSAGES)
# =====================================================
@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    print("🔥 INCOMING PAYLOAD:", data)

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        phone = message["from"]
        text = message["text"]["body"].strip().upper()
    except Exception as e:
        print("❌ IGNORE:", e)
        return {"status": "ignored"}

    # =================================================
    # DEMO RESTAURANT LOGIC
    # =================================================
    if text == "HI":
        send_text(
            phone,
            f"👋 Welcome to {RESTAURANT_NAME}!\n\nReply:\nMENU"
        )

    elif text == "MENU":
        send_text(
            phone,
            "🍽 MENU\n1️⃣ Pizza\n2️⃣ Burger\n\nReply:\nITEM Pizza"
        )

    elif text.startswith("ITEM"):
        item = text.replace("ITEM", "").strip()
        send_text(
            phone,
            f"👍 You selected *{item}*\n\nReply:\nORDER {item}"
        )

    elif text.startswith("ORDER"):
        item = text.replace("ORDER", "").strip()
        send_text(
            phone,
            f"✅ Order Confirmed!\n\n🍴 Item: {item}\n🏪 {RESTAURANT_NAME}\n\nThank you!"
        )

    else:
        send_text(
            phone,
            "❓ Invalid input\n\nReply:\nHI\nMENU\nITEM Pizza\nORDER Pizza"
        )

    return {"status": "ok"}

# =====================================================
# SEND TEXT MESSAGE (SAFE FOR DEMO)
# =====================================================
def send_text(to: str, text: str):
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
    print("📤 SENT:", r.text)

# =====================================================
# OPTIONAL: TEMPLATE SENDER (USE LATER)
# =====================================================
"""
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

    requests.post(url, headers=headers, json=payload)
"""
