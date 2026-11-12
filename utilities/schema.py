from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, Literal

# id email hashed_password is_verified created_at 
class UserCreate(BaseModel):
    name: str
    age: Optional[int] = None
    email: EmailStr
    role: Literal["recruiter", "user"]
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str