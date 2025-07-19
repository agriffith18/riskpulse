from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

class Settings(BaseSettings):
    MONGO_URL: str 
    SECRET: str 
    ALGORITHM: str
    # can add more, e.g. JWT_SECRET: str, REDIS_URL: str, etc.

    model_config = ConfigDict()

# create a single settings instance
settings = Settings()
