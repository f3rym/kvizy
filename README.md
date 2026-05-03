# Claude Telegram Bot

Telegram бот для работы с Claude AI через CLI с управлением файлами, мониторингом и аудитом.

## Возможности

### 🤖 Claude AI Integration
- Интеграция с Claude CLI
- Шифрование API ключей (AES-256)
- Кэширование ответов (Redis, TTL 1 час)
- Поддержка разных моделей (opus, sonnet, haiku)
- Команды: `/ask`, `/analyze`, `/review`, `/fix`

### 📁 File System
- Безопасная работа с файлами
- Whitelist/blacklist директорий
- Команды: `/ls`, `/pwd`, `/cd`, `/cat`, `/mkdir`, `/create`, `/rm`, `/download`
- Загрузка файлов через Telegram
- Защита от path traversal

### 📊 Monitoring
- Статистика системы (CPU, Memory, Disk, Network)
- Мониторинг Docker контейнеров
- Настраиваемые пороги предупреждений
- Команды: `/stats`, `/docker`, `/health`, `/alerts`

### 📋 Logging & Audit
- Автоматическое логирование всех действий
- Статистика использования
- Поиск по логам
- Команды: `/my_logs`, `/my_stats`, `/audit_logs`, `/audit_stats`

### 👥 User Management
- Роли: admin, user
- Первый пользователь становится админом
- Управление пользователями

## Быстрый старт

### 1. Клонировать репозиторий

```bash
git clone <repository-url>
cd claude-telegram
```

### 2. Создать .env файл

```bash
cp .env.example .env
```

Отредактировать `.env`:

```bash
# Telegram Bot Token (получить у @BotFather)
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Database Password
DB_PASSWORD=your_secure_password_here
DATABASE_URL=postgresql://postgres:your_secure_password_here@postgres:5432/claude_bot

# Redis
REDIS_URL=redis://redis:6379/0

# Encryption Key (сгенерировать)
ENCRYPTION_KEY=your_encryption_key_here

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### 3. Сгенерировать ключ шифрования

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Скопировать результат в `ENCRYPTION_KEY` в `.env`

### 4. Создать директории

```bash
mkdir -p logs data workspace
chmod 755 logs data workspace
```

### 5. Запустить

```bash
docker-compose up -d
```

### 6. Проверить логи

```bash
docker-compose logs -f bot
```

### 7. Остановить

```bash
docker-compose down
```

## Структура проекта

```
claude-telegram/
├── src/
│   ├── bot/
│   │   ├── handlers/          # Обработчики команд
│   │   │   ├── commands.py    # Основные команды
│   │   │   ├── claude.py      # Claude AI команды
│   │   │   ├── files.py       # Файловые команды
│   │   │   ├── monitor.py     # Мониторинг
│   │   │   └── audit.py       # Аудит
│   │   ├── middlewares/       # Middleware
│   │   │   ├── auth.py        # Аутентификация
│   │   │   └── audit.py       # Логирование
│   │   ├── states/            # FSM состояния
│   │   └── main.py            # Точка входа
│   ├── core/
│   │   ├── config.py          # Конфигурация
│   │   └── database.py        # База данных
│   ├── models/
│   │   └── user.py            # Модель пользователя
│   ├── services/              # Бизнес-логика
│   │   ├── auth_service.py    # Аутентификация
│   │   ├── claude_service.py  # Claude AI
│   │   ├── key_service.py     # API ключи
│   │   ├── cache_service.py   # Кэширование
│   │   ├── file_service.py    # Файлы
│   │   ├── monitor_service.py # Мониторинг
│   │   └── audit_service.py   # Аудит
│   └── utils/
│       └── logger.py          # Логирование
├── migrations/                # SQL миграции
├── docker-compose.yml         # Docker Compose
├── Dockerfile                 # Docker образ
├── requirements.txt           # Python зависимости
└── README.md                  # Документация
```

## Команды бота

### Основные команды

- `/start` - Начать работу с ботом
- `/help` - Справка по командам
- `/status` - Статус бота
- `/profile` - Ваш профиль

### Claude AI

- `/api_key_add` - Добавить API ключ
- `/api_key_show` - Показать API ключ (замаскированный)
- `/api_key_remove` - Удалить API ключ
- `/ask <вопрос>` - Задать вопрос Claude
- `/analyze <код>` - Анализ кода
- `/review <код>` - Code review
- `/fix <код>` - Исправить код

### Файловая система

- `/ls` - Список файлов в текущей директории
- `/pwd` - Показать текущую директорию
- `/cd <путь>` - Перейти в директорию
- `/cat <файл>` - Прочитать файл
- `/mkdir <имя>` - Создать директорию
- `/create <файл>` - Создать файл
- `/rm <файл>` - Удалить файл
- `/download <файл>` - Скачать файл
- 📎 Отправить файл - Загрузить файл в бот

### Мониторинг

- `/stats` - Статистика системы
- `/docker` - Статистика Docker контейнеров
- `/health` - Быстрая проверка здоровья
- `/alerts` - Показать пороги предупреждений

### Логи и аудит

- `/my_logs` - Мои последние действия
- `/my_stats` - Моя статистика

### Команды администратора

- `/users` - Список пользователей
- `/make_admin <user_id>` - Сделать пользователя админом
- `/set_alert <metric> <value>` - Установить порог предупреждения
- `/audit_logs [limit] [offset]` - Все логи аудита
- `/audit_stats` - Статистика действий
- `/audit_search <запрос>` - Поиск в логах
- `/audit_user <user_id>` - Логи пользователя

## Безопасность

### API ключи
- Шифрование Fernet (AES-256)
- Ключ шифрования в переменных окружения
- Автоматическое удаление сообщений с ключами
- Маскирование при отображении

### Файловая система
- Whitelist разрешенных директорий: `/app/data`, `/app/workspace`
- Blacklist системных директорий: `/etc`, `/sys`, `/proc`, и т.д.
- Защита от path traversal
- Разрешение symlinks
- Ограничение размера файлов (20MB)

### Аудит
- Логирование всех действий
- Пользователи видят только свои логи
- Админы видят все логи
- Нет логирования паролей и API ключей

## Требования

### Системные требования
- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM минимум
- 10GB свободного места на диске

### Python зависимости
- Python 3.11+
- aiogram 3.4.1
- asyncpg 0.29.0
- redis 5.0.1
- cryptography 41.0.7
- psutil 5.9.6
- docker 7.0.0

## Мониторинг

### Логи

```bash
# Все логи
docker-compose logs -f

