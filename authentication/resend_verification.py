from utilities.send_email import send_email
from fastapi import APIRouter, status, Depends, HTTPException, BackgroundTasks
from utilities.database import get_db
from utilities.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from utilities.utility import create_token
from sqlalchemy import select
from datetime import datetime, timedelta, timezone

class resend_verification_request(BaseModel):
    email: EmailStr

router = APIRouter(tags=["Verification"], prefix="/auth")

@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification(request: resend_verification_request, bg: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if user.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already verified")
    
    payload={
        "id": user.id,
        "email": user.email,
        "type": "verify",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10)
    }

    bg.add_task(send_email, user.email, "Verify Email", f"<p>Verify your email by clicking the link: http://localhost:3000/verify-email/{create_token(payload)}</p>")
    return {"response": "Email sent successfully."}