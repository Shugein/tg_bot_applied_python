"""
Единый экземпляр UserStorage для всего приложения.

Паттерн: Singleton через module-level variable
- Python модули загружаются один раз
- Все импорты получают один и тот же объект
- Решает проблему множественных экземпляров storage

Использование в handlers:
    from storage.instance import storage
    user_data = await storage.get_user(user_id)
"""

from .user_storage import UserStorage

# Единственный экземпляр storage для всего приложения
storage = UserStorage()
