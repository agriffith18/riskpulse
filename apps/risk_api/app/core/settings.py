from pydantic_settings import BaseSettings # type: ignore
from pydantic import Field # type: ignore

class Settings(BaseSettings):
    MONGO_URL: str = Field(..., env="MONGO_URL")
    # you can add more, e.g. JWT_SECRET: str, REDIS_URL: str, etc.

    class Config:
        env_file = ".env"          # for local development
        env_file_encoding = "utf-8"

# create a single settings instance
settings = Settings()
