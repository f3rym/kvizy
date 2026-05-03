# Фаза 2: Базовый бот (упрощенная)

**Длительность:** 2-3 недели  
**Цель:** Простой работающий бот с базовой аутентификацией

## Упрощенный подход

Минимальный функционал:
- Регистрация пользователей
- Простые роли (admin/user)
- Базовые команды
- Без сложных middleware
- Без 2FA (можно добавить позже)

## Задачи

### 2.1 Базовый бот (2-3 дня)

#### src/bot/main.py
```python
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from src.core.config import settings

async def main():
    bot = Bot(token=settings.telegram_bot_token)
    storage = RedisStorage.from_url(settings.redis_url)
    dp = Dispatcher(storage=storage)
    
    # Register handlers
    from src.bot.handlers import commands
    dp.include_router(commands.router)
    
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
```

- [ ] Создать main.py
- [ ] Настроить Bot и Dispatcher
- [ ] Подключить Redis storage

### 2.2 Простая аутентификация (3-4 дня)

#### Регистрация
- [ ] Handler для `/start`:
```python
@router.message(Command("start"))
async def start_handler(message: Message):
    user = await get_or_create_user(message.from_user.id)
    await message.answer(f"Привет, {user.username}!")
```

- [ ] Функция `get_or_create_user()`:
  - Проверка в БД
  - Создание если нет
  - Роль по умолчанию: 'user'

#### Простые роли
- [ ] Только 2 роли: `admin` и `user`
- [ ] Первый пользователь = admin
- [ ] Остальные = user

#### Middleware для проверки
```python
class AuthMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = await get_user(event.from_user.id)
        if not user:
            await event.answer("Сначала /start")
            return
        data['user'] = user
        return await handler(event, data)
```

### 2.3 Базовые команды (2-3 дня)

#### Команды для всех
- [ ] `/start` - регистрация/приветствие
- [ ] `/help` - список команд
- [ ] `/status` - статус бота
- [ ] `/profile` - профиль пользователя

#### Команды для admin
- [ ] `/users` - список пользователей
- [ ] `/make_admin <user_id>` - сделать админом

#### src/bot/handlers/commands.py
```python
from aiogram import Router
from aiogram.filters import Command

router = Router()

@router.message(Command("start"))
async def start(message: Message):
    # Регистрация
    pass

@router.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer("""
Доступные команды:
/start - Начать
/help - Помощь
/status - Статус
/profile - Профиль
    """)

@router.message(Command("status"))
async def status(message: Message):
    await message.answer("✅ Бот работает")
```

### 2.4 Простые inline кнопки (1-2 дня)

#### Главное меню
```python
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")],
        [InlineKeyboardButton(text="📊 Статус", callback_data="status")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")]
    ])
```

- [ ] Создать клавиатуры
- [ ] Обработчики callback

### 2.5 Простое логирование (1 день)

#### Логирование команд
```python
async def log_command(user_id: int, command: str):
    await db.execute(
        "INSERT INTO audit_logs (user_id, action) VALUES ($1, $2)",
        user_id, command
    )
```

- [ ] Логирование всех команд
- [ ] Сохранение в БД

### 2.6 Обработка ошибок (1 день)

#### Простой error handler
```python
@router.error()
async def error_handler(event, exception):
    logging.error(f"Error: {exception}")
    await event.message.answer("Произошла ошибка. Попробуйте позже.")
```

- [ ] Глобальный error handler
- [ ] Логирование ошибок
- [ ] Уведомление пользователя

### 2.7 Тестирование (2 дня)

#### Простые тесты
```python
import pytest
from src.services.auth_service import get_or_create_user

@pytest.mark.asyncio
async def test_create_user():
    user = await get_or_create_user(12345, "testuser")
    assert user.telegram_id == 12345
```

- [ ] Тесты для auth
- [ ] Тесты для команд
- [ ] Базовое покрытие

## Структура кода

```
src/
├── bot/
│   ├── main.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   └── commands.py
│   ├── middlewares/
│   │   ├── __init__.py
│   │   └── auth.py
│   └── keyboards/
│       ├── __init__.py
│       └── inline.py
├── services/
│   ├── __init__.py
│   └── auth_service.py
├── models/
│   └── user.py
└── core/
    ├── config.py
    └── database.py
```

## Минимальные требования

Без дополнительных сервисов - всё в одном контейнере.

## Критерии завершения

- [ ] Бот запускается
- [ ] Регистрация работает
- [ ] Роли работают
- [ ] Базовые команды работают
- [ ] Inline кнопки работают
- [ ] Логирование работает
- [ ] Ошибки обрабатываются
- [ ] Базовые тесты проходят

## Следующая фаза

После завершения базового бота переходим к **Фазе 3: Claude интеграция**
