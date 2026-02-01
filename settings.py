from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    BOT_TOKEN: str
    BOT_URL: str = 'https://t.me/prevelinoe_petanie_4all_hse_bot'

    LLM_API_KEY: str

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

settings = Settings()