from fastapi import FastAPI, Request
from sqlalchemy.orm import Session
import requests

from app.db import Base, engine
from app.deps import get_db
from app.models import Tenant, User, Message, ConversationSession

# =================================================
# CONFIG
# =================================================
WHATSAPP_TOKEN = "PASTE_META_ACCESS_TOKEN"
PHONE_NUMBER_ID = "PASTE_PHONE_NUMBER_ID"
VERIFY_TOKEN = "verify_123"

# =================================================
# APP INIT
# =================================================
app = FastAPI(title="Multitenant WhatsApp Chatbot – Restaurant Demo")
Base.metadata.create_all(bind=engine)

# =================================================
# HEALTH
# =================================================
@app.get("/health")
def health():
    return {"status": "ok"}

# =================================================
# RESTAURANT CHAT LOGIC
# =================================================
def process_restaurant_chat(phone: str, text: str, tenant: Tenant, db: Session):

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

    # Save incoming
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

    # -------- RESTAURANT FLOW --------
    if "menu" in text:
        template = "restaurant_menu"
        params = []

    elif text in ["pizza", "burger", "pasta"]:
        session.context["item"] = text
        db.commit()
        template = "restaurant_item_received"
        params = [text.title()]

    elif text.startswith("order"):
        item = session.context.get("item", "item")
        template = "restaurant_order_confirmed"
        params = [item.title()]
        session.state = "idle"
        session.context = {}
        db.commit()

    else:
        template = "restaurant_welcome"
        params = []

    return template, params

# =================================================
# WEBHOOK VERIFY
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
# WHATSAPP INCOMING
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

    # DEMO: RESTAURANT TENANT
    tenant = db.query(Tenant).filter(
        Tenant.domain_type == "restaurant"
    ).first()

    template, params = process_restaurant_chat(phone, text, tenant, db)

    send_template(phone, template, params)

    return {"status": "sent"}

# =================================================
# SEND TEMPLATE
# =================================================
def send_template(to: str, template_name: str, params: list):

    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

    components = []
    if params:
        components.append({
            "type": "body",
            "parameters": [{"type": "text", "text": p} for p in params]
        })

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": "en_US"},
            "components": components
        }
    }

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    requests.post(url, headers=headers, json=data)
