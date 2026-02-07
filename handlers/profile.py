from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from storage.user_storage import UserStorage
from storage.models import UserProfile
from states import ProfileSetup
from services.calculator import HealthCalculator
from services.weather_api import WeatherAPIClient
from settings import settings

router = Router()
storage = UserStorage()
weather_api = WeatherAPIClient(settings.OPENWEATHER_API_KEY)


# ============================================================================
# ПАТТЕРН: Linear FSM Flow для многошагового сбора данных
# ============================================================================
#
# Шаг 1: /set_profile → запускает диалог → ProfileSetup.weight
# Шаг 2: user вводит вес → валидация → state.update_data(weight=...) → ProfileSetup.height
# Шаг 3: user вводит рост → валидация → state.update_data(height=...) → ProfileSetup.age
# ... и так далее
# Финал: собираем все данные из state.get_data() → создаём UserProfile → сохраняем
#
# Ключевые принципы:
# 1. Валидация НА КАЖДОМ ШАГЕ (если ошибка → return без смены состояния)
# 2. Данные накапливаются в FSMContext через update_data()
# 3. Storage НЕ трогаем до финального шага
# 4. Пользователь может ввести ошибку — handler повторяет запрос
# ============================================================================


@router.message(Command("set_profile"))
async def start_profile_setup(message: Message, state: FSMContext):
    """
    Запускает многошаговый диалог настройки профиля.

    Паттерн: FSM Entry Point
    - Отправляем приветственное сообщение с инструкциями
    - Переводим пользователя в первое состояние (ProfileSetup.weight)
    - НЕ собираем данные здесь — только запускаем процесс
    """
    await message.reply(
        "👋 Давай настроим твой профиль!\n\n"
        "Я буду задавать вопросы один за другим. "
        "Отвечай последовательно.\n\n"
        "🔢 **Шаг 1/6**: Введи свой вес в килограммах\n"
        "Пример: `70`")

    # Переводим в первое состояние FSM
    # Следующее сообщение пользователя попадёт в process_weight()
    await state.set_state(ProfileSetup.weight)


@router.message(ProfileSetup.weight)
async def process_weight(message: Message, state: FSMContext):
    """
    Обрабатывает ввод веса (первый шаг FSM).

    Паттерн: Validation → Store → Next State
    1. Парсим ввод (пытаемся преобразовать в float)
    2. Валидируем диапазон (30-300 кг)
    3. Если ошибка → подсказка и return (остаёмся в ProfileSetup.weight)
    4. Если OK → сохраняем в state.update_data() и переходим дальше
    """
    try:
        weight = float(message.text.strip())

        # Валидация диапазона (защита от опечаток: 7000 вместо 70)
        if weight < 30 or weight > 300:
            await message.reply(
                "❌ Вес должен быть от 30 до 300 кг.\n\n"
                "Проверь ввод и попробуй снова:"
            )
            return  # Остаёмся в ProfileSetup.weight

    except ValueError:
        # Пользователь ввёл не число
        await message.reply(
            "❌ Пожалуйста, введи число.\n\n"
            "Пример: `70`")
        return  # Остаёмся в ProfileSetup.weight

    # Сохраняем вес в FSM контекст
    # Данные хранятся В ПАМЯТИ FSM, не в storage!
    await state.update_data(weight_kg=weight)

    # Переходим к следующему шагу
    await message.reply(
        "✅ Вес сохранён!\n\n"
        "🔢 **Шаг 2/6**: Введи свой рост в сантиметрах\n"
        "Пример: `175`")
    await state.set_state(ProfileSetup.height)


@router.message(ProfileSetup.height)
async def process_height(message: Message, state: FSMContext):
    """Обрабатывает ввод роста (второй шаг FSM)."""
    try:
        height = float(message.text.strip())

        if height < 100 or height > 250:
            await message.reply(
                "❌ Рост должен быть от 100 до 250 см.\n\n"
                "Попробуй снова:"
            )
            return

    except ValueError:
        await message.reply(
            "❌ Пожалуйста, введи число.\n\n"
            "Пример: `175`")
        return

    await state.update_data(height_cm=height)

    await message.reply(
        "✅ Рост сохранён!\n\n"
        "🔢 **Шаг 3/6**: Сколько тебе лет?\n"
        "Пример: `25`")
    await state.set_state(ProfileSetup.age)


@router.message(ProfileSetup.age)
async def process_age(message: Message, state: FSMContext):
    """Обрабатывает ввод возраста (третий шаг FSM)."""
    try:
        age = int(message.text.strip())

        if age < 10 or age > 120:
            await message.reply(
                "❌ Возраст должен быть от 10 до 120 лет.\n\n"
                "Попробуй снова:"
            )
            return

    except ValueError:
        await message.reply(
            "❌ Пожалуйста, введи целое число.\n\n"
            "Пример: `25`")
        return

    await state.update_data(age=age)

    await message.reply(
        "✅ Возраст сохранён!\n\n"
        "🔢 **Шаг 4/6**: Сколько минут в день ты занимаешься спортом?\n"
        "Пример: `30` (можно `0` если не занимаешься)")
    await state.set_state(ProfileSetup.activity)


@router.message(ProfileSetup.activity)
async def process_activity(message: Message, state: FSMContext):
    """Обрабатывает ввод активности (четвёртый шаг FSM)."""
    try:
        activity = int(message.text.strip())

        if activity < 0 or activity > 300:
            await message.reply(
                "❌ Активность должна быть от 0 до 300 минут.\n\n"
                "Попробуй снова:"
            )
            return

    except ValueError:
        await message.reply(
            "❌ Пожалуйста, введи целое число.\n\n"
            "Пример: `30`")
        return

    await state.update_data(activity_minutes=activity)

    await message.reply(
        "✅ Активность сохранена!\n\n"
        "🔢 **Шаг 5/6**: В каком городе ты находишься?\n"
        "Нужно для учёта погоды при расчёте нормы воды.\n\n"
        "Пример: `Moscow` или `Санкт-Петербург`")
    await state.set_state(ProfileSetup.city)


