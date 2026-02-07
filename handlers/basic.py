from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart

from storage.user_storage import UserStorage
from services.calculator import HealthCalculator

router = Router()
storage = UserStorage()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """
    Обработчик команды /start - первое взаимодействие с ботом.

    Паттерн: Onboarding Flow
    - Приветствие
    - Краткое описание возможностей
    - Призыв к действию (call-to-action)
    """
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "друг"

    # Проверяем есть ли уже профиль
    user_data = await storage.get_user(user_id)
    has_profile = user_data is not None

    if has_profile:
        # Returning user
        await message.reply(
            f"👋 С возвращением, {first_name}!\n\n"
            f"📊 Твой профиль:\n"
            f"├ Вес: {user_data.profile.weight_kg} кг\n"
            f"├ Цель воды: {user_data.profile.water_goal_ml} мл\n"
            f"└ Цель калорий: {user_data.profile.calorie_goal} ккал\n\n"
            f"📝 Быстрые команды:\n"
            f"/log_water - Добавить воду\n"
            f"/log_food - Добавить еду\n"
            f"/log_workout - Тренировка\n"
            f"/check_progress - Прогресс\n"
            f"/help - Все команды"
        )
    else:
        # New user - onboarding
        await message.reply(
            f"👋 Привет, {first_name}!\n\n"
            f"🏋️ Health Tracking Bot поможет тебе:\n"
            f"✅ Отслеживать норму воды\n"
            f"✅ Считать калории с AI помощью\n"
            f"✅ Логировать тренировки\n"
            f"✅ Следить за прогрессом\n\n"
            f"🚀 Начни с настройки профиля:\n"
            f"/set_profile - Создать профиль\n\n"
            f"❓ Нужна помощь? /help"
        )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Обработчик команды /help - справка по командам.

    Паттерн: Structured Help
    - Группируем команды по категориям
    - Примеры использования
    - Указываем на продвинутые функции
    """
    supported_workouts = ", ".join(HealthCalculator.get_supported_workouts())

    await message.reply(
        f"📖 Справка по командам\n\n"
        f"🔧 Настройка:\n"
        f"/start - Главное меню\n"
        f"/set_profile - Настроить профиль (вес, рост, цели)\n\n"
        f"📝 Логирование:\n"
        f"/log_water - Добавить воду\n"
        f"  Пример: /log_water 250\n\n"
        f"/log_food - Добавить еду\n"
        f"  Пример: /log_food банан\n"
        f"  💡 Если продукт не найден - AI оценит калории!\n\n"
        f"/log_workout - Тренировка\n"
        f"  Пример: /log_workout running 30\n"
        f"  Типы: {supported_workouts}\n\n"
        f"📊 Прогресс:\n"
        f"/check_progress - Посмотреть прогресс за сегодня\n\n"
        f"ℹ️ Информация:\n"
        f"/help - Эта справка\n\n"
        f"💡 Полезные фишки:\n"
        f"• Данные сохраняются автоматически\n"
        f"• Счётчики сбрасываются в полночь\n"
        f"• AI оценивает калории для любых продуктов\n"
        f"• Тренировки увеличивают норму воды"
    )


# ============================================================================
# ПАТТЕРН: Onboarding & Help для AI-ботов
# ============================================================================
#
# **Лучшие практики для /start:**
#
# 1. **Персонализация**
#    - Используй first_name пользователя
#    - Разные сообщения для новых vs returning users
#    - Показывай текущий статус (профиль, прогресс)
#
# 2. **Clear Call-to-Action**
#    - Для новых: "Создай профиль →"
#    - Для существующих: "Продолжай логировать →"
#    - Одна главная кнопка, не перегружай
#
# 3. **Value Proposition**
#    - Что бот делает (3-5 пунктов)
#    - Уникальная фишка (AI для калорий)
#    - Почему использовать этот бот
#
# **Лучшие практики для /help:**
#
# 1. **Структура по категориям**
#    - Настройка
#    - Основные функции
#    - Дополнительные фишки
#
# 2. **Примеры использования**
#    - Не просто "/log_water"
#    - А "/log_water 250" с пояснением
#
# 3. **Highlight продвинутых функций**
#    - AI оценка калорий
#    - Автоматические расчёты
#    - Интеграции с API
#
# **Для AI-ботов специфика:**
#
# - Объясни когда используется AI (fallback, recommendations)
# - Покажи примеры AI возможностей
# - Дай понять что бот "умный", но не страшный
#
# Пример расширенного /start для AI-бота с персонализацией:
#
# @router.message(CommandStart())
# async def cmd_start(message: Message):
#     user_id = message.from_user.id
#     user_data = await storage.get_user(user_id)
#
#     if user_data:
#         # Персонализированное приветствие на основе данных
#         streak = calculate_streak(user_data)
#         last_action = get_last_action(user_data)
#
#         await message.reply(
#             f"Привет! Streak: {streak} дней 🔥\n"
#             f"Последнее: {last_action}\n\n"
#             f"AI рекомендация: {get_ai_recommendation(user_data)}"
#         )
#     else:
#         # Onboarding с AI preview
#         await message.reply(
#             "Попробуй AI: напиши /log_food тарелка борща"
#         )
#
# Это стандарт для modern AI-ботов с персонализацией.
# ============================================================================
