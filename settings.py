from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Конфигурация приложения через Pydantic Settings.

    Паттерн: Configuration as Code
    - Все настройки в одном месте с type hints
    - Автозагрузка из .env файла
    - Валидация типов (OPENWEATHER_API_KEY должен быть str)

    Для AI-ботов это критично: часто нужно переключать API ключи
    (dev/prod), менять модели LLM, настраивать температуру generation.
    Всё это здесь, не хардкодится в коде.
    """

    # Telegram Bot
    BOT_TOKEN: str
    BOT_URL: str = 'https://t.me/prevelinoe_petanie_4all_hse_bot'

    # LLM API (OpenRouter в твоём случае)
    LLM_API_KEY: str

    # External APIs
    OPENWEATHER_API_KEY: str  # Получить на https://openweathermap.org/api

    # Storage
    USER_DATA_FILE: str = "user_data.json"  # Путь к файлу с данными

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()