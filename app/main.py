from fastapi import FastAPI, Request
from sqlalchemy.orm import Session
import requests

from app.db import Base, engine
from app.deps import get_db
from app.models import Tenant, User, Message, ConversationSession

# =================================================
# CONFIG (DEMO MODE)
# =================================================
WHATSAPP_TOKEN = "PASTE_META_ACCESS_TOKEN"
PHONE_NUMBER_ID = "PASTE_PHONE_NUMBER_ID"
VERIFY_TOKEN = "verify_123"

# =================================================
# APP INIT
# =================================================
app = FastAPI(title="Multitenant WhatsApp Chatbot – Grocery Demo")
Base.metadata.create_all(bind=engine)

# =================================================
# HEALTH CHECK
# =================================================
@app.get("/health")
def health():
    return {"status": "ok"}

# =================================================
# GROCERY CHAT LOGIC
# =================================================
def process_grocery_chat(phone: str, text: str, tenant: Tenant, db: Session):

    text = text.lower()

    # User
    user = db.query(User).filter(
        User.phone == phone,
        User.tenant_id == tenant.id
    ).first()

    if not user:
        user = User(
            tenant_id=tenant.id,
            phone=phone,
            name="Guest"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Save incoming message
    db.add(Message(
        tenant_id=tenant.id,
        user_id=user.id,
        direction="in",
        message_text=text
    ))
    db.commit()

    # Session
    session = db.query(ConversationSession).filter(
        ConversationSession.user_id == user.id,
        ConversationSession.tenant_id == tenant.id
    ).first()

    if not session:
        session = ConversationSession(
            tenant_id=tenant.id,
            user_id=user.id,
            state="idle",
            context={}
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    # -------------------------
    # GROCERY FLOW
    # -------------------------
    if "menu" in text:
        reply = (
            "🛒 Grocery Menu:\n"
            "• Rice – ₹50/kg\n"
            "• Sugar – ₹40/kg\n"
            "• Oil – ₹120/litre\n"
            "\nType item name to know price."
        )

    elif "rice" in text:
        reply = "Rice costs ₹50 per kg. Type `order rice` to place order."

    elif "sugar" in text:
        reply = "Sugar costs ₹40 per kg. Type `order sugar` to place order."

    elif "oil" in text:
        reply = "Oil costs ₹120 per litre. Type `order oil` to place order."

    elif "order" in text:
        reply = "✅ Your order has been placed successfully."

    else:
        reply = (
            "Hello 👋 Welcome to our Grocery Store.\n"
            "Type `menu` to see available items."
        )

    # Save outgoing message
    db.add(Message(
        tenant_id=tenant.id,
        user_id=user.id,
        direction="out",
        message_text=reply
    ))
    db.commit()

    return reply

# =================================================
# WEBHOOK VERIFICATION
# =================================================
@app.get("/webhook/whatsapp")
def verify_webhook(
    hub_mode: str = None,
    hub_challenge: str = None,
    hub_verify_token: str = None
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    return {"error": "verification failed"}

# =================================================
# WHATSAPP INCOMING MESSAGE
# =================================================
@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    payload = await request.json()

    try:
        message = payload["entry"][0]["changes"][0]["value"]["messages"][0]
        phone = message["from"]
        text = message["text"]["body"]
    except Exception:
        return {"status": "ignored"}

    db = next(get_db())

    # DEMO: FIRST TENANT (GROCERY)
    tenant = db.query(Tenant).filter(
        Tenant.domain_type == "grocery"
    ).first()

    process_grocery_chat(phone, text, tenant, db)

    send_template_message(phone)

    return {"status": "sent"}

# =================================================
# SEND TEMPLATE MESSAGE (META DEMO RULE)
# =================================================
def send_template_message(to: str):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": "hello_world",
            "language": {"code": "en_US"}
        }
    }

    requests.post(url, headers=headers, json=data)
