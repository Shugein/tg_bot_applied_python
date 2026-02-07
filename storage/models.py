from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class UserProfile:
    """
    Профиль пользователя с физическими параметрами и целями.

    Паттерн: Dataclass вместо обычного класса
    - Автоматически генерирует __init__, __repr__, __eq__
    - Type hints для IDE autocomplete
    - Легко сериализуется в JSON через dataclasses.asdict()
    """
    user_id: int
    weight_kg: float
    height_cm: float
    age: int
    activity_minutes_per_day: int
    city: str

    # Опциональные поля
    manual_calorie_goal: Optional[int] = None

    # Рассчитанные цели (кешируются после расчёта)
    water_goal_ml: int = 0
    calorie_goal: int = 0

    # Метаданные
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class DailyTracking:
    """
    Ежедневные счётчики воды и калорий.

    Паттерн: Lazy Reset
    - Не нужен background task для сброса в полночь
    - При каждом get_user() проверяется дата
    - Если новый день — счётчики автоматически обнуляются
    """
    date: str  # "YYYY-MM-DD"
    water_ml: int = 0
    calories: int = 0
    burned_calories: int = 0

    def reset_if_new_day(self) -> bool:
        """
        Проверяет, наступил ли новый день.
        Если да — сбрасывает все счётчики и возвращает True.

        Returns:
            True если произошёл reset, False если день тот же
        """
        today = datetime.now().strftime("%Y-%m-%d")
        if self.date != today:
            self.date = today
            self.water_ml = 0
            self.calories = 0
            self.burned_calories = 0
            return True
        return False


@dataclass
class UserData:
    """
    Полные данные пользователя: профиль + ежедневный трекинг.

    Паттерн: Aggregate Root (DDD)
    - UserData — единая точка входа для работы с данными пользователя
    - Вся логика доступа инкапсулирована в UserStorage
    """
    profile: UserProfile
    daily: DailyTracking