@router.message(ProfileSetup.city)
async def process_city(message: Message, state: FSMContext):
    """Обрабатывает ввод города (пятый шаг FSM)."""
    city = message.text.strip()

    if len(city) < 2:
        await message.reply(
            "❌ Название города слишком короткое.\n\n"
            "Попробуй снова:"
        )
        return

    await state.update_data(city=city)

    await message.reply(
        "✅ Город сохранён!\n\n"
        "🔢 **Шаг 6/6**: Хочешь задать свою дневную цель по калориям?\n\n"
        "Введи число (например, `2000`) или напиши `нет` для автоматического расчёта.")
    await state.set_state(ProfileSetup.manual_calories)


@router.message(ProfileSetup.manual_calories)
async def finalize_profile(message: Message, state: FSMContext):
    """
    Финальный handler: собирает все данные, рассчитывает цели и сохраняет профиль.

    Паттерн: Integration Point
    - Собираем все данные из FSM через state.get_data()
    - Интегрируем внешние API (weather_api)
    - Используем сервисы для расчётов (HealthCalculator)
    - Сохраняем в storage
    - Очищаем FSM состояние
    - Отправляем подтверждение

    Это критический паттерн для AI-ботов:
    Финальный handler — место интеграции всех слоёв приложения.
    """
    user_id = message.from_user.id

    # Шаг 1: Парсинг manual_calories
    manual_goal = None
    user_input = message.text.strip().lower()

    # Если пользователь ввёл не "нет"/"no"/"skip" — пробуем парсить число
    if user_input not in ["нет", "no", "skip", "н"]:
        try:
            manual_goal = int(user_input)
            if manual_goal < 1000 or manual_goal > 5000:
                await message.reply(
                    "❌ Цель калорий должна быть от 1000 до 5000 ккал.\n"
                    "Использую автоматический расчёт."
                )
                manual_goal = None
        except ValueError:
            # Не число — используем автоматический расчёт
            pass

    # Шаг 2: Получаем все собранные данные из FSM
    data = await state.get_data()

    # Шаг 3: Получаем температуру через Weather API
    await message.reply("⏳ Получаю данные о погоде...")
    temperature = await weather_api.get_temperature(data["city"])

    # Шаг 4: Рассчитываем норму воды
    water_goal = HealthCalculator.calculate_water_goal(
        weight_kg=data["weight_kg"],
        activity_minutes=data["activity_minutes"],
        temperature_celsius=temperature
    )

    # Шаг 5: Рассчитываем норму калорий
    calorie_goal = HealthCalculator.calculate_calorie_goal(
        weight_kg=data["weight_kg"],
        height_cm=data["height_cm"],
        age=data["age"],
        activity_minutes=data["activity_minutes"],
        manual_goal=manual_goal
    )

    # Шаг 6: Создаём объект UserProfile
    profile = UserProfile(
        user_id=user_id,
        weight_kg=data["weight_kg"],
        height_cm=data["height_cm"],
        age=data["age"],
        activity_minutes_per_day=data["activity_minutes"],
        city=data["city"],
        manual_calorie_goal=manual_goal,
        water_goal_ml=water_goal,
        calorie_goal=calorie_goal
    )

    # Шаг 7: Сохраняем профиль в storage
    await storage.save_profile(user_id, profile)

    # Шаг 8: ВАЖНО! Очищаем FSM состояние
    await state.clear()

    # Шаг 9: Отправляем красивое подтверждение с целями
    temp_info = f" (сейчас {temperature:.1f}°C)" if temperature else ""
    goal_type = "ручная" if manual_goal else "рассчитанная"

    await message.reply(
        f"✅ Профиль успешно создан!\n\n"
        f"📊 Твои параметры:\n"
        f"├ Вес: {data['weight_kg']} кг\n"
        f"├ Рост: {data['height_cm']} см\n"
        f"├ Возраст: {data['age']} лет\n"
        f"├ Активность: {data['activity_minutes']} мин/день\n"
        f"└ Город: {data['city']}{temp_info}\n\n"
        f"🎯 Дневные цели:\n"
        f"├ 💧 Вода: {water_goal} мл\n"
        f"└ 🍽 Калории: {calorie_goal} ккал ({goal_type})\n\n"
        f"📝 Начни логирование:\n"
        f"• /log_water - добавить воду\n"
        f"• /log_food - добавить еду\n"
        f"• /log_workout - тренировка\n"
        f"• /check_progress - прогресс\n\n"
        f"💡 Чтобы изменить профиль, просто запусти /set_profile снова"
    )


# ============================================================================
# ПАТТЕРН: FSM State Isolation
# ============================================================================
#
# Каждый handler "слушает" ТОЛЬКО своё состояние:
# - @router.message(ProfileSetup.weight) срабатывает ТОЛЬКО когда state = ProfileSetup.weight
# - Другие сообщения пользователя игнорируются этим handler
#
# Преимущества:
# 1. Нет конфликтов между handlers
# 2. Можно запустить несколько FSM параллельно (профиль + логирование еды)
# 3. Легко добавить новые шаги (вставил handler между weight и height)
#
# Для AI-ботов это критично: часто нужны сложные диалоги с ветвлениями.
# ============================================================================
