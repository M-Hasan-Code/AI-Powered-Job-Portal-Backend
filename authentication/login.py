import uuid
from fastapi import Response
from config import settings
from utilities.utility import create_token, hash_refresh_token
from utilities.models import User, Session
from utilities.schema import UserLogin
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from utilities.database import get_db
from pwdlib import PasswordHash
from sqlalchemy import select
from utilities.send_email import send_email
from fastapi import BackgroundTasks
from datetime import datetime, timedelta, timezone

router = APIRouter(tags=["Authentication"], prefix="/auth")

password_hash = PasswordHash.recommended()

def verify_password(plain_password: str, hashed_password: str):
    return password_hash.verify(plain_password, hashed_password)

@router.post("/login", status_code=status.HTTP_200_OK)
async def login(user_login: UserLogin, response: Response, bg: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_login.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    if not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    if not user.is_verified:
        payload = {
            "id": user.id,
            "email": user.email,
            "type": "verify",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=10)
        }
        bg.add_task(send_email, user.email, "Verify Email", f"<p>Verify your email by clicking the link: http://localhost:3000/verify-email/{create_token(payload)}</p>")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not verified. Please verify your email."
        )

    _uuid = str(uuid.uuid4())
    access_token = create_token({"id": user.id, "type": "access", "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)})
    refresh_token = create_token({"id": user.id, "uuid": _uuid, "type": "refresh", "exp": datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)})
    response.set_cookie("refresh_token", refresh_token, httponly=True, max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60, secure=False, samesite="lax")
    session = Session(
    uuid=_uuid,
    user_id=user.id,
    refresh_token=hash_refresh_token(refresh_token),
    expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
)
    db.add(session)
    await db.commit()

    return {"access_token": access_token}