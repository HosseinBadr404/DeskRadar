from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    
    AI_CORE_URL: str
    DATABASE_URL: str

    class Config:
        env_file = ".env"


settings = Settings()