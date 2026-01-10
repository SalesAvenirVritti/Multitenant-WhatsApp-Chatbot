from fastapi import FastAPI, Request
import requests
import os

app = FastAPI()

WHATSAPP_TOKEN = os.getenv("EAAcZAUrL1kAUBQWMOwhrzgDTgAPgtIqQGXyKWpmq0pGks0cgekZBthZAE3ZA8pZBaPRhN4u1BrLjR2JGCs904trjX4YwhbLXvFXpdLN3DU6WHr5DM778LRe6uiMpQZCPvMNFkvDFgZA5xWI34DyrC68mDi6a5rc1qSdhA3isVvhEKhzLvINREZC78ZCFbA4QHe4FhGlLYLFGgFhJaFOeXv5orKYpCrSZBILp28MHDoYEXyQYEuSuP1IUnn22jNOmZCS30LWZCycq1BZBussZB4sPepZBddyRIOekAZDZD")
PHONE_NUMBER_ID = os.getenv("P58320700693461")
VERIFY_TOKEN = "verify_123"

# --------------------
# HEALTH CHECK
# --------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# --------------------
# WEBHOOK VERIFY
# --------------------
@app.get("/webhook")
def verify_webhook(
    hub_mode: str = None,
    hub_challenge: str = None,
    hub_verify_token: str = None,
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    return "Verification failed"

# --------------------
# WEBHOOK RECEIVE
# --------------------
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
        return "ignored"

    # --------------------
    # SIMPLE DEMO LOGIC
    # --------------------
    if text == "hi":
        send_text(phone, "👋 Welcome to Jasper’s Market!\nReply MENU to see items")

    elif text == "menu":
        send_text(phone, "🛒 Items:\n1️⃣ Apple\n2️⃣ Bread\nReply: ORDER Apple")

    elif text.startswith("order"):
        item = text.replace("order", "").strip()
        send_text(phone, f"✅ Order confirmed for {item}\nThank you!")

    else:
        send_text(phone, "Reply HI or MENU")

    return "ok"

# --------------------
# SEND TEXT
# --------------------
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

    res = requests.post(url, headers=headers, json=payload)
    print("SEND RESULT:", res.text)
