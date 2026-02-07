from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from storage.user_storage import UserStorage
from services.calculator import HealthCalculator

router = Router()
storage = UserStorage()


@router.message(Command("log_workout"))
async def log_workout(message: Message):
    """
    Логирует тренировку: тип и длительность.

    Формат: /log_workout <тип> <минуты>
    Пример: /log_workout running 30

    Паттерн: Command with Multiple Arguments
    - Парсим 2 параметра из одной команды
    - Рассчитываем сожжённые калории через MET values
    - Обновляем норму воды (тренировка увеличивает потребность)
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

    # Парсинг команды: /log_workout running 30
    parts = message.text.split()

    if len(parts) < 3:
        supported = ", ".join(HealthCalculator.get_supported_workouts())
        await message.reply(
            f"❓ Укажи тип тренировки и время.\n\n"
            f"Формат: /log_workout тип минуты\n"
            f"Пример: /log_workout running 30\n\n"
            f"Поддерживаемые типы:\n{supported}")
        return

    workout_type = parts[1].lower()

    # Валидация минут
    try:
        minutes = int(parts[2])
        if minutes <= 0 or minutes > 300:
            await message.reply(
                "❌ Время тренировки должно быть от 1 до 300 минут."
            )
            return
    except ValueError:
        await message.reply(
            "❌ Неверный формат времени. Введи число.\n\n"
            "Пример: /log_workout running 30")
        return

    # Проверка типа тренировки
    supported_workouts = HealthCalculator.get_supported_workouts()
    if workout_type not in supported_workouts:
        await message.reply(
            f"❌ Неизвестный тип тренировки: {workout_type}\n\n"
            f"Поддерживаемые типы:\n{', '.join(supported_workouts)}")
        return

    # Рассчитываем сожжённые калории
    burned_calories = HealthCalculator.calculate_workout_calories(
        workout_type=workout_type,
        duration_minutes=minutes,
        weight_kg=user_data.profile.weight_kg
    )

    # Рассчитываем дополнительную потребность в воде
    water_bonus = HealthCalculator.calculate_workout_water_bonus(minutes)

    # Обновляем данные: добавляем сожжённые калории
    await storage.update_daily(user_id, burned_calories=burned_calories)

    # Увеличиваем норму воды на время тренировки
    user_data.profile.water_goal_ml += water_bonus
    await storage.save_profile(user_id, user_data.profile)

    # Получаем обновлённые данные
    user_data = await storage.get_user(user_id)

    await message.reply(
        f"🏋️ Тренировка добавлена!\n\n"
        f"Тип: {workout_type.capitalize()}\n"
        f"Время: {minutes} мин\n"
        f"Сожжено: {burned_calories} ккал 🔥\n\n"
        f"💧 Дополнительная вода: +{water_bonus} мл\n"
        f"Новая цель воды: {user_data.profile.water_goal_ml} мл\n\n"
        f"💡 Не забудь выпить воду после тренировки!")
