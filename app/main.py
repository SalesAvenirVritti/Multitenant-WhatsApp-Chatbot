from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import requests
import os
import json

app = FastAPI()

# ===============================
# CONFIG
# ===============================
VERIFY_TOKEN = "verify_123"
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
GRAPH_URL = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

# ===============================
# HEALTH CHECK
# ===============================
@app.get("/health")
def health():
    return {"status": "ok"}

# ===============================
# META WEBHOOK VERIFICATION
# ===============================
@app.get("/webhook", response_class=PlainTextResponse)
def verify_webhook(request: Request):
    params = request.query_params

    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == VERIFY_TOKEN
    ):
        return params.get("hub.challenge")

    return PlainTextResponse("Verification failed", status_code=403)

# ===============================
# WHATSAPP MESSAGE RECEIVER
# ===============================
@app.post("/webhook")
async def receive_message(request: Request):
    data = await request.json()
    print("INCOMING:", json.dumps(data, indent=2))

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        from_number = message["from"]

        # TEXT MESSAGE
        if message["type"] == "text":
            user_text = message["text"]["body"].lower().strip()

            if user_text in ["hi", "hello", "hey"]:
                send_restaurant_menu(from_number)
            else:
                send_text(from_number, "Please type *Hi* to see menu 🍽️")

        # BUTTON REPLY
        elif message["type"] == "interactive":
            button_id = message["interactive"]["button_reply"]["id"]
            handle_button_reply(from_number, button_id)

    except Exception as e:
        print("ERROR:", e)

    return {"status": "ok"}

# ===============================
# SEND TEXT MESSAGE
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

    requests.post(GRAPH_URL, headers=headers, json=payload)

# ===============================
# SEND RESTAURANT WELCOME MENU
# ===============================
def send_restaurant_menu(to):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": (
                    "👋 *Welcome to Foodie Hub!*\n\n"
                    "Simply select from the options below or type your query to get started 🍕"
                )
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "VIEW_MENU",
                            "title": "📖 View Menu"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "PLACE_ORDER",
                            "title": "🛒 Place Order"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "LOCATION",
                            "title": "📍 Location"
                        }
                    }
                ]
            }
        }
    }

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    requests.post(GRAPH_URL, headers=headers, json=payload)

# ===============================
# HANDLE BUTTON CLICKS
# ===============================
def handle_button_reply(to, button_id):
    if button_id == "VIEW_MENU":
        send_text(
            to,
            "🍽️ *Our Menu*\n\n1️⃣ Pizza\n2️⃣ Burger\n3️⃣ Pasta\n\nReply with item name to order."
        )

    elif button_id == "PLACE_ORDER":
        send_text(
            to,
            "🛒 Please type the item name you want to order.\nExample: *Pizza*"
        )

    elif button_id == "LOCATION":
        send_text(
            to,
            "📍 *Foodie Hub*\nMG Road, Pune\n⏰ 10 AM – 11 PM"
        )