# Только бот
docker-compose logs -f bot

# Только база данных
docker-compose logs -f postgres

# Только Redis
docker-compose logs -f redis
```

### Статус контейнеров

```bash
docker-compose ps
```

### Использование ресурсов

```bash
docker stats
```

## Обслуживание

### Бэкап базы данных

```bash
docker-compose exec postgres pg_dump -U postgres claude_bot > backup.sql
```

### Восстановление базы данных

```bash
docker-compose exec -T postgres psql -U postgres claude_bot < backup.sql
```

### Очистка кэша Redis

```bash
docker-compose exec redis redis-cli FLUSHDB
```

### Обновление

```bash
git pull
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Разработка

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Запуск локально

```bash
# Запустить только БД и Redis
docker-compose up -d postgres redis

# Запустить бот локально
python -m src.bot.main
```

### Тестирование

```bash
pytest
```

### Форматирование кода

```bash
black src/
flake8 src/
```

## Troubleshooting

### Бот не запускается

1. Проверить логи: `docker-compose logs bot`
2. Проверить .env файл
3. Проверить доступность Telegram API
4. Проверить подключение к БД и Redis

### База данных не подключается

1. Проверить пароль в .env
2. Проверить статус контейнера: `docker-compose ps postgres`
3. Проверить логи: `docker-compose logs postgres`

### Redis не работает

1. Проверить статус: `docker-compose ps redis`
2. Проверить логи: `docker-compose logs redis`
3. Проверить подключение: `docker-compose exec redis redis-cli ping`

### Ошибки с файлами

1. Проверить права доступа к директориям `data/` и `workspace/`
2. Проверить whitelist в `src/services/file_service.py`

## Фазы разработки

- ✅ Phase 1: Project Setup
- ✅ Phase 2: User Management
- ✅ Phase 3: Claude Integration
- ✅ Phase 4: File System
- ✅ Phase 5: Simple Monitoring
- ✅ Phase 6: Logging & Audit
- 🔄 Phase 7-10: В разработке

## Лицензия

MIT

## Поддержка

Для вопросов и предложений создавайте issue в репозитории.
