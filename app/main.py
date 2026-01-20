import os
import json
import uuid
import logging
import requests
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse

# ======================================================
# LOGGING CONFIG
# ======================================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("whatsapp-bot")

# ======================================================
# APP INIT
# ======================================================
app = FastAPI()

VERIFY_TOKEN = "verify_123"
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

GRAPH_URL = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

logger.info("🚀 APP STARTED")
logger.info("WHATSAPP_TOKEN SET: %s", bool(WHATSAPP_TOKEN))
logger.info("PHONE_NUMBER_ID: %s", PHONE_NUMBER_ID)

# ======================================================
# MIDDLEWARE – REQUEST LOGGING
# ======================================================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start_time = datetime.utcnow()

    logger.info(
        "[%s] ➡️ %s %s",
        request_id,
        request.method,
        request.url.path,
    )

    try:
        response = await call_next(request)
    except Exception as exc:
        logger.exception("[%s] ❌ UNHANDLED ERROR", request_id)
        return JSONResponse(status_code=500, content={"error": "internal error"})

    duration = (datetime.utcnow() - start_time).total_seconds()
    logger.info(
        "[%s] ⬅️ %s (%0.3fs)",
        request_id,
        response.status_code,
        duration,
    )
    return response

# ======================================================
# HEALTH
# ======================================================
@app.get("/")
def root():
    return {"status": "running"}

@app.get("/health")
def health():
    return {"status": "ok"}

# ======================================================
# WEBHOOK VERIFY (GET)
# ======================================================
@app.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(request: Request):
    params = request.query_params
    logger.info("🔍 WEBHOOK VERIFY REQUEST: %s", dict(params))

    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == VERIFY_TOKEN
    ):
        logger.info("✅ WEBHOOK VERIFIED SUCCESSFULLY")
        return params.get("hub.challenge")

    logger.warning("❌ WEBHOOK VERIFICATION FAILED")
    return PlainTextResponse("Verification failed", status_code=403)

# ======================================================
# WEBHOOK RECEIVE (POST)
# ======================================================
@app.post("/webhook")
async def receive_webhook(request: Request):
    logger.info("🔥 WEBHOOK POST RECEIVED")

    try:
        payload = await request.json()
        logger.debug("📩 RAW PAYLOAD:\n%s", json.dumps(payload, indent=2))
    except Exception:
        logger.warning("⚠️ INVALID JSON RECEIVED")
        return {"status": "invalid json"}

    try:
        entry = payload["entry"][0]
        change = entry["changes"][0]
        value = change["value"]

        # Ignore non-message updates
        if "messages" not in value:
            logger.info("ℹ️ EVENT IGNORED (no messages key)")
            return {"status": "ignored"}

        message = value["messages"][0]
        from_number = message["from"]
        msg_type = message.get("type")

        logger.info("📨 MESSAGE FROM %s | TYPE=%s", from_number, msg_type)

        if msg_type == "text":
            user_text = message["text"]["body"].strip().lower()
            logger.info("👤 USER SAID: %s", user_text)

            if user_text in ["hi", "hello", "hey"]:
                reply = (
                    "👋 Welcome to *Spice Villa Restaurant* 🍽️\n\n"
                    "Reply with:\n"
                    "1️⃣ Menu\n"
                    "2️⃣ Order\n"
                    "3️⃣ Location"
                )
                send_text(from_number, reply)

    except KeyError as e:
        logger.error("❌ PAYLOAD FORMAT ERROR: missing %s", e)
    except Exception:
        logger.exception("❌ UNEXPECTED PROCESSING ERROR")

    return {"status": "ok"}

# ======================================================
# SEND MESSAGE TO WHATSAPP
# ======================================================
def send_text(to: str, text: str):
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        logger.error("❌ CANNOT SEND MESSAGE – ENV VARS MISSING")
        return

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(GRAPH_URL, json=payload, headers=headers, timeout=10)
        logger.info("📤 SEND STATUS: %s", response.status_code)
        logger.debug("📤 SEND RESPONSE: %s", response.text)
    except Exception:
        logger.exception("❌ FAILED TO CALL WHATSAPP API")
