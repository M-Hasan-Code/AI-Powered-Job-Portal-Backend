from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from utilities.database import get_db
from utilities.send_email import send_email
from pydantic import BaseModel, EmailStr
from utilities.models import User
from sqlalchemy import select

from utilities.utility import create_token

class EmailSchema(BaseModel):
    email: EmailStr

router = APIRouter(tags=["Authentication"], prefix="/auth")
@router.post("/forgot-password")
async def forgot_password(schema: EmailSchema, bg: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    user = await db.execute(select(User).where(User.email == schema.email))
    user = user.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not user.is_verified:
        payload = {
        "id": user.id,
        "email": user.email,
        "type": "verify",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10)            
        }

        bg.add_task(send_email, schema.email, "Verification Email", f"<p>Verify your email by clicking the link: http://localhost:3000/verify-email/{create_token(payload)}</p>")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is not verified. We sent you a verification link. Verify first, then reset your password.",
        )

    reset_payload = {
        "id": user.id,
        "email": user.email,
        "type": "reset",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    bg.add_task(
        send_email,
        user.email,
        "Reset Your Password",
        f"<p>Reset your password by clicking the link: "
        f"http://localhost:3000/reset-password/{create_token(reset_payload)}</p>"
        f"<p>This link expires in 10 minutes. If you didn't request it, ignore this email.</p>",
    )

    return {"message": "Password reset link has been sent to your email."}