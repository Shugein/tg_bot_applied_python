from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from storage.user_storage import UserStorage

router = Router()
storage = UserStorage()


@router.message(Command("log_water"))
async def log_water_intake(message: Message):
    """
    Логирует потребление воды.

    Формат: /log_water <миллилитры>
    Пример: /log_water 250

    Паттерн: Command Argument Parsing
    - Быстрое логирование без FSM диалога
    - Пользователь вводит всё в одной команде
    - Валидация и подсказки при ошибках

    Когда использовать:
    - Простые операции (1 параметр)
    - Частые действия (логирование воды/еды)
    - Опытные пользователи предпочитают скорость

    Для сложных операций (много параметров) используй FSM.
    """
    user_id = message.from_user.id

    # Проверка профиля
    user_data = await storage.get_user(user_id)
    if not user_data:
        await message.reply(
            "❌ Профиль не найден.\n\n"
            "Сначала настрой профиль: /set_profile"
        )
        return

    # Парсинг аргумента команды
    # message.text = "/log_water 250"
    # parts = ["/log_water", "250"]
    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        # Пользователь ввёл только /log_water без количества
        await message.reply(
            "❓ Укажи количество воды в миллилитрах.\n\n"
            "**Формат**: `/log_water <мл>`\n"
            "**Пример**: `/log_water 250`")
        return

    # Валидация числа
    try:
        amount = int(parts[1])
    except ValueError:
        await message.reply(
            "❌ Неверный формат. Введи число.\n\n"
            "**Пример**: `/log_water 250`")
        return

    # Валидация диапазона
    # Защита от случайных опечаток (25000 вместо 250)
    if amount <= 0 or amount > 5000:
        await message.reply(
            "❌ Количество должно быть от 1 до 5000 мл.\n\n"
            "Проверь ввод: может опечатка?"
        )
        return

    # Паттерн: Incremental Update
    # storage.update_daily ДОБАВЛЯЕТ amount к текущему значению
    # Не заменяет, а накапливает
    await storage.update_daily(user_id, water_ml=amount)

    # Получаем обновлённые данные для прогресса
    user_data = await storage.get_user(user_id)
    total_water = user_data.daily.water_ml
    goal = user_data.profile.water_goal_ml
    percentage = (total_water / goal * 100) if goal > 0 else 0
    remaining = max(0, goal - total_water)

    # Прогресс-бар (визуальный индикатор)
    # 0-20% → ⬜⬜⬜⬜⬜
    # 20-40% → ⬜⬜⬜⬜
    # ...
    # 100%+ → ✅✅✅✅✅
    filled = min(5, int(percentage // 20))
    empty = 5 - filled
    progress_bar = "💧" * filled + "⬜" * empty

    # Мотивационное сообщение
    if percentage >= 100:
        congrats = "🎉 Цель выполнена!"
    elif percentage >= 80:
        congrats = "💪 Почти у цели!"
    elif percentage >= 50:
        congrats = "👍 Хороший прогресс!"
    else:
        congrats = "📊 Продолжай пить воду!"

    await message.reply(
        f"✅ Добавлено **{amount} мл** воды\n\n"
        f"{progress_bar}\n\n"
        f"**Сегодня**: {total_water}/{goal} мл ({percentage:.1f}%)\n"
        f"**Осталось**: {remaining} мл\n\n"
        f"{congrats}")


# Паттерн сравнения: Command Args vs FSM
#
# /log_water 250  ← COMMAND ARGS (этот handler)
# + Быстро для опытных пользователей
# + Минимум сообщений (1 вместо 3)
# - Сложнее для новичков
# - Нужна валидация и подсказки
#
# /log_water → "Сколько?" → 250  ← FSM
# + Понятнее для новичков (step-by-step)
# + Можно добавить подсказки на каждом шаге
# - Больше сообщений
# - Медленнее
#
# Для AI-ботов часто нужны оба варианта:
# - /quick_log 250 ← для power users
# - /log → FSM диалог ← для новичков
