import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from utilities.database import get_db
from utilities.models import Session as UserSession
from utilities.utility import create_token, decode_token, hash_refresh_token

router = APIRouter(tags=["Refresh"], prefix="/auth")


def unauthorized(msg="Invalid or expired refresh token"):
    return HTTPException(status.HTTP_401_UNAUTHORIZED, msg)


@router.post("/refresh")
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise unauthorized("Refresh token is missing")
    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        raise unauthorized()
    if payload.get("type") != "refresh":
        raise unauthorized("Invalid token type")

    result = await db.execute(select(UserSession).where(UserSession.uuid == payload.get("uuid")))
    session = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if not session or session.refresh_token != hash_refresh_token(token) or session.expires_at < now:
        raise unauthorized()

    new_uuid = str(uuid.uuid4())
    days = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    access = create_token({"id": session.user_id, "type": "access",
                           "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)})
    new_refresh = create_token({"id": session.user_id, "uuid": new_uuid, "type": "refresh", "exp": now + days})

    session.uuid, session.refresh_token, session.expires_at = new_uuid, hash_refresh_token(new_refresh), now + days
    await db.commit()

    response.set_cookie("refresh_token", new_refresh, httponly=True, max_age=int(days.total_seconds()),
                        secure=False, samesite="lax")
    return {"access_token": access}