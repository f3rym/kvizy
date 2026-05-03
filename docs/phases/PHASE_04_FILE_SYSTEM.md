# Фаза 4: Файловая система (упрощенная)

**Длительность:** 1-2 недели  
**Цель:** Базовое управление файлами с безопасностью

## Упрощенный подход

Минимальный функционал:
- Навигация по разрешенным директориям
- Чтение/создание/редактирование файлов
- Простые подтверждения
- Базовая безопасность
- Без сложных batch операций

## Задачи

### 4.1 Базовая навигация (2-3 дня)

#### src/services/file_service.py
```python
import os
from pathlib import Path

class FileService:
    def __init__(self):
        self.allowed_dirs = ['/app/data', '/app/workspace']
        self.blacklist = ['/etc', '/sys', '/proc', '/root']
    
    def validate_path(self, path: str) -> bool:
        real_path = os.path.realpath(path)
        
        # Проверка blacklist
        if any(real_path.startswith(bl) for bl in self.blacklist):
            return False
        
        # Проверка whitelist
        if not any(real_path.startswith(al) for al in self.allowed_dirs):
            return False
        
        return True
    
    async def list_files(self, path: str):
        if not self.validate_path(path):
            raise PermissionError("Access denied")
        
        files = []
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            files.append({
                'name': item,
                'is_dir': os.path.isdir(full_path),
                'size': os.path.getsize(full_path) if os.path.isfile(full_path) else 0
            })
        return files
```

#### Команды
- [ ] `/ls [path]` - список файлов
- [ ] `/cd <path>` - смена директории (сохранение в Redis)
- [ ] `/pwd` - текущая директория

### 4.2 Чтение файлов (1-2 дня)

#### Команда /cat
```python
@router.message(Command("cat"))
async def cat_handler(message: Message, user: User):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /cat <файл>")
        return
    
    file_path = args[1]
    
    try:
        if not file_service.validate_path(file_path):
            await message.answer("❌ Доступ запрещен")
            return
        
        with open(file_path, 'r') as f:
            content = f.read(5000)  # Первые 5000 символов
        
        await message.answer(f"```\n{content}\n```", parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")
```

- [ ] `/cat <file>` - просмотр файла
- [ ] Ограничение 5000 символов
- [ ] Syntax highlighting (Markdown)

### 4.3 Создание и редактирование (2-3 дня)

#### Команда /create
```python
@router.message(Command("create"))
async def create_handler(message: Message, state: FSMContext):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /create <файл>")
        return
    
    await state.update_data(file_path=args[1])
    await state.set_state(FileStates.creating)
    await message.answer("Отправьте содержимое файла:")
```

- [ ] `/create <file>` - создать файл
- [ ] FSM для ввода содержимого
- [ ] Подтверждение перед созданием

#### Команда /edit
- [ ] `/edit <file>` - редактировать файл
- [ ] Показать текущее содержимое
- [ ] FSM для нового содержимого
- [ ] Подтверждение с diff

### 4.4 Удаление (1 день)

#### Команда /rm
```python
@router.message(Command("rm"))
async def rm_handler(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /rm <файл>")
        return
    
    file_path = args[1]
    
    # Подтверждение
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Удалить", callback_data=f"rm_confirm:{file_path}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="rm_cancel")]
    ])
    
    await message.answer(
        f"⚠️ Удалить файл {file_path}?\nЭто действие нельзя отменить!",
        reply_markup=keyboard
    )
```

- [ ] `/rm <file>` - удалить файл
- [ ] Двойное подтверждение
- [ ] Только для файлов (не директорий)

### 4.5 Загрузка/скачивание (2 дня)

#### Загрузка в бот
```python
@router.message(F.document)
async def document_handler(message: Message):
    # Получить текущую директорию пользователя
    current_dir = await redis.get(f"cwd:{message.from_user.id}")
    
    # Скачать файл
    file = await message.bot.download(message.document)
    
    # Сохранить
    file_path = os.path.join(current_dir, message.document.file_name)
    
    if not file_service.validate_path(file_path):
        await message.answer("❌ Доступ запрещен")
        return
    
    with open(file_path, 'wb') as f:
        f.write(file.read())
    
    await message.answer(f"✅ Файл сохранен: {file_path}")
```

- [ ] Обработка документов
- [ ] Сохранение в текущую директорию
- [ ] Проверка размера (макс 20MB)

#### Скачивание из бота
- [ ] `/download <file>` - скачать файл
- [ ] Отправка как документ
- [ ] Проверка размера (макс 50MB Telegram лимит)

### 4.6 Простые подтверждения (1-2 дня)

#### Уровни подтверждений
- **Level 0:** Чтение - без подтверждения
- **Level 1:** Создание - простое подтверждение
- **Level 2:** Изменение - подтверждение с preview
- **Level 3:** Удаление - двойное подтверждение

#### Реализация
```python
async def require_confirmation(message: Message, action: str, level: int):
    if level == 0:
        return True
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm:{action}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])
    
    await message.answer(f"Подтвердите действие: {action}", reply_markup=keyboard)
```

### 4.7 Безопасность (1-2 дня)

#### Path validation
- [ ] Проверка на `../` (path traversal)
- [ ] Нормализация путей
- [ ] Blacklist системных директорий
- [ ] Whitelist разрешенных директорий

#### Ограничения
- [ ] Максимальный размер файла: 20MB
- [ ] Запрет опасных расширений: .exe, .sh (опционально)
- [ ] Rate limiting для файловых операций

#### Аудит
- [ ] Логирование всех операций
- [ ] Сохранение в audit_logs

### 4.8 Тестирование (1 день)

#### Тесты
```python
def test_validate_path():
    service = FileService()
    assert service.validate_path('/app/data/test.txt') == True
    assert service.validate_path('/etc/passwd') == False
    assert service.validate_path('/app/data/../../../etc/passwd') == False
```

- [ ] Тесты валидации путей
- [ ] Тесты файловых операций
- [ ] Тесты безопасности

## Структура кода

```
src/
├── services/
│   └── file_service.py
└── bot/
    ├── handlers/
    │   └── files.py
    └── states/
        └── file_states.py
```

## Минимальные требования

Без дополнительных зависимостей - используем стандартную библиотеку Python.

## Критерии завершения

- [ ] Навигация работает
- [ ] Чтение файлов работает
- [ ] Создание/редактирование работает
- [ ] Удаление работает
- [ ] Загрузка/скачивание работает
- [ ] Подтверждения работают
- [ ] Безопасность настроена
- [ ] Тесты проходят

## Следующая фаза

После завершения файловой системы переходим к **Фазе 5: Простой мониторинг**
