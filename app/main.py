from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

# ===============================
# CONFIG (REPLACE THESE)
# ===============================
WHATSAPP_TOKEN = "PASTE_YOUR_ACCESS_TOKEN_HERE"
PHONE_NUMBER_ID = "PASTE_PHONE_NUMBER_ID_HERE"
VERIFY_TOKEN = "verify_123"

RESTAURANT_NAME = "Food Plaza"

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

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        phone = message["from"]
        text = message["text"]["body"].strip().upper()
    except Exception:
        return {"status": "ignored"}

    # ===============================
    # BOT LOGIC (DEMO)
    # ===============================
    if text == "HI":
        send_template(
            phone,
            "restaurant_welcome",
            [RESTAURANT_NAME]
        )

    elif text == "MENU":
        send_template(
            phone,
            "restaurant_menu",
            ["Pizza"]
        )

    elif text.startswith("ITEM"):
        item = text.replace("ITEM", "").strip()
        send_template(
            phone,
            "restaurant_order_confirm",
            [item]
        )

    elif text.startswith("ORDER"):
        item = text.replace("ORDER", "").strip()
        send_text(
            phone,
            f"✅ Your order for {item} is confirmed!\nThank you for ordering with {RESTAURANT_NAME} 🍕"
        )

    else:
        send_text(
            phone,
            "Please reply:\nHI\nMENU\nITEM Pizza\nORDER Pizza"
        )

    return {"status": "ok"}

# ===============================
# SEND TEMPLATE MESSAGE
# ===============================
def send_template(to, template_name, variables):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "en"},
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

# ===============================
# SEND NORMAL TEXT MESSAGE
# ===============================
def send_text(to, text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

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

    requests.post(url, headers=headers, json=payload)
from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

# ===============================
# CONFIG (REPLACE THESE)
# ===============================
WHATSAPP_TOKEN = "PASTE_YOUR_ACCESS_TOKEN_HERE"
PHONE_NUMBER_ID = "PASTE_PHONE_NUMBER_ID_HERE"
VERIFY_TOKEN = "verify_123"

RESTAURANT_NAME = "Food Plaza"

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
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        phone = message["from"]
        text = message["text"]["body"]
    except Exception as e:
        print("ERROR:", e)
        return {"status": "ignored"}

    # SIMPLE TEXT REPLY (NO TEMPLATE)
    send_text(phone, "👋 Hi! Grocery bot is working.")

    return {"status": "ok"}

    # ===============================
    # BOT LOGIC (DEMO)
    # ===============================
    if text == "HI":
        send_template(
            phone,
            "restaurant_welcome",
            [RESTAURANT_NAME]
        )

    elif text == "MENU":
        send_template(
            phone,
            "restaurant_menu",
            ["Pizza"]
        )

    elif text.startswith("ITEM"):
        item = text.replace("ITEM", "").strip()
        send_template(
            phone,
            "restaurant_order_confirm",
            [item]
        )

    elif text.startswith("ORDER"):
        item = text.replace("ORDER", "").strip()
        send_text(
            phone,
            f"✅ Your order for {item} is confirmed!\nThank you for ordering with {RESTAURANT_NAME} 🍕"
        )

    else:
        send_text(
            phone,
            "Please reply:\nHI\nMENU\nITEM Pizza\nORDER Pizza"
        )

    return {"status": "ok"}

# ===============================
# SEND TEMPLATE MESSAGE
# ===============================
def send_template(to, template_name, variables):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "en"},
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

# ===============================
# SEND NORMAL TEXT MESSAGE
# ===============================
def send_text(to, text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

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

    requests.post(url, headers=headers, json=payload)
