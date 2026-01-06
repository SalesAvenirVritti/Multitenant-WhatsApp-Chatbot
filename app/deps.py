from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Tenant


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_tenant(
    x_api_key: str = Header(..., alias="X-API-KEY"),
    db: Session = Depends(get_db)
):
    tenant = db.query(Tenant).filter(Tenant.api_key == x_api_key).first()

    if not tenant:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    return tenant
