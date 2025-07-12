from pydantic_settings import BaseSettings
from pydantic import ConfigDict
class Settings(BaseSettings):
    MONGO_URL: str 
    SECRET: str 
    ALGORITHM: str
    # can add more, e.g. JWT_SECRET: str, REDIS_URL: str, etc.

    model_config = ConfigDict(
        env_file = "../../../.env",
        env_file_encoding = "utf-8",
    )

# create a single settings instance
settings = Settings()
