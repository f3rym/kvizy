# Фаза 1: Инфраструктура (упрощенная)

**Длительность:** 1-2 недели  
**Цель:** Минимальная инфраструктура в Docker Compose

## Упрощенный подход

Всё работает на одном сервере в Docker Compose:
- PostgreSQL (один контейнер)
- Redis (один контейнер)
- Bot (один контейнер)

Без Kubernetes, без сложного мониторинга, без микросервисов.

## Задачи

### 1.1 Docker Compose окружение (2-3 дня)

#### docker-compose.yml
- [ ] Создать `docker-compose.yml`:
```yaml
version: '3.8'
services:
  bot:
    build: .
    restart: always
    depends_on:
      - postgres
      - redis
    env_file: .env
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
  
  postgres:
    image: postgres:15-alpine
    restart: always
    environment:
      POSTGRES_DB: claude_bot
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

#### Dockerfile
- [ ] Создать простой `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "src.bot.main"]
```

#### .env файл
- [ ] Создать `.env.example`:
```
TELEGRAM_BOT_TOKEN=your_token_here
DB_PASSWORD=your_password
REDIS_URL=redis://redis:6379
DATABASE_URL=postgresql://postgres:password@postgres:5432/claude_bot
```

### 1.2 Базы данных (2 дня)

#### PostgreSQL схема
- [ ] Создать `migrations/001_initial.sql`:
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    role VARCHAR(50) DEFAULT 'guest',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    encrypted_key TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(255),
    details TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Инициализация БД
- [ ] Создать `scripts/init_db.py`:
```python
import psycopg2
import os

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
with open('migrations/001_initial.sql') as f:
    conn.cursor().execute(f.read())
conn.commit()
```

### 1.3 Структура проекта (1 день)

```
claude-telegram/
├── src/
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── handlers/
│   │   └── middlewares/
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   └── claude_service.py
│   ├── models/
│   │   └── user.py
│   └── core/
│       ├── config.py
│       └── database.py
├── tests/
├── migrations/
├── logs/
├── data/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

- [ ] Создать всю структуру
- [ ] Создать пустые `__init__.py`

### 1.4 Зависимости (1 день)

#### requirements.txt
```
aiogram==3.4.1
asyncpg==0.29.0
redis==5.0.1
python-dotenv==1.0.0
psycopg2-binary==2.9.9
```

- [ ] Создать requirements.txt
- [ ] Тестовая установка

### 1.5 Базовая конфигурация (1 день)

#### src/core/config.py
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    telegram_bot_token: str
    database_url: str
    redis_url: str
    
    class Config:
        env_file = ".env"

settings = Settings()
```

#### src/core/database.py
```python
import asyncpg

async def get_db_pool():
    return await asyncpg.create_pool(settings.database_url)
```

### 1.6 Простое логирование (1 день)

#### Логи в файл
- [ ] Настроить logging в файл `logs/bot.log`
- [ ] Ротация логов (daily)
- [ ] Простой формат

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
```

### 1.7 Запуск и тестирование (1 день)

- [ ] `docker-compose up -d`
- [ ] Проверка контейнеров
- [ ] Проверка подключения к БД
- [ ] Проверка подключения к Redis
- [ ] Инициализация БД

## Минимальные требования

**Сервер:**
- 2 CPU cores
- 4 GB RAM
- 20 GB disk

**Команды:**
```bash
# Запуск
docker-compose up -d

# Логи
docker-compose logs -f bot

# Остановка
docker-compose down

# Перезапуск
docker-compose restart bot
```

## Критерии завершения

- [ ] Docker Compose работает
- [ ] PostgreSQL доступна
- [ ] Redis доступен
- [ ] Структура проекта создана
- [ ] Зависимости установлены
- [ ] Конфигурация загружается
- [ ] Логирование работает

## Следующая фаза

После завершения инфраструктуры переходим к **Фазе 2: Базовый бот**
