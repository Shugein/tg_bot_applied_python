import aiohttp
from typing import Optional
import logging

# Настройка логирования для отладки API вызовов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WeatherAPIClient:
    """
    Клиент для OpenWeatherMap API.

    Паттерн: External API Client
    - Изолированный класс для работы с одним API
    - Возвращает Optional[T] для graceful degradation
    - Логирует ошибки, но не падает

    Критично для AI-ботов:
    - Внешние API могут быть недоступны
    - Rate limits, timeouts, сетевые ошибки
    - Бот должен работать даже если API не отвечает
    """

    def __init__(self, api_key: str):
        """
        Инициализация клиента.

        Args:
            api_key: API ключ от OpenWeatherMap
                    Получить: https://openweathermap.org/api
                    Free tier: 1000 calls/day
        """
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    async def get_temperature(self, city: str) -> Optional[float]:
        """
        Получает текущую температуру для города.

        Использует OpenWeatherMap Current Weather API.
        https://openweathermap.org/current

        Args:
            city: Название города (на английском или русском)
                 Примеры: "Moscow", "Санкт-Петербург", "New York"

        Returns:
            Температура в градусах Цельсия или None при ошибке

        Паттерн: Graceful Degradation
        - Если API не отвечает → возвращаем None
        - Caller сам решает что делать (использовать default или показать ошибку)
        - Бот НЕ падает из-за недоступности погоды
        """
        try:
            params = {
                "q": city,
                "appid": self.api_key,
                "units": "metric",  # Температура в Цельсиях
                "lang": "ru"        # Описание погоды на русском (опционально)
            }

            # Паттерн: aiohttp Context Manager
            # async with гарантирует закрытие соединения
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)  # 10 секунд timeout
                ) as response:

                    # Проверка статуса ответа
                    if response.status == 200:
                        data = await response.json()
                        temperature = data["main"]["temp"]

                        logger.info(
                            f"Weather API: {city} → {temperature}°C"
                        )
                        return temperature

                    elif response.status == 404:
                        # Город не найден
                        logger.warning(
                            f"Weather API: City '{city}' not found (404)"
                        )
                        return None

                    elif response.status == 401:
                        # Невалидный API ключ
                        logger.error(
                            f"Weather API: Invalid API key (401)"
                        )
                        return None

                    else:
                        # Другие ошибки
                        logger.error(
                            f"Weather API error {response.status} for {city}"
                        )
                        return None

        except aiohttp.ClientError as e:
            # Сетевые ошибки (timeout, connection refused, etc.)
            logger.error(f"Weather API network error: {e}")
            return None

        except KeyError as e:
            # JSON структура изменилась (API breaking change)
            logger.error(f"Weather API unexpected response structure: {e}")
            return None

        except Exception as e:
            # Неожиданные ошибки (на всякий случай)
            logger.error(f"Weather API unexpected error: {e}")
            return None


# ============================================================================
# ПАТТЕРН: API Client Best Practices для AI-ботов
# ============================================================================
#
# 1. **Timeouts**: Всегда устанавливай timeout (10 сек для погоды достаточно)
#    Без timeout — запрос может висеть минутами
#
# 2. **Error Handling**: Обрабатывай конкретные ошибки (404, 401, timeout)
#    Возвращай None вместо exception — caller сам решит что делать
#
# 3. **Logging**: Логируй все ошибки с контекстом (город, статус код)
#    Помогает дебажить проблемы в production
#
# 4. **Optional Return**: Optional[float] явно говорит "может быть None"
#    Caller обязан проверить: if temp is not None: ...
#
# 5. **Context Managers**: async with для автоматического закрытия соединений
#    Предотвращает утечки ресурсов
#
# Для AI-ботов с LLM это особенно важно:
# - LLM вызовы могут занимать 3-30 секунд
# - Rate limits от OpenAI/Anthropic (60 req/min)
# - Нужны retry с exponential backoff
# - Fallback на кешированные результаты
# ============================================================================
