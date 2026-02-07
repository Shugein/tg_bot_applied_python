from aiogram.fsm.state import State, StatesGroup

# FSM для настройки профиля пользователя
class ProfileSetup(StatesGroup):
    """
    Многошаговый диалог для сбора профиля пользователя.

    Паттерн: Linear FSM Flow
    - weight → height → age → activity → city → manual_calories
    - Каждый handler валидирует ввод перед переходом
    - При ошибке остаёмся в том же состоянии (return без set_state)

    Это стандартный паттерн для onboarding в AI-ботах:
    собираем данные последовательно, без возможности пропустить шаг.
    """
    weight = State()             # Ожидаем вес в кг
    height = State()             # Ожидаем рост в см
    age = State()                # Ожидаем возраст
    activity = State()           # Ожидаем минуты активности/день
    city = State()               # Ожидаем город (для погоды)
    manual_calories = State()    # Опционально: ручная цель калорий


# FSM для логирования еды
class FoodLogging(StatesGroup):
    """
    Диалог для добавления еды с поддержкой API и LLM fallback.

    Паттерн: Branching FSM Flow
    - food_name → поиск в API
      - Найдено 0 продуктов → LLM estimation → confirmation
      - Найден 1 продукт → auto-select → portion_size
      - Найдено 2+ → select_product → portion_size

    Этот паттерн критичен для AI-ботов с внешними API:
    нужны fallback стратегии когда API не находит данные.
    """
    food_name = State()          # Ожидаем название продукта
    select_product = State()     # Выбор из нескольких результатов API
    portion_size = State()       # Ожидаем размер порции в граммах
    llm_confirmation = State()   # Подтверждение LLM оценки (если API не нашёл)