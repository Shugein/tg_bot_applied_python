from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from storage.user_storage import UserStorage
from states import FoodLogging
from services.food_api import FoodAPIClient
from services.llm_calories import LLMCalorieEstimator
from settings import settings

router = Router()
storage = UserStorage()
food_api = FoodAPIClient()
llm_estimator = LLMCalorieEstimator(settings.LLM_API_KEY)


@router.message(Command("log_food"))
async def start_food_logging(message: Message, state: FSMContext):
    """
    Запускает процесс логирования еды.

    Паттерн: Optional Command Argument
    - /log_food → FSM диалог
    - /log_food банан → сразу поиск
    """
    user_id = message.from_user.id

    if not await storage.get_user(user_id):
        await message.reply(
            "❌ Профиль не найден.\n\n"
            "Сначала настрой профиль: /set_profile"
        )
        return

    # Проверяем аргумент команды
    parts = message.text.split(maxsplit=1)
    if len(parts) > 1:
        # Есть аргумент — сразу ищем
        food_name = parts[1]
        await state.update_data(food_name=food_name)
        await search_and_display(message, state)
    else:
        # Нет аргумента — запрашиваем
        await message.reply(
            "🍽 **Логирование еды**\n\n"
            "Что ты съел? Напиши название продукта.\n"
            "Пример: `молоко`, `банан`, `пицца`")
        await state.set_state(FoodLogging.food_name)


@router.message(FoodLogging.food_name)
async def receive_food_name(message: Message, state: FSMContext):
    """Получаем название продукта и запускаем поиск."""
    food_name = message.text.strip()
    await state.update_data(food_name=food_name)
    await search_and_display(message, state)


async def search_and_display(message: Message, state: FSMContext):
    """
    Ищет продукт в OpenFoodFacts и показывает результаты.

    Паттерн: Cascading Fallback Strategy
    1. Поиск в OpenFoodFacts (бесплатно, быстро)
    2. Если 0 результатов → LLM estimation (платно, точнее)
    3. Если 1 результат → автовыбор
    4. Если 2+ → пользователь выбирает из списка
    """
    data = await state.get_data()
    query = data["food_name"]

    await message.reply(f"🔍 Ищу '{query}' в базе продуктов...")

    # Шаг 1: Поиск в OpenFoodFacts
    products = await food_api.search_products(query, limit=5)

    if not products:
        # Шаг 2: LLM Fallback
        await message.reply(
            "❌ Продукт не найден в базе.\n"
            "🤖 Использую AI для оценки калорийности..."
        )
        await llm_fallback(message, state)
        return

    if len(products) == 1:
        # Один результат — автовыбор
        await state.update_data(selected_product=products[0])
        await ask_portion_size(message, state, from_api=True)
        return

    # Несколько результатов — inline keyboard
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{p['product_name']} ({p['calories_per_100g']} ккал/100г)",
                callback_data=f"food_{i}"
            )]
            for i, p in enumerate(products[:5])  # Максимум 5 кнопок
        ] + [[InlineKeyboardButton(
            text="❌ Ничего не подходит → использовать AI",
            callback_data="food_llm"
        )]]
    )

    await state.update_data(search_results=products)
    await message.reply(
        "📋 Найдено несколько вариантов. Выбери подходящий:",
        reply_markup=keyboard
    )
    await state.set_state(FoodLogging.select_product)


@router.callback_query(FoodLogging.select_product)
async def handle_product_selection(callback: CallbackQuery, state: FSMContext):
    """Обрабатывает выбор продукта из списка."""
    data = await state.get_data()

    if callback.data == "food_llm":
        # Пользователь выбрал LLM fallback
        await callback.message.answer("🤖 Использую AI для оценки...")
        await llm_fallback(callback.message, state)
        await callback.answer()
        return

    # Выбран продукт из списка
    index = int(callback.data.split("_")[1])
    products = data["search_results"]
    selected = products[index]

    await state.update_data(selected_product=selected)
    await callback.message.answer(f"✅ Выбрано: {selected['product_name']}")
    await ask_portion_size(callback.message, state, from_api=True)
    await callback.answer()


async def llm_fallback(message: Message, state: FSMContext):
    """
    LLM оценка калорийности (когда OpenFoodFacts не нашёл).

    Паттерн: AI Fallback with Confirmation
    - Показываем LLM оценку с объяснением
    - Просим пользователя подтвердить
    - Сохраняем только после подтверждения
    """
    data = await state.get_data()
    food_name = data["food_name"]

    try:
        # Вызываем LLM для оценки
        estimate = await llm_estimator.estimate_calories(food_name)

        # Эмодзи для confidence level
        confidence_emoji = {
            "high": "✅",
            "medium": "⚠️",
            "low": "❓"
        }
        emoji = confidence_emoji.get(estimate.confidence, "❓")

        # Сохраняем LLM оценку в state
        await state.update_data(
            llm_estimate=estimate.model_dump(),
            use_llm=True
        )

        await message.reply(
            f"🤖 **AI Оценка калорийности**\n\n"
            f"**Продукт**: {food_name}\n"
            f"**Калории**: {estimate.calories} ккал\n"
            f"**Порция**: ~{estimate.portion_grams}г\n"
            f"**Уверенность**: {emoji} {estimate.confidence}\n\n"
            f"💡 **Объяснение**:\n{estimate.explanation}\n\n"
            f"Хочешь использовать эту оценку? (да/нет)")
        await state.set_state(FoodLogging.llm_confirmation)

    except Exception as e:
        await message.reply(
            f"❌ Ошибка AI оценки: {e}\n\n"
            "Попробуй ввести название продукта точнее."
        )
        await state.clear()


@router.message(FoodLogging.llm_confirmation)
async def handle_llm_confirmation(message: Message, state: FSMContext):
    """Обрабатывает подтверждение LLM оценки."""
    response = message.text.strip().lower()

    if response in ["да", "yes", "y", "д", "ок", "ok"]:
        data = await state.get_data()
        estimate = data["llm_estimate"]

        # Используем LLM оценку как есть
        user_id = message.from_user.id
        await storage.update_daily(user_id, calories=estimate["calories"])

        await message.reply(
            f"✅ Добавлено: {estimate['calories']} ккал\n\n"
            f"Проверь прогресс: /check_progress")
        await state.clear()
    else:
        await message.reply(
            "❌ Отменено. Попробуй /log_food снова с более точным названием."
        )
        await state.clear()


async def ask_portion_size(message: Message, state: FSMContext, from_api: bool):
    """Запрашивает размер порции."""
    data = await state.get_data()

    if from_api:
        product = data["selected_product"]
        await message.reply(
            f"📏 Сколько грамм **{product['product_name']}** ты съел?\n\n"
            f"Калорийность: {product['calories_per_100g']} ккал на 100г\n\n"
            f"Введи число (например, `150`):")
    else:
        await message.reply(
            "📏 Сколько грамм? Введи число:"
        )

    await state.set_state(FoodLogging.portion_size)


@router.message(FoodLogging.portion_size)
async def finalize_food_log(message: Message, state: FSMContext):
    """
    Финализирует логирование еды.

    Паттерн: Integration Point
    - Рассчитываем калории: (ккал/100г) * (граммы/100)
    - Сохраняем в storage
    - Показываем прогресс
    """
    user_id = message.from_user.id
    data = await state.get_data()

    try:
        grams = float(message.text.strip())

        if grams <= 0 or grams > 5000:
            await message.reply("❌ Граммы должны быть от 1 до 5000.")
            return

    except ValueError:
        await message.reply("❌ Введи число (например, 150).")
        return

    product = data["selected_product"]
    calories_per_100g = product["calories_per_100g"]
    total_calories = int((calories_per_100g / 100) * grams)

    # Логируем калории
    await storage.update_daily(user_id, calories=total_calories)

    # Получаем прогресс
    user_data = await storage.get_user(user_id)
    total = user_data.daily.calories
    goal = user_data.profile.calorie_goal
    percentage = (total / goal * 100) if goal > 0 else 0

    await message.reply(
        f"✅ **Добавлено**:\n"
        f"{grams}г {product['product_name']} = {total_calories} ккал\n\n"
        f"📊 **Сегодня**: {total}/{goal} ккал ({percentage:.1f}%)\n\n"
        f"Проверь прогресс: /check_progress")
    await state.clear()


# ============================================================================
# ПАТТЕРН: Cascading Fallback для AI-ботов
# ============================================================================
#
# OpenFoodFacts → LLM → User Confirmation
#
# **Почему этот паттерн важен:**
#
# 1. **Cost Optimization**
#    - OpenFoodFacts бесплатный, используем первым
#    - LLM платный ($0.003 за запрос), только fallback
#    - Экономим ~70% запросов к LLM
#
# 2. **Accuracy vs Speed**
#    - API быстрее (200ms), точнее для известных продуктов
#    - LLM медленнее (2-5s), но работает для любых описаний
#
# 3. **User Trust**
#    - Показываем источник данных (база vs AI)
#    - Confidence level для LLM оценок
#    - Подтверждение перед сохранением AI оценки
#
# **Применение в других AI-ботах:**
#
# - Image recognition: Vision API → Multimodal LLM fallback
# - Translation: Google Translate → GPT-4 для идиом
# - Product search: Elasticsearch → LLM semantic search
#
# Этот pattern = Production-ready AI applications.
# ============================================================================
