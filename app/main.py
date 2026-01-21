from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Incoming(BaseModel):
    from_number: str
    text: str

@app.get("/")
def root():
    return {"status": "fastapi running"}

@app.post("/message")
def handle_message(data: Incoming):
    msg = data.text.lower().strip()

    if msg in ["hi", "hello", "hey"]:
        return {
            "reply": (
                "👋 Welcome to *Spice Villa Restaurant* 🍽️\n\n"
                "Reply with:\n"
                "1️⃣ Menu\n"
                "2️⃣ Order\n"
                "3️⃣ Location"
            )
        }

    if msg == "1":
        return {"reply": "📋 Today’s Menu:\n• Paneer\n• Biryani\n• Noodles"}

    if msg == "2":
        return {"reply": "🛒 Please send item name to order"}

    if msg == "3":
        return {"reply": "📍 We are at MG Road, Bangalore"}

    return {"reply": "❓ Sorry, please reply 1, 2 or 3"}
