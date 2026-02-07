import asyncio
from aiogram import Bot, Dispatcher
from settings import settings
from handlers import setup_handlers
from middlewares import LoggingMiddleware

# Создаем экземпляры бота и диспетчера
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# Настраиваем middleware и обработчики
dp.message.middleware(LoggingMiddleware())
setup_handlers(dp)

async def main():
    print("🤖 Health Tracking Bot запущен!")
    print(f"📊 Модульная архитектура: handlers/ services/ storage/")
    print(f"💾 Данные сохраняются в: {settings.USER_DATA_FILE}")
    print(f"\n✨ Доступные команды:")
    print("   /set_profile - Настроить профиль")
    print("   /log_water <мл> - Добавить воду")
    print("   /log_workout <тип> <минуты> - Добавить тренировку")
    print("   /check_progress - Посмотреть прогресс")
    print(f"\n⏳ Ожидаю сообщений...\n")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())