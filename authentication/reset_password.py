from pydantic import BaseModel, Field
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from pwdlib import PasswordHash
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from utilities.database import get_db
from utilities.models import Session as UserSession, User
from utilities.utility import decode_token

router = APIRouter(tags=["Authentication"], prefix="/auth")
password_hash = PasswordHash.recommended()

class ResetPasswordSchema(BaseModel):
    token: str
    new_password: str = Field(min_length=8)

@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(schema: ResetPasswordSchema, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(schema.token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset link has expired",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset link",
        )

    if payload.get("type") != "reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type",
        )

    result = await db.execute(select(User).where(User.id == payload.get("id")))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.hashed_password = password_hash.hash(schema.new_password)
    await db.execute(delete(UserSession).where(UserSession.user_id == user.id))
    await db.commit()
    return {"message": "Password reset successfully. Please log in again."}