import secrets

import bcrypt
from fastapi import HTTPException, Request
from sqlmodel import Session

from models import AuditLog


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def csrf_token(request: Request) -> str:
    token = request.session.get("csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf"] = token
    return token


async def verify_csrf(request: Request):
    form = await request.form()
    sent = str(form.get("csrf_token", ""))
    saved = request.session.get("csrf", "")
    if not saved or not secrets.compare_digest(sent, saved):
        raise HTTPException(status_code=403, detail="CSRF token tidak valid")


def audit(session: Session, event: str, detail: str = "", user_id=None, request: Request = None):
    ip = request.client.host if request and request.client else None
    session.add(AuditLog(user_id=user_id, event=event, detail=detail[:300], ip=ip))
    session.commit()
