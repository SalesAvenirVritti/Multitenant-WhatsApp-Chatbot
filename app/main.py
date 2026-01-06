from fastapi import FastAPI, Depends, Request
from sqlalchemy.orm import Session
import uuid
import os

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
# ENV (for now hardcoded – later move to .env)
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
    domain_type: str,  # hospital | restaurant
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
# Tenant Info
# -------------------------------------------------
@app.get("/tenant/me")
def tenant_me(tenant=Depends(get_current_tenant)):
    return {
        "tenant_id": str(tenant.id),
        "name": tenant.name,
        "domain_type": tenant.domain_type
    }

# -------------------------------------------------
# FAQ
# -------------------------------------------------
@app.post("/faq")
def add_faq(
    question: str,
    answer: str,
    tenant=Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    db.add(FAQ(
        tenant_id=tenant.id,
        question=question.lower(),
        answer=answer
    ))
    db.commit()
    return {"message": "FAQ added"}

# -------------------------------------------------
# Menu (Restaurant)
# -------------------------------------------------
@app.post("/menu")
def add_menu(
    name: str,
    price: str,
    category: str = None,
    tenant=Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    if tenant.domain_type != "restaurant":
        return {"error": "Not a restaurant tenant"}

    db.add(MenuItem(
        tenant_id=tenant.id,
        name=name.lower(),
        price=price,
        category=category
    ))
    db.commit()
    return {"message": "Menu item added"}

# -------------------------------------------------
# CORE CHAT LOGIC (USED BY SWAGGER + WHATSAPP)
# -------------------------------------------------
def process_chat(
    phone: str,
    message: str,
    tenant: Tenant,
    db: Session
):
    msg = message.lower()

    # User
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

    # Save incoming
    db.add(Message(
        tenant_id=tenant.id,
        user_id=user.id,
        direction="in",
        message_text=message
    ))

    # Session
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

    # ---------------- HOSPITAL ----------------
    if tenant.domain_type == "hospital":

        if session.state == "booking_doctor":
            session.context["doctor"] = message
            reply = "Which date do you prefer?"
            session.state = "booking_date"

        elif session.state == "booking_date":
            db.add(Appointment(
                tenant_id=tenant.id,
                user_id=user.id,
                doctor_name=session.context["doctor"],
                appointment_date=message
            ))
            reply = "✅ Appointment booked successfully"
            session.state = "idle"
            session.context = {}

        elif "appointment" in msg:
            reply = "Which doctor would you like to book?"
            session.state = "booking_doctor"

        else:
            faq = db.query(FAQ).filter(
                FAQ.tenant_id == tenant.id,
                FAQ.question.ilike(f"%{msg}%")
            ).first()
            reply = faq.answer if faq else "Sorry, I didn't understand."

    # ---------------- RESTAURANT ----------------
    else:

        if session.state == "ordering_size":
            session.context["size"] = message
            reply = "How many would you like?"
            session.state = "ordering_quantity"

        elif session.state == "ordering_quantity":
            cart = db.query(Cart).filter(
                Cart.tenant_id == tenant.id,
                Cart.user_id == user.id,
                Cart.status == "open"
            ).first()

            if not cart:
                cart = Cart(
                    tenant_id=tenant.id,
                    user_id=user.id
                )
                db.add(cart)
                db.commit()
                db.refresh(cart)

            db.add(CartItem(
                cart_id=cart.id,
                item_name=session.context["item"],
                size=session.context["size"],
                quantity=int(message)
            ))

            reply = "🛒 Item added to cart"
            session.state = "idle"
            session.context = {}

        else:
            menu = db.query(MenuItem).filter(
                MenuItem.tenant_id == tenant.id,
                MenuItem.name.ilike(f"%{msg}%")
            ).first()

            if menu:
                session.context["item"] = menu.name
                reply = "What size would you like?"
                session.state = "ordering_size"
            else:
                reply = "Please choose an item from the menu."

    # Save outgoing
    db.add(Message(
        tenant_id=tenant.id,
        user_id=user.id,
        direction="out",
        message_text=reply
    ))

    db.commit()
    return reply

# -------------------------------------------------
# Swagger / API chat
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
# WhatsApp Webhook Verification
# -------------------------------------------------
@app.get("/webhook/whatsapp")
def verify_webhook(
    hub_mode: str = None,
    hub_challenge: str = None,
    hub_verify_token: str = None
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    return {"status": "verification failed"}

# -------------------------------------------------
# WhatsApp Incoming Messages
# -------------------------------------------------
@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    payload = await request.json()

    try:
        value = payload["entry"][0]["changes"][0]["value"]
        message = value["messages"][0]
        phone = message["from"]
        text = message["text"]["body"]
    except Exception:
        return {"status": "ignored"}

    # ⚠️ For now: FIRST tenant (later map WhatsApp number → tenant)
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

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }

    requests.post(url, headers=headers, json=data)
import requests
from fastapi import Request

# -----------------------------------
# WhatsApp Webhook (Meta Cloud API)
# -----------------------------------

WHATSAPP_TOKEN = "PUT_YOUR_WHATSAPP_TOKEN_HERE"
PHONE_NUMBER_ID = "PUT_PHONE_NUMBER_ID_HERE"

@app.get("/webhook/whatsapp")
def verify_webhook(
    hub_mode: str = None,
    hub_challenge: str = None,
    hub_verify_token: str = None
):
    VERIFY_TOKEN = "my_verify_token"

    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)

    return {"error": "Verification failed"}


@app.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    data = await request.json()

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        phone = message["from"]
        text = message["text"]["body"]

        # 🔁 Call your existing chatbot logic
        response = chat_message(
            phone=phone,
            message=text,
            tenant=Depends(get_current_tenant),
            db=next(get_db())
        )

        reply_text = response["reply"]

        # 🔁 Send reply back to WhatsApp
        url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"body": reply_text}
        }

        requests.post(url, headers=headers, json=payload)

    except Exception as e:
        print("Webhook error:", e)

    return {"status": "received"}
