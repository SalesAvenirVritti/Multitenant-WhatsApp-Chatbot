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
    print("🔥 WEBHOOK HIT 🔥")
    data = await request.json()
    print("INCOMING MESSAGE:", json.dumps(data, indent=2))

async def receive_message(request: Request):
    data = await request.json()
    print("INCOMING MESSAGE:", json.dumps(data, indent=2))

    try:
        value = data["entry"][0]["changes"][0]["value"]

        # Ignore status updates
        if "messages" not in value:
            return {"status": "ignored"}

        message = value["messages"][0]
        from_number = message["from"]

        # ===============================
        # TEXT MESSAGE
        # ===============================
        if message["type"] == "text":
            user_text = message["text"]["body"].lower().strip()

            # 🔴 IMPORTANT: reply ONLY on HI (template-first rule)
            if user_text in ["hi", "hello", "hey"]:
                send_restaurant_template(from_number)
            else:
                print("Ignored text (template not triggered yet)")

        # ===============================
        # BUTTON CLICK (TEMPLATE RESPONSE)
        # ===============================
        elif message["type"] == "interactive":
            button_id = message["interactive"]["button_reply"]["id"]
            handle_button_click(from_number, button_id)

    except Exception as e:
        print("ERROR:", e)

    return {"status": "ok"}

# ===============================
# SEND TEXT
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
# SEND RESTAURANT TEMPLATE (LIKE HDFC)
# ===============================
def send_restaurant_template(to):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": (
                    "👋 *Welcome to Spice Villa Restaurant!*\n\n"
                    "Simply select from the options below or type your query to get started 🍽️"
                )
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "MENU",
                            "title": "📖 View Menu"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "ORDER",
                            "title": "🛒 Place Order"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "CONTACT",
                            "title": "📞 Contact Us"
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
# HANDLE TEMPLATE BUTTONS
# ===============================
def handle_button_click(to, button_id):
    if button_id == "MENU":
        send_text(
            to,
            "🍽️ *Today’s Menu*\n\n• Paneer Butter Masala\n• Chicken Biryani\n• Veg Pizza"
        )

    elif button_id == "ORDER":
        send_text(
            to,
            "🛒 Please reply with the item name you want to order.\nExample: *Veg Pizza*"
        )

    elif button_id == "CONTACT":
        send_text(
            to,
            "📞 *Spice Villa Restaurant*\nCall: +91 9XXXXXXXXX\n⏰ 10 AM – 11 PM"
        )
