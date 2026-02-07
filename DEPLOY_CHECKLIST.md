# Чеклист для деплоя

## Перед деплоем на Render.com

### 1. Проверка файлов
- [x] Dockerfile создан
- [x] .dockerignore создан
- [x] docker-compose.yml создан
- [x] .env.example создан
- [x] requirements.txt содержит все зависимости
- [x] Все handler файлы на месте (handlers/)
- [x] Все service файлы на месте (services/)
- [x] Storage модули на месте (storage/)

### 2. Проверка .env
- [ ] BOT_TOKEN заполнен (получить у @BotFather)
- [ ] OPENWEATHER_API_KEY заполнен (https://openweathermap.org/api)
- [ ] LLM_API_KEY заполнен (https://openrouter.ai/)

### 3. Git репозиторий
```bash
# Закоммить все изменения
git add .
git commit -m "Add Docker deployment configuration"
git push origin main
```

### 4. Деплой на Render.com

1. **Создай Web Service**:
   - Зайди на https://render.com
   - New → Web Service
   - Connect GitHub репозиторий

2. **Настройки**:
   - Name: `health-tracker-bot`
   - Environment: `Docker`
   - Instance Type: `Free`

3. **Environment Variables** (добавь в Render.com):
   ```
   BOT_TOKEN=<твой токен>
   OPENWEATHER_API_KEY=<твой ключ>
   LLM_API_KEY=<твой ключ>
   BOT_URL=https://t.me/prevelinoe_petanie_4all_hse_bot
   USER_DATA_FILE=user_data.json
   ```

4. **Disk для persistence** (ВАЖНО!):
   - Settings → Disks → Add Disk
   - Name: `data`
   - Mount Path: `/app`
   - Size: `1 GB`

5. **Deploy**:
   - Нажми "Create Web Service"
   - Дождись завершения build (3-5 минут)
   - Проверь логи: должна появиться строка "Бот запущен!"

### 5. Проверка работы

После успешного деплоя протестируй в Telegram:
```
/start          → Приветствие
/set_profile    → Настройка профиля (6 шагов)
/log_water 250  → Логирование воды
/log_food       → Поиск еды в OpenFoodFacts
/log_workout running 30  → Тренировка
/check_progress → Прогресс за день
```

### 6. Скриншоты для сдачи

Сделай скриншоты для отчета:
- [ ] Build logs с Render.com (показывающие успешный deploy)
- [ ] Application logs с Render.com (логи работы бота)
- [ ] Примеры команд в Telegram
- [ ] /check_progress с данными

### 7. Баллы за задание

Проверка выполнения:
- [x] Базовый бот работает (2 балла)
- [x] Профиль сохраняется (1 балл)
- [x] Расчёт воды/калорий (0.3 балла)
- [x] API интеграция (0.2 балла)
- [x] Логирование воды (1.5 балла)
- [x] Логирование еды (1.5 балла)
- [x] Логирование тренировок (1.5 балла)
- [x] Прогресс (1 балл)
- [ ] Деплой (1 балл) ← осталось сделать
- [x] БОНУС: LLM калории (+2 балла)

**Итого**: 10/10 базовых + 2 бонусных = **12 баллов**

## Troubleshooting

**Build failed на Render.com**:
- Проверь requirements.txt (все ли зависимости указаны?)
- Проверь логи build в Render.com Dashboard
- Убедись что Dockerfile syntax корректен

**Бот не запускается**:
- Проверь Application Logs в Render.com
- Убедись что BOT_TOKEN корректный
- Проверь что все Environment Variables добавлены

**Данные теряются после рестарта**:
- Убедись что Disk настроен и примонтирован к `/app`
- Проверь что USER_DATA_FILE=user_data.json в env vars

**LLM не работает**:
- Проверь LLM_API_KEY
- Проверь баланс на OpenRouter
- Проверь модель в services/llm_calories.py
