from typing import Literal
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CalorieEstimate(BaseModel):
    """
    Pydantic модель для structured output от LLM.

    Паттерн: Structured Outputs с Pydantic
    - OpenAI/OpenRouter API автоматически форсит LLM вернуть валидный JSON
    - Pydantic валидирует типы и constraint'ы
    - Нет нужды в ручном парсинге regex
    """
    calories: int = Field(
        ...,
        ge=1,
        le=5000,
        description="Оценка калорийности в ккал"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        ...,
        description="Уровень уверенности в оценке"
    )
    explanation: str = Field(
        ...,
        min_length=10,
        max_length=300,
        description="Краткое объяснение расчёта"
    )
    portion_grams: int = Field(
        ...,
        ge=1,
        le=2000,
        description="Примерный вес порции в граммах"
    )


class LLMCalorieEstimator:
    """
    Умное определение калорийности через LLM (OpenRouter).

    Паттерн: AI Fallback Strategy + Structured Outputs
    - Если OpenFoodFacts не находит продукт → используем LLM
    - LLM возвращает валидированный Pydantic объект
    - Автоматическая валидация типов и constraint'ов
    """

    def __init__(
        self,
        api_key: str,
        model: str = "arcee-ai/trinity-large-preview:free",
        base_url: str = "https://openrouter.ai/api/v1"
    ):
        """
        Инициализация LLM клиента для OpenRouter.

        Args:
            api_key: OpenRouter API key (sk-or-v1-...)
            model: Модель для использования
                  - anthropic/claude-3.5-sonnet (рекомендуется)
                  - openai/gpt-4o (поддерживает structured outputs)
                  - anthropic/claude-3-haiku (быстрая, дешёвая)
            base_url: OpenRouter API endpoint
        """
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model

    async def estimate_calories(
        self,
        food_description: str,
        user_context: str = ""
    ) -> CalorieEstimate:
        """
        Оценивает калорийность продукта через LLM.

        Args:
            food_description: Описание еды от пользователя
                             Примеры: "тарелка борща", "банан", "пицца пепперони большая"
            user_context: Дополнительный контекст (опционально)

        Returns:
            CalorieEstimate - Pydantic объект с полями:
            - calories: int
            - confidence: "high" | "medium" | "low"
            - explanation: str
            - portion_grams: int

        Raises:
            Exception: При ошибке LLM API
        """
        try:
            system_prompt = """Ты эксперт-диетолог. Оцени калорийность продукта на основе описания.

ВАЖНО - предполагай стандартную порцию если не указано иначе:
- Для "тарелка супа" используй ~300г
- Для "банан" используй средний банан ~120г
- Для "кусок пиццы" используй 1/8 большой пиццы ~150г
- Для "порция риса" используй ~150г

Твой ответ будет автоматически валидирован по JSON schema."""

            user_message = f"Оцени калорийность: {food_description}"
            if user_context:
                user_message += f"\nКонтекст: {user_context}"

            # Паттерн: Structured Outputs через response_format
            # OpenAI API форсит модель вернуть JSON согласно Pydantic схеме
            completion = await self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                response_format=CalorieEstimate,  # Pydantic модель
                temperature=0.3,  # Низкая для консистентности
            )

            # Автоматически распарсенный и валидированный объект
            result = completion.choices[0].message.parsed

            logger.info(
                f"LLM estimate for '{food_description}': "
                f"{result.calories} kcal ({result.confidence} confidence)"
            )

            return result

        except Exception as e:
            logger.error(f"LLM calorie estimation error: {e}")

            # Fallback при ошибке LLM
            # Ограничиваем длину explanation до 200 символов
            error_msg = str(e)[:100]  # Первые 100 символов ошибки
            return CalorieEstimate(
                calories=200,
                confidence="low",
                explanation=f"Ошибка AI оценки. Используется примерное значение 200 ккал на стандартную порцию.",
                portion_grams=100
            )


# ============================================================================
# ПАТТЕРН: Structured Outputs с Pydantic (Modern LLM Best Practice)
# ============================================================================
#
# **Преимущества над ручным парсингом:**
#
# 1. **Гарантированная валидация**
#    - Pydantic автоматически проверяет типы (int, str, Literal)
#    - Field constraints (ge=1, le=5000) валидируются
#    - Нет необходимости в try-except для парсинга JSON
#
# 2. **Type Safety**
#    - IDE autocomplete работает с result.calories
#    - MyPy/Pylance проверяет типы статически
#    - Меньше runtime ошибок
#
# 3. **API Enforcement**
#    - OpenAI API форсит LLM вернуть валидный JSON
#    - Если LLM не может сгенерировать валидный ответ → автоматический retry
#    - Меньше "мусорных" ответов от LLM
#
# 4. **Документация как код**
#    - Field(description=...) автоматически передаётся в LLM prompt
#    - Pydantic схема = документация для других разработчиков
#
# **Применение в AI-ботах:**
#
# - Персональные рекомендации: `class FoodRecommendation(BaseModel)`
# - Анализ фото еды: `class FoodDetection(BaseModel)` с multimodal LLM
# - Генерация планов: `class WorkoutPlan(BaseModel)`
# - Чат-бот с actions: `class BotAction(BaseModel)` с Literal["send_message", "log_food"]
#
# Structured Outputs — стандарт для production LLM applications.
# ============================================================================
