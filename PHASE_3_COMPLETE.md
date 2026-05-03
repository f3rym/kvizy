# Claude Telegram Bot - Phase 3: Claude Integration

## Что создано

### Сервисы

#### ClaudeService (`src/services/claude_service.py`)
- ✅ `query()` - отправка запросов в Claude CLI
  - Поддержка разных моделей (opus, sonnet, haiku)
  - Настройка temperature и max_tokens
  - Timeout 60 секунд
  - Обработка ошибок
- ✅ `analyze_code()` - анализ кода
- ✅ `review_code()` - code review
- ✅ `fix_code()` - исправление кода

#### KeyService (`src/services/key_service.py`)
- ✅ Шифрование API ключей (Fernet/AES-256)
- ✅ `save_key()` - сохранение ключа
- ✅ `get_key()` - получение ключа
- ✅ `delete_key()` - удаление ключа
- ✅ `mask_key()` - маскирование для отображения

#### CacheService (`src/services/cache_service.py`)
- ✅ Кэширование ответов Claude в Redis
- ✅ TTL 1 час
- ✅ Автоматическое кэширование при запросах
- ✅ Cache hit/miss логирование

### Обработчики команд

#### API ключи
- ✅ `/api_key_add` - добавить API ключ (с FSM)
- ✅ `/api_key_show` - показать замаскированный ключ
- ✅ `/api_key_remove` - удалить ключ

#### Работа с Claude
- ✅ `/ask <вопрос>` - задать любой вопрос
- ✅ `/analyze <код>` - анализ кода
- ✅ `/review <код>` - code review
- ✅ `/fix <код>` - исправление кода

### Интеграция
- ✅ Обновлен `src/bot/main.py` - подключены сервисы
- ✅ Обновлен `/help` - добавлены команды Claude

## Функционал

### Безопасность API ключей
- Ключи шифруются с помощью Fernet (AES-256)
- Ключ шифрования хранится в .env
- Сообщения с ключами автоматически удаляются
- Отображение только замаскированных ключей

### Кэширование
- Автоматическое кэширование всех ответов Claude
- TTL 1 час
- Ключ кэша: MD5(model:prompt)
- Экономия API calls и времени

### Обработка ошибок
- Timeout 60 секунд
- Обработка ошибок Claude CLI
- Проверка наличия API ключа
- Логирование всех операций

## Как использовать

### 1. Получить Claude API ключ
Зарегистрируйтесь на https://console.anthropic.com/ и получите API ключ

### 2. Добавить ключ в бот
```
/api_key_add
<отправить ключ>
```

### 3. Задать вопрос
```
/ask Что такое Python?
```

### 4. Анализ кода
```
/analyze
def hello():
    print("Hello")
```

### 5. Code review
```
/review
def process(data):
    return eval(data)  # Опасно!
```

### 6. Исправление кода
```
/fix
def add(a, b)
    return a + b  # Синтаксическая ошибка
```

## Требования

### Claude CLI
Необходимо установить Claude CLI:
```bash
pip install anthropic-cli
```

Или использовать официальный Claude CLI от Anthropic.

### Encryption Key
Сгенерировать ключ шифрования:
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

Добавить в `.env`:
```
ENCRYPTION_KEY=your_generated_key_here
```

## Тестирование

### 1. Запустить бот
```bash
docker-compose up -d
docker-compose logs -f bot
```

### 2. В Telegram
1. `/api_key_add` - добавить ключ
2. `/api_key_show` - проверить ключ
3. `/ask Привет!` - протестировать запрос
4. `/analyze print("test")` - протестировать анализ

### 3. Проверить кэш
```bash
docker-compose exec redis redis-cli
> KEYS cache:claude:*
> TTL cache:claude:<key>
```

## Следующий шаг

**Фаза 4: Файловая система** - добавление управления файлами

---

**Статус:** ✅ Фаза 3 завершена
