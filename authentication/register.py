from utilities.utility import create_token
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status
from pwdlib import PasswordHash
from utilities.database import get_db
from utilities.schema import UserCreate
from utilities.models import User
from utilities.send_email import send_email
from fastapi import BackgroundTasks

password_hash = PasswordHash.recommended()

def get_password_hash(password):
    return password_hash.hash(password)

# id name age email hashed_password is_verified created_at 
router = APIRouter(tags=["Authentication"], prefix="/auth")
@router.post("/signup")
async def create_user(user: UserCreate, bg: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    is_user = (await db.execute(select(User).where(User.email == user.email))).first()
    if is_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
    hashed_password = get_password_hash(user.password)
    new_user = User(name=user.name, age=user.age, email=user.email, hashed_password=hashed_password, role=user.role)
    db.add(new_user)
    
    await db.commit()
    payload={
        "id": new_user.id,
        "email": new_user.email,
        "type": "verify",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10)
    }
    bg.add_task(send_email, user.email, "Verify Email", f"<p>Verify your email by clicking the link: http://localhost:3000/verify-email/{create_token(payload)}</p>")
    return {"response": "User created successfully. Check you email for verification."}