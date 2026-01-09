from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

# ===============================
# CONFIG
# ===============================
WHATSAPP_TOKEN = "EAAcZAUrL1kAUBQWMOwhrzgDTgAPgtIqQGXyKWpmq0pGks0cgekZBthZAE3ZA8pZBaPRhN4u1BrLjR2JGCs904trjX4YwhbLXvFXpdLN3DU6WHr5DM778LRe6uiMpQZCPvMNFkvDFgZA5xWI34DyrC68mDi6a5rc1qSdhA3isVvhEKhzLvINREZC78ZCFbA4QHe4FhGlLYLFGgFhJaFOeXv5orKYpCrSZBILp28MHDoYEXyQYEuSuP1IUnn22jNOmZCS30LWZCycq1BZBussZB4sPepZBddyRIOekAZDZD"
PHONE_NUMBER_ID = "958320700693461"
VERIFY_TOKEN = "verify_123"

BUSINESS_NAME = "Jasper's Market"

GRAPH_URL = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

HEADERS = {
    "Authorization": f"Bearer {WHATSAPP_TOKEN}",
    "Content-Type": "application/json"
}

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
def verify_webhook(request: Request):
    params = request.query_params
    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == VERIFY_TOKEN
    ):
        return int(params.get("hub.challenge"))
    return "Verification failed", 403

# ===============================
# WEBHOOK RECEIVER
# ===============================
@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    print("📩 INCOMING:", data)

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        phone = message["from"]
        text = message["text"]["body"].strip().upper()
    except Exception as e:
        print("⚠️ Ignored:", e)
        return {"status": "ignored"}

    # ===============================
    # DEMO BOT LOGIC (SAFE)
    # ===============================

    if text == "HI":
        # FIRST MESSAGE → TEMPLATE (24h safe)
        send_template(
            phone,
            "restaurant_welcome",
            [BUSINESS_NAME]
        )

    elif text == "MENU":
        send_template(
            phone,
            "restaurant_menu",
            ["Pizza, Burger, Sandwich"]
        )

    elif text.startswith("ITEM"):
        item = text.replace("ITEM", "").strip()
        send_template(
            phone,
            "restaurant_item_selected",
            [item]
        )

    elif text.startswith("ORDER"):
        item = text.replace("ORDER", "").strip()
        send_text(
            phone,
            f"✅ Order confirmed!\n\nItem: {item}\nThank you for shopping with {BUSINESS_NAME} 🛒"
        )

    else:
        send_text(
            phone,
            "Reply with:\nHI\nMENU\nITEM Pizza\nORDER Pizza"
        )

    return {"status": "ok"}

# ===============================
# SEND TEMPLATE MESSAGE
# ===============================
def send_template(to, template_name, variables):
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

    r = requests.post(GRAPH_URL, headers=HEADERS, json=payload)
    print("📤 TEMPLATE:", r.text)

# ===============================
# SEND NORMAL TEXT MESSAGE
# ===============================
def send_text(to, text):
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }

    r = requests.post(GRAPH_URL, headers=HEADERS, json=payload)
    print("📤 TEXT:", r.text)
