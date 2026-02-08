# Health Tracking Bot

Telegram-бот для отслеживания здоровья и фитнеса.
(для написания этого бота я вайбкодил, чтобы получить готовый шаблон для работы с данными и ускорить процесс)
(вайбкодил я аккуратно, в режиме обучения, чтобы все усвоить и понять архитектурные патерны)

## Скрины

<img width="816" height="865" alt="image" src="https://github.com/user-attachments/assets/9eb2e1f3-621a-4527-96f6-af0bf2ba38c4" />


<img width="795" height="720" alt="image" src="https://github.com/user-attachments/assets/566b59d4-2b83-4bed-bc5e-55773d7ce78f" />


<img width="787" height="151" alt="image" src="https://github.com/user-attachments/assets/7ec89b78-301b-4544-affb-5add749faab0" />


## Возможности

- **Профиль пользователя**: настройка параметров (вес, рост, возраст, активность, город)
- **Трекинг воды**: логирование потребления воды с автоматическим расчётом дневной нормы
- **Трекинг питания**: подсчёт калорий через FoodData Central API и LLM
- **Трекинг тренировок**: учёт физической активности и расчёт сожжённых калорий
- **Прогресс**: визуализация достижения дневных целей

## Технологии

- **aiogram 3** - асинхронный фреймворк для Telegram Bot API
- **FSM** - многошаговые диалоги для настройки профиля
- **OpenWeatherMap API** - учёт температуры для расчёта нормы воды
- **FoodData Central API** - база данных продуктов
- **LLM API** - распознавание еды из фото и текста
- **Docker** - контейнеризация

## Запуск

```bash
# Создать .env файл
BOT_TOKEN=your_token
OPENWEATHER_API_KEY=your_key
LLM_API_KEY=your_key

# Запустить в Docker
docker compose up -d
```

## Команды

- `/start` - начало работы
- `/set_profile` - настройка профиля
- `/log_water <мл>` - добавить воду
- `/log_food` - добавить еду
- `/log_workout <тип> <минуты>` - добавить тренировку
- `/check_progress` - посмотреть прогресс
