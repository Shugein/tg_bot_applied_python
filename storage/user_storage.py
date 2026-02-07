import json
import asyncio
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from dataclasses import asdict

from .models import UserProfile, DailyTracking, UserData


class UserStorage:
    """
    Хранилище данных пользователей с JSON persistence.

    Паттерн: Repository Pattern
    - Скрывает детали хранения (JSON, БД, etc.)
    - Предоставляет простой интерфейс для handlers
    - Можно заменить на SQLite, не меняя handlers

    Паттерн: Hybrid Storage (In-Memory + Persistence)
    - Данные в памяти для быстрого доступа (Dict)
    - Автосохранение в JSON после каждого изменения
    - Загрузка при старте бота

    Это идеально для AI-ботов где:
    - Профили редко меняются (1 раз при настройке)
    - Нужен быстрый доступ при каждом сообщении
    - Простота важнее масштабирования
    """

    def __init__(self, persistence_file: str = "user_data.json"):
        """
        Инициализация хранилища.

        Args:
            persistence_file: Путь к JSON файлу для сохранения данных
        """
        self._data: Dict[int, UserData] = {}
        self._file = Path(persistence_file)
        self._lock = asyncio.Lock()  # Thread-safe для async операций
        self._load_from_disk()

    def _load_from_disk(self):
        """
        Загружает данные из JSON файла при старте бота.
        Если файла нет — создаёт пустое хранилище.
        """
        if not self._file.exists():
            print(f"Файл {self._file} не найден. Создаю новое хранилище.")
            return

        try:
            with open(self._file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Десериализация JSON → dataclasses
            for user_id_str, user_dict in data.items():
                user_id = int(user_id_str)
                profile = UserProfile(**user_dict['profile'])
                daily = DailyTracking(**user_dict['daily'])
                self._data[user_id] = UserData(profile=profile, daily=daily)

            print(f"Загружено {len(self._data)} пользователей из {self._file}")
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")
            # Не падаем, просто начинаем с пустого хранилища

    async def _persist(self):
        """
        Сохраняет данные в JSON файл.

        Паттерн: Async Lock
        - Несколько handlers могут одновременно писать данные
        - Lock гарантирует, что запись в файл атомарная
        """
        async with self._lock:
            try:
                # Сериализация dataclasses → dict → JSON
                data = {}
                for user_id, user_data in self._data.items():
                    data[str(user_id)] = {
                        'profile': asdict(user_data.profile),
                        'daily': asdict(user_data.daily)
                    }

                with open(self._file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Ошибка сохранения данных: {e}")

    async def get_user(self, user_id: int) -> Optional[UserData]:
        """
        Получает данные пользователя.

        Паттерн: Lazy Reset
        - Автоматически сбрасывает daily счётчики если новый день
        - Не нужны cron jobs или background tasks

        Args:
            user_id: Telegram user ID

        Returns:
            UserData или None если пользователь не зарегистрирован
        """
        user_data = self._data.get(user_id)
        if not user_data:
            return None

        # Автоматический reset если новый день
        if user_data.daily.reset_if_new_day():
            await self._persist()  # Сохраняем reset
            print(f"Daily reset для пользователя {user_id}")

        return user_data

    async def save_profile(self, user_id: int, profile: UserProfile):
        """
        Создаёт или обновляет профиль пользователя.

        Если это новый пользователь — создаёт DailyTracking.
        Если существующий — обновляет только профиль.

        Args:
            user_id: Telegram user ID
            profile: UserProfile с заполненными данными
        """
        if user_id in self._data:
            # Обновляем профиль, daily трекинг оставляем
            self._data[user_id].profile = profile
        else:
            # Новый пользователь — создаём с чистым daily tracking
            today = datetime.now().strftime("%Y-%m-%d")
            self._data[user_id] = UserData(
                profile=profile,
                daily=DailyTracking(date=today)
            )

        await self._persist()

    async def update_daily(
        self,
        user_id: int,
        water_ml: int = 0,
        calories: int = 0,
        burned_calories: int = 0
    ):
        """
        Инкрементально обновляет ежедневный трекинг.

        Паттерн: Incremental Updates
        - Не заменяем значения, а добавляем к существующим
        - /log_water 250 → daily.water_ml += 250

        Args:
            user_id: Telegram user ID
            water_ml: Сколько мл воды добавить
            calories: Сколько калорий добавить
            burned_calories: Сколько калорий сожжено

        Raises:
            ValueError: Если пользователь не зарегистрирован
        """
        user_data = await self.get_user(user_id)
        if not user_data:
            raise ValueError(
                f"Пользователь {user_id} не найден. "
                "Сначала выполните /set_profile"
            )

        # Инкрементальное обновление
        user_data.daily.water_ml += water_ml
        user_data.daily.calories += calories
        user_data.daily.burned_calories += burned_calories

        await self._persist()

    def has_profile(self, user_id: int) -> bool:
        """
        Проверяет, есть ли у пользователя профиль.

        Используется в handlers для быстрой проверки:
        if not storage.has_profile(user_id):
            await message.reply("Сначала /set_profile")
            return
        """
        return user_id in self._data
