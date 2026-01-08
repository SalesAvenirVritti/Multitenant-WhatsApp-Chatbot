from fastapi import FastAPI, Request
import requests
import os

VERIFY_TOKEN = "verify_123"
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    if (
        params.get("hub.mode") == "subscribe"
        and params.get("hub.verify_token") == VERIFY_TOKEN
    ):
        return int(params.get("hub.challenge"))
    return {"error": "Verification failed"}

@app.post("/webhook")
async def receive_whatsapp_message(request: Request):
    data = await request.json()
    print("INCOMING PAYLOAD:", data)

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        phone = message["from"]
        text = message["text"]["body"]

        reply = f"👋 You said: {text}"

        url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"body": reply}
        }

        r = requests.post(url, headers=headers, json=payload)
        print("SEND STATUS:", r.status_code, r.text)

    except Exception as e:
        print("ERROR:", e)

    return {"status": "ok"}
