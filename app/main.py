from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import json

app = FastAPI()

VERIFY_TOKEN = "verify_123"

# -------------------------------
# HEALTH CHECK
# -------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# -------------------------------
# META WEBHOOK VERIFICATION (GET)
# -------------------------------
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

# -------------------------------
# META WEBHOOK RECEIVER (POST)
# -------------------------------
@app.post("/webhook")
async def receive_webhook(request: Request):
    print("\n🔥🔥🔥 META WEBHOOK HIT 🔥🔥🔥")

    try:
        body = await request.json()
        print("📩 PAYLOAD:")
        print(json.dumps(body, indent=2))
    except Exception as e:
        print("❌ ERROR PARSING JSON:", e)

    return {"status": "received"}
