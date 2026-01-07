from fastapi import FastAPI, Depends, Request, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
import uuid
import requests

from app.db import Base, engine
from app.deps import get_db, get_current_tenant
from app.models import (
    Tenant,
    User,
    Message,
    FAQ,
    ConversationSession,
    Appointment,
    MenuItem,
    Cart,
    CartItem
)

# -------------------------------------------------
# ENV (move to .env later)
# -------------------------------------------------
WHATSAPP_TOKEN = "PASTE_META_ACCESS_TOKEN"
PHONE_NUMBER_ID = "PASTE_PHONE_NUMBER_ID"
VERIFY_TOKEN = "my_verify_token"

# -------------------------------------------------
# App init
# -------------------------------------------------
app = FastAPI(title="Multitenant WhatsApp Chatbot")
Base.metadata.create_all(bind=engine)

# -------------------------------------------------
# Health
# -------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

# -------------------------------------------------
# Create Tenant
# -------------------------------------------------
@app.post("/tenants")
def create_tenant(
    name: str,
    domain_type: str,
    db: Session = Depends(get_db)
):
    tenant = Tenant(
        name=name,
        domain_type=domain_type,
        api_key=str(uuid.uuid4())
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    return {
        "tenant_id": str(tenant.id),
        "api_key": tenant.api_key
    }

# -------------------------------------------------
# CORE CHAT LOGIC
# -------------------------------------------------
def process_chat(phone: str, message: str, tenant: Tenant, db: Session):
    msg = message.lower()

    user = db.query(User).filter(
        User.tenant_id == tenant.id,
        User.phone == phone
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

    db.add(Message(
        tenant_id=tenant.id,
        user_id=user.id,
        direction="in",
        message_text=message
    ))

    session = db.query(ConversationSession).filter(
        ConversationSession.tenant_id == tenant.id,
        ConversationSession.user_id == user.id
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

    # ---- SIMPLE FAQ FLOW ----
    faq = db.query(FAQ).filter(
        FAQ.tenant_id == tenant.id,
        FAQ.question.ilike(f"%{msg}%")
    ).first()

    reply = faq.answer if faq else "Sorry, I didn't understand."

    db.add(Message(
        tenant_id=tenant.id,
        user_id=user.id,
        direction="out",
        message_text=reply
    ))

    db.commit()
    return reply

# -------------------------------------------------
# Swagger API chat
# -------------------------------------------------
@app.post("/chat/message")
def chat_api(
    phone: str,
    message: str,
    tenant=Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    reply = process_chat(phone, message, tenant, db)
    return {"reply": reply}

# -------------------------------------------------
# WhatsApp Webhook Verification (META REQUIRED)
# -------------------------------------------------
@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return PlainTextResponse(content=hub_challenge)

    return PlainTextResponse("Verification failed", status_code=403)

# -------------------------------------------------
# WhatsApp Incoming Messages
# -------------------------------------------------
@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    payload = await request.json()
    print("📩 Incoming payload:", payload)

    try:
        value = payload["entry"][0]["changes"][0]["value"]
        message = value["messages"][0]
        phone = message["from"]
        text = message["text"]["body"]
    except Exception:
        return {"status": "ignored"}

    db = next(get_db())
    tenant = db.query(Tenant).first()

    reply = process_chat(phone, text, tenant, db)
    send_whatsapp_message(phone, reply)

    return {"status": "sent"}

# -------------------------------------------------
# Send WhatsApp message
# -------------------------------------------------
def send_whatsapp_message(to: str, text: str):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
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
    requests.post(url, headers=headers, json=payload)
