from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    MAIL_PASSWORD: str
    DATABASE_URL: str
    GROQ_API_KEY: str
    class Config:
        env_file = ".env"

settings = Settings()
