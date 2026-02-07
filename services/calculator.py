from typing import Optional


class HealthCalculator:
    """
    Калькулятор норм воды, калорий и тренировок.

    Паттерн: Service Layer (чистая бизнес-логика)
    - Нет зависимостей от Telegram, API, хранилища
    - Только статические методы с формулами
    - Легко unit-тестировать: calc.calculate_water_goal(70, 30, 25) → 2850
    """

    WORKOUT_MET_VALUES = {
        "running": 9.8,      # Бег 8 км/ч
        "jogging": 7.0,      # Лёгкая пробежка
        "walking": 3.5,      # Ходьба 5 км/ч
        "cycling": 7.5,      # Велосипед средний темп
        "swimming": 8.0,     # Плавание кроль
        "gym": 5.0,          # Силовая тренировка
        "yoga": 2.5,         # Йога/растяжка
        "hiit": 8.0,         # Высокоинтенсивный интервальный тренинг
    }

    @staticmethod
    def calculate_water_goal(
        weight_kg: float,
        activity_minutes: int,
        temperature_celsius: Optional[float] = None
    ) -> int:
        """
        Рассчитывает дневную норму воды.

        Формула:
        - Базовая норма: weight × 30 мл/кг
        - Активность: +500 мл за каждые 30 минут
        - Жаркая погода (>25°C): +750 мл (среднее от 500-1000)

        Args:
            weight_kg: Вес в килограммах
            activity_minutes: Минут активности в день
            temperature_celsius: Температура в городе (опционально)

        Returns:
            Норма воды в миллилитрах

        Example:
            >>> HealthCalculator.calculate_water_goal(70, 60, 30)
            3850  # 70*30 + (60/30)*500 + 750
        """
        # Базовая норма (30 мл на кг)
        base_water = weight_kg * 30

        # Бонус за активность (500 мл за каждые 30 минут)
        activity_bonus = (activity_minutes / 30) * 500

        # Бонус за жаркую погоду
        temperature_bonus = 0
        if temperature_celsius and temperature_celsius > 25:
            temperature_bonus = 750  # Среднее от 500-1000 мл

        total = base_water + activity_bonus + temperature_bonus
        return int(total)

    @staticmethod
    def calculate_calorie_goal(
        weight_kg: float,
        height_cm: float,
        age: int,
        activity_minutes: int,
        manual_goal: Optional[int] = None
    ) -> int:
        """
        Рассчитывает дневную норму калорий.

        Формула:
        - Базовый обмен: 10 × вес + 6.25 × рост - 5 × возраст
        - Активность: +200-400 ккал в зависимости от уровня

        Примечание: Формула не учитывает пол для простоты.

        Args:
            weight_kg: Вес в кг
            height_cm: Рост в см
            age: Возраст в годах
            activity_minutes: Минут активности в день
            manual_goal: Ручная цель (если задана, используется вместо расчёта)

        Returns:
            Норма калорий в ккал
        """
        # Если пользователь задал ручную цель — используем её
        if manual_goal:
            return manual_goal

        # Базовый обмен веществ (BMR)
        base_calories = 10 * weight_kg + 6.25 * height_cm - 5 * age

        # Активность: градация по времени
        if activity_minutes < 30:
            activity_bonus = 200      # Низкая активность
        elif activity_minutes < 60:
            activity_bonus = 300      # Средняя активность
        else:
            activity_bonus = 400      # Высокая активность

        return int(base_calories + activity_bonus)

    @staticmethod
    def calculate_workout_calories(
        workout_type: str,
        duration_minutes: int,
        weight_kg: float
    ) -> int:
        """
        Рассчитывает сожжённые калории на тренировке.

        Используется формула: Calories = MET × вес(кг) × время(часы)

        MET (Metabolic Equivalent) — универсальная мера интенсивности.
        1 MET = энергия в покое. 8 MET = в 8 раз больше энергии.

        Args:
            workout_type: Тип тренировки (running, cycling, etc.)
            duration_minutes: Длительность в минутах
            weight_kg: Вес пользователя в кг

        Returns:
            Сожжённые калории

        Example:
            >>> HealthCalculator.calculate_workout_calories("running", 30, 70)
            343  # 9.8 MET × 70 kg × 0.5 hours
        """
        # Получаем MET value для типа тренировки
        met = HealthCalculator.WORKOUT_MET_VALUES.get(
            workout_type.lower(),
            5.0  # Default для неизвестных типов (средняя интенсивность)
        )

        hours = duration_minutes / 60
        calories = met * weight_kg * hours

        return int(calories)

    @staticmethod
    def calculate_workout_water_bonus(duration_minutes: int) -> int:
        """
        Рассчитывает дополнительную потребность в воде от тренировки.

        Формула: +200 мл за каждые 30 минут тренировки

        Args:
            duration_minutes: Длительность тренировки в минутах

        Returns:
            Дополнительные миллилитры воды

        Example:
            >>> HealthCalculator.calculate_workout_water_bonus(45)
            300  # (45 / 30) * 200 = 300 мл
        """
        return int((duration_minutes / 30) * 200)

    @staticmethod
    def get_supported_workouts() -> list[str]:
        """
        Возвращает список поддерживаемых типов тренировок.

        Используется в handlers для подсказок пользователю.
        """
        return list(HealthCalculator.WORKOUT_MET_VALUES.keys())
