"""
Handlers package — Presentation Layer.

Паттерн: Router Registration
- Каждый модуль (water.py, food.py) создаёт свой Router
- __init__.py собирает все роутеры в одну функцию setup_handlers()
- bot.py вызывает setup_handlers(dp) — и всё подключено

Преимущества для AI-ботов:
- Легко добавить новые функции (создал food_recommendations.py → добавил 1 строку сюда)
- Можно условно подключать роутеры (if settings.ENABLE_PREMIUM: dp.include_router(premium.router))
- Тестирование: каждый роутер тестируется изолированно
"""

from aiogram import Dispatcher


def setup_handlers(dp: Dispatcher):
    """
    Подключает все роутеры обработчиков к диспетчеру.

    Порядок подключения важен:
    - Более специфичные фильтры должны быть раньше
    - Общие fallback handlers — в конце

    Args:
        dp: Telegram Bot Dispatcher
    """
    # Импортируем роутеры здесь, чтобы избежать circular imports
    # и чтобы модули handlers/ были независимыми друг от друга

    from . import basic, profile, water, workout, progress, food

    # Подключаем роутеры
    # Порядок важен: базовые команды первыми
    dp.include_router(basic.router)
    dp.include_router(profile.router)
    dp.include_router(water.router)
    dp.include_router(food.router)
    dp.include_router(workout.router)
    dp.include_router(progress.router)

    print("✅ Handlers подключены: basic, profile, water, food, workout, progress")
