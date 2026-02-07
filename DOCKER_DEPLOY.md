# Docker Deployment Guide

## Локальный запуск с Docker

### 1. Настройка переменных окружения

Скопируй `.env.example` в `.env` и заполни значения:

```bash
cp .env.example .env
nano .env  # или любой другой редактор
```

### 2. Запуск с Docker Compose

```bash
# Собрать и запустить бот
docker-compose up -d

# Посмотреть логи
docker-compose logs -f bot

# Остановить бот
docker-compose down
```

### 3. Запуск с Docker (без compose)

```bash
# Собрать image
docker build -t health-tracker-bot .

# Запустить контейнер
docker run -d \
  --name health_bot \
  --env-file .env \
  -v $(pwd)/user_data.json:/app/user_data.json \
  --restart unless-stopped \
  health-tracker-bot

# Посмотреть логи
docker logs -f health_bot

# Остановить контейнер
docker stop health_bot
docker rm health_bot
```

## Деплой на Render.com

### Вариант 1: Web Service (рекомендуется)

1. Зарегистрируйся на [Render.com](https://render.com)
2. Создай новый **Web Service**
3. Подключи GitHub репозиторий
4. Настройки:
   - **Environment**: Docker
   - **Dockerfile Path**: `./Dockerfile`
   - **Environment Variables**: добавь все переменные из `.env`
5. Добавь **Disk** для persistence:
   - **Mount Path**: `/app`
   - Это сохранит `user_data.json` между перезапусками

### Вариант 2: Railway

1. Зарегистрируйся на [Railway.app](https://railway.app)
2. Нажми **New Project** → **Deploy from GitHub repo**
3. Выбери репозиторий
4. Railway автоматически обнаружит Dockerfile
5. Добавь environment variables через Settings → Variables
6. Добавь Volume для `/app/user_data.json`

## Полезные команды

```bash
# Пересобрать после изменений в коде
docker-compose up -d --build

# Посмотреть размер image
docker images health-tracker-bot

# Посмотреть запущенные контейнеры
docker ps

# Зайти внутрь контейнера
docker exec -it health_bot bash

# Очистить неиспользуемые images
docker system prune -a
```

## Проверка работоспособности

После запуска проверь в Telegram:
- `/start` - приветствие
- `/set_profile` - настройка профиля
- `/log_water 250` - логирование воды
- `/check_progress` - просмотр прогресса

## Troubleshooting

**Проблема**: Бот не запускается
- Проверь логи: `docker-compose logs bot`
- Убедись что `.env` содержит корректный `BOT_TOKEN`

**Проблема**: Данные теряются после перезапуска
- Проверь что volume настроен: `docker-compose config`
- Убедись что `user_data.json` существует локально

**Проблема**: LLM не работает
- Проверь `LLM_API_KEY` в `.env`
- Проверь модель в `services/llm_calories.py`
