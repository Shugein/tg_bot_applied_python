from aiogram import BaseMiddleware
from aiogram.types import Message


class LoggingMiddleware(BaseMiddleware):
    """
    Middleware для логирования всех входящих сообщений.

    Паттерн: Middleware Chain
    - Выполняется ДО handlers
    - Логирует каждое сообщение пользователя
    - Критично для деплоя: в логах видно все команды

    Для сдачи задания: скриншот логов должен показывать
    все команды пользователей через этот middleware.
    """

    async def __call__(self, handler, event: Message, data: dict):
        """
        Обрабатывает каждое сообщение.

        Args:
            handler: Следующий handler в цепочке
            event: Telegram Message
            data: Дополнительные данные

        Returns:
            Результат вызова handler
        """
        # Логируем сообщение
        user_id = event.from_user.id
        username = event.from_user.username or "NoUsername"
        text = event.text or "[Media/Sticker]"

        print(f"📨 Message from @{username} (ID: {user_id}): {text}")

        # Передаём управление следующему handler
        return await handler(event, data)


# ============================================================================
# ПАТТЕРН: Middleware для AI-ботов
# ============================================================================
#
# **Что можно добавить в Middleware:**
#
# 1. **Analytics & Logging**
#    - Какие команды используются чаще всего
#    - Время ответа handlers
#    - Ошибки и exceptions
#
# 2. **Authentication & Authorization**
#    - Проверка user_id в whitelist
#    - Premium features для платных пользователей
#    - Ban list для spam пользователей
#
# 3. **Rate Limiting**
#    - Ограничение запросов к LLM (например, 10/день для free tier)
#    - Throttling для дорогих операций
#
# 4. **Context Enrichment**
#    - Автоматическая загрузка user profile в data['user']
#    - Добавление timestamp, locale, etc.
#
# 5. **Error Handling**
#    - Try-except вокруг handler
#    - Отправка friendly error messages пользователю
#    - Логирование exceptions в Sentry/CloudWatch
#
# Пример расширенного middleware:
#
# class AIBotMiddleware(BaseMiddleware):
#     async def __call__(self, handler, event, data):
#         user_id = event.from_user.id
#
#         # Rate limiting
#         if not await check_rate_limit(user_id):
#             await event.reply("Too many requests. Try again later.")
#             return
#
#         # Load user context
#         data['user_profile'] = await storage.get_user(user_id)
#
#         # Execute handler with error handling
#         try:
#             return await handler(event, data)
#         except Exception as e:
#             logger.error(f"Handler error: {e}")
#             await event.reply("Oops! Something went wrong.")
#
# Это standard pattern для production AI-ботов.
# ============================================================================
