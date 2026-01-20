import os
import json
import requests
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

# ===============================
# DEBUG: APP STARTUP
# ===============================
print("🚀 APP STARTED")
print("WHATSAPP_TOKEN SET:", bool(os.getenv("WHATSAPP_TOKEN")))
print("PHONE_NUMBER_ID:", os.getenv("PHONE_NUMBER_ID"))

app = FastAPI()

# ===============================
# CONFIG
# ===============================
VERIFY_TOKEN = "verify_123"

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
    print("❌ ENV VARS MISSING — BOT CANNOT SEND MESSAGES")

GRAPH_URL = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

# ===============================
# HEALTH CHECK
# ===============================
@app.get("/health")
def health():
    return {"status": "ok"}

# ===============================
# META WEBHOOK VERIFICATION (GET)
# ===============================
@app.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(request: Request):
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    print("🔍 VERIFY REQUEST:", params)

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ WEBHOOK VERIFIED")
        return challenge

    return PlainTextResponse("Verification failed", status_code=403)

# ========
