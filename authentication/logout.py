import jwt
from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from utilities.utility import decode_token
from utilities.database import get_db
from utilities.models import Session as UserSession

router = APIRouter(tags=["Logout"], prefix="/auth")

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("refresh_token")

    if token:
        try:
            payload = decode_token(token)
            if payload.get("type") == "refresh":
                await db.execute(delete(UserSession).where(UserSession.uuid == payload.get("uuid")))
                await db.commit()
        except jwt.PyJWTError:
            pass

    response.delete_cookie("refresh_token", httponly=True, secure=False, samesite="none")
    return {"message": "Logged out successfully."}