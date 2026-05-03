# Фаза 3: Claude интеграция (упрощенная)

**Длительность:** 2 недели  
**Цель:** Базовая работа с Claude CLI

## Упрощенный подход

Минимальный функционал:
- Простой wrapper для Claude CLI
- Базовые запросы
- Простое управление конфигурацией
- Без сложного контекста
- Без batch обработки (можно добавить позже)

## Задачи

### 3.1 Простой Claude wrapper (3-4 дня)

#### src/services/claude_service.py
```python
import subprocess
import asyncio

class ClaudeService:
    async def query(self, prompt: str, api_key: str, model: str = "claude-sonnet-4-6"):
        cmd = [
            "claude",
            "--api-key", api_key,
            "--model", model,
            prompt
        ]
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            raise Exception(f"Claude error: {stderr.decode()}")
        
        return stdout.decode()
```

- [ ] Создать простой wrapper
- [ ] Subprocess управление
- [ ] Обработка ошибок
- [ ] Timeout (30 сек)

### 3.2 Управление API ключами (2 дня)

#### Хранение ключей
```python
from cryptography.fernet import Fernet

class KeyService:
    def __init__(self):
        self.cipher = Fernet(settings.encryption_key)
    
    async def save_key(self, user_id: int, api_key: str):
        encrypted = self.cipher.encrypt(api_key.encode())
        await db.execute(
            "INSERT INTO api_keys (user_id, encrypted_key) VALUES ($1, $2)",
            user_id, encrypted
        )
    
    async def get_key(self, user_id: int):
        row = await db.fetchrow(
            "SELECT encrypted_key FROM api_keys WHERE user_id = $1",
            user_id
        )
        if row:
            return self.cipher.decrypt(row['encrypted_key']).decode()
```

#### Команды
- [ ] `/api_key_add` - добавить ключ
- [ ] `/api_key_show` - показать (частично)
- [ ] `/api_key_remove` - удалить

### 3.3 Простая конфигурация (1-2 дня)

#### Базовые настройки
```python
class Config:
    model: str = "claude-sonnet-4-6"
    temperature: float = 0.7
    max_tokens: int = 4000
```

#### Команды
- [ ] `/config` - показать конфигурацию
- [ ] `/config_model <model>` - выбрать модель
  - claude-opus-4-7
  - claude-sonnet-4-6
  - claude-haiku-4-5

### 3.4 Базовые запросы (2-3 дня)

#### Команда /ask
```python
@router.message(Command("ask"))
async def ask_handler(message: Message, user: User):
    prompt = message.text.replace("/ask", "").strip()
    
    if not prompt:
        await message.answer("Использование: /ask <ваш вопрос>")
        return
    
    api_key = await key_service.get_key(user.id)
    if not api_key:
        await message.answer("Сначала добавьте API ключ: /api_key_add")
        return
    
    status = await message.answer("🤔 Думаю...")
    
    try:
        response = await claude_service.query(prompt, api_key)
        await status.delete()
        await message.answer(response)
    except Exception as e:
        await status.delete()
        await message.answer(f"Ошибка: {e}")
```

- [ ] `/ask <prompt>` - простой запрос
- [ ] Обработка длинных ответов (разбивка на части)
- [ ] Индикатор загрузки

#### Команда /chat (опционально)
- [ ] Простой chat режим
- [ ] Сохранение последних 5 сообщений в Redis
- [ ] `/exit` для выхода

### 3.5 Работа с кодом (3-4 дня)

#### Команда /analyze
```python
@router.message(Command("analyze"))
async def analyze_handler(message: Message, user: User):
    # Получить путь к файлу
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /analyze <путь к файлу>")
        return
    
    file_path = args[1]
    
    # Прочитать файл
    try:
        with open(file_path) as f:
            code = f.read()
    except Exception as e:
        await message.answer(f"Ошибка чтения файла: {e}")
        return
    
    # Отправить в Claude
    prompt = f"Проанализируй этот код:\n\n```\n{code}\n```"
    response = await claude_service.query(prompt, api_key)
    
    await message.answer(response)
```

- [ ] `/analyze <file>` - анализ кода
- [ ] `/review <file>` - code review
- [ ] `/fix <file>` - предложить исправления

### 3.6 Простое кэширование (1 день)

#### Кэш в Redis
```python
import hashlib

async def get_cached_response(prompt: str):
    key = f"cache:{hashlib.md5(prompt.encode()).hexdigest()}"
    cached = await redis.get(key)
    if cached:
        return cached.decode()
    return None

async def cache_response(prompt: str, response: str):
    key = f"cache:{hashlib.md5(prompt.encode()).hexdigest()}"
    await redis.setex(key, 3600, response)  # 1 час
```

- [ ] Кэширование ответов
- [ ] TTL 1 час
- [ ] Команда `/cache_clear` (admin)

### 3.7 Простая статистика (1 день)

#### Счетчики
```python
async def track_usage(user_id: int, tokens: int):
    await redis.hincrby(f"usage:{user_id}", "requests", 1)
    await redis.hincrby(f"usage:{user_id}", "tokens", tokens)
```

#### Команда /my_stats
- [ ] Количество запросов
- [ ] Примерное количество токенов
- [ ] Примерная стоимость

### 3.8 Тестирование (2 дня)

#### Тесты
```python
@pytest.mark.asyncio
async def test_claude_query():
    service = ClaudeService()
    response = await service.query("Hello", "test_key")
    assert response is not None
```

- [ ] Тесты wrapper
- [ ] Тесты команд
- [ ] Mock Claude CLI

## Структура кода

```
src/
├── services/
│   ├── claude_service.py
│   ├── key_service.py
│   └── cache_service.py
└── bot/
    └── handlers/
        └── claude.py
```

## Минимальные требования

Дополнительные пакеты:
```
cryptography==41.0.7
```

## Критерии завершения

- [ ] Claude wrapper работает
- [ ] API ключи сохраняются безопасно
- [ ] Базовая конфигурация работает
- [ ] Команда /ask работает
- [ ] Команды работы с кодом работают
- [ ] Кэширование работает
- [ ] Статистика собирается
- [ ] Тесты проходят

## Следующая фаза

После завершения Claude интеграции переходим к **Фазе 4: Файловая система**
