from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from storage.user_storage import UserStorage

# Создаём Router для этого модуля
# Каждый handler file имеет свой router
router = Router()

# Singleton instance storage (создаётся один раз при импорте модуля)
# Это простой паттерн для небольших ботов
# Для больших приложений лучше использовать Dependency Injection
storage = UserStorage()


@router.message(Command("check_progress"))
async def check_daily_progress(message: Message):
    """
    Показывает ежедневный прогресс по воде и калориям.

    Паттерн: Handler → Storage → Response
    1. Получаем данные из storage (слой данных)
    2. Рассчитываем проценты и статусы (presentation logic)
    3. Форматируем красивый ответ с эмодзи

    Этот handler демонстрирует ключевой принцип:
    - НЕТ бизнес-логики здесь (расчёты делает calculator)
    - НЕТ работы с JSON (делает storage)
    - Только: получить данные → показать пользователю
    """
    user_id = message.from_user.id

    # Паттерн: Early Return для валидации
    # Если профиль не создан → подсказываем пользователю и выходим
    user_data = await storage.get_user(user_id)
    if not user_data:
        await message.reply(
            "❌ Профиль не найден.\n\n"
            "Сначала настрой свой профиль командой /set_profile"
        )
        return

    # Извлекаем данные для удобства
    profile = user_data.profile
    daily = user_data.daily

    # Расчёт прогресса воды
    water_pct = (
        (daily.water_ml / profile.water_goal_ml * 100)
        if profile.water_goal_ml > 0
        else 0
    )
    water_remaining = max(0, profile.water_goal_ml - daily.water_ml)
    water_status = "✅" if daily.water_ml >= profile.water_goal_ml else "⏳"

    # Расчёт прогресса калорий
    cal_pct = (
        (daily.calories / profile.calorie_goal * 100)
        if profile.calorie_goal > 0
        else 0
    )
    cal_remaining = max(0, profile.calorie_goal - daily.calories)

    # Статус калорий
    if daily.calories > profile.calorie_goal * 1.1:  # Превышение на 10%
        cal_status = "⚠️"
    elif daily.calories >= profile.calorie_goal:
        cal_status = "✅"
    else:
        cal_status = "⏳"

    # Нетто калории (съедено - сожжено)
    net_calories = daily.calories - daily.burned_calories

    # Мотивационное сообщение
    if water_pct >= 100 and cal_pct <= 110:  # Вода выполнена, калории в норме
        motivation = "🎉 Отличная работа! Цели достигнуты!"
    elif water_pct >= 80 and cal_pct <= 120:
        motivation = "💪 Хороший прогресс! Продолжай в том же духе!"
    else:
        motivation = "📊 Следи за показателями — ты на верном пути!"

    # Форматированный ответ
    await message.reply(
        f"📊 Прогресс за {daily.date}\n\n"
        f"{water_status} Вода: {daily.water_ml}/{profile.water_goal_ml} мл "
        f"({water_pct:.1f}%)\n"
        f"   └ Осталось: {water_remaining} мл\n\n"
        f"{cal_status} Калории: {daily.calories}/{profile.calorie_goal} ккал "
        f"({cal_pct:.1f}%)\n"
        f"   ├ Осталось: {cal_remaining} ккал\n"
        f"   ├ 🔥 Сожжено: {daily.burned_calories} ккал\n"
        f"   └ 📈 Нетто: {net_calories} ккал\n\n"
        f"{motivation}"
    )


# Паттерн: Async Handler
# Все handlers в aiogram 3.x асинхронные
# - await storage.get_user() не блокирует бот
# - Бот может обрабатывать других пользователей параллельно
# - Критично для AI-ботов где LLM вызовы занимают 3-10 секунд
