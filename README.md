# 🤖 Claude Telegram Bot

Полнофункциональный Telegram бот для работы с Claude AI от Anthropic. Предоставляет удобный интерфейс для взаимодействия с Claude через Telegram с поддержкой выполнения команд, планировщика задач и управления доступом.

## ✨ Основные возможности

### 💬 Работа с Claude AI
- **Режим диалога** - общайтесь с Claude без команд, как в обычном чате
- **Выполнение bash команд** - Claude может выполнять команды на сервере с вашего подтверждения
- **История диалогов** - сохранение контекста беседы между сессиями
- **Анализ и review кода** - встроенные команды для работы с кодом
- **Доступ к kubectl и Docker** - управление Kubernetes и контейнерами
- **Персистентное хранилище** - `/home/claude` для сохранения проектов между сессиями

### 🔑 Управление доступом
- **Whitelist система** - контроль доступа к боту
- **Sharing API ключей** - делитесь своим Claude API ключом с коллегами
- **Роли пользователей** - админы и обычные пользователи
- **Аудит действий** - логирование всех операций
- **Шифрование ключей** - все API ключи хранятся в зашифрованном виде

### ⏰ Планировщик задач
- **Cron задачи** - периодическое выполнение команд Claude
- **Напоминания** - одноразовые задачи на определенное время
- **Персистентность** - задачи сохраняются при перезапуске бота
- **Управление через кнопки** - удобное добавление и удаление задач

### 📊 Мониторинг
- **Системная статистика** - CPU, память, диск, сеть
- **Docker контейнеры** - мониторинг состояния контейнеров
- **Kubernetes поды** - проверка статуса подов
- **Логи и аудит** - просмотр действий пользователей
- **Настраиваемые пороги** - предупреждения о превышении лимитов

### 📁 Файловая система
- **Навигация** - ls, cd, pwd команды
- **Чтение и создание файлов** - просмотр и редактирование
- **Скачивание** - получение файлов через бота
- **Загрузка** - отправка файлов в бот
- **Безопасность** - whitelist директорий, защита от path traversal

## 🚀 Быстрый старт

### Требования
- Docker и Docker Compose V2
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))
- Claude API Key (получить на [console.anthropic.com](https://console.anthropic.com))

### Установка

1. **Клонируйте репозиторий**
```bash
git clone <repository-url>
cd claude-telegram
```

2. **Создайте `.env` файл**
```bash
cp .env.example .env
```

3. **Настройте переменные окружения**
```env
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Database
POSTGRES_DB=claude_bot
POSTGRES_PASSWORD=your_secure_password
DATABASE_URL=postgresql://postgres:your_secure_password@postgres:5432/claude_bot

# Redis
REDIS_URL=redis://redis:6379

# Encryption (сгенерируйте: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ENCRYPTION_KEY=your_encryption_key_here

# Environment
ENVIRONMENT=production
LOG_LEVEL=INFO
```

4. **Запустите бота**
```bash
docker compose up -d
```

5. **Проверьте логи**
```bash
docker logs bot -f
```

6. **Остановите бота**
```bash
docker compose down
```

## 🏗️ Архитecture

```
claude-telegram/
├── src/
│   ├── bot/
│   │   ├── handlers/          # Обработчики команд
│   │   │   ├── commands.py    # Основные команды и кнопки
│   │   │   ├── claude.py      # Claude AI интеграция
│   │   │   ├── scheduler.py   # Планировщик задач
│   │   │   ├── key_sharing.py # Управление shared ключами
│   │   │   ├── files.py       # Файловая система
│   │   │   ├── monitor.py     # Мониторинг
│   │   │   ├── audit.py       # Аудит
│   │   │   └── whitelist.py   # Whitelist управление
│   │   ├── middlewares/       # Middleware
│   │   │   ├── auth.py        # Аутентификация и whitelist
│   │   │   └── audit.py       # Логирование действий
│   │   └── main.py            # Точка входа
│   ├── services/              # Бизнес-логика
│   │   ├── claude_service.py  # Работа с Claude API
│   │   ├── key_service.py     # Управление API ключами
│   │   ├── scheduler_service.py # APScheduler интеграция
│   │   ├── cache_service.py   # Redis кэширование
│   │   ├── auth_service.py    # Аутентификация
│   │   ├── whitelist_service.py # Whitelist
│   │   ├── file_service.py    # Файловые операции
│   │   ├── monitor_service.py # Системный мониторинг
│   │   └── audit_service.py   # Аудит логи
│   ├── models/                # Модели данных
│   │   └── user.py            # User model
│   ├── core/                  # Ядро приложения
│   │   ├── config.py          # Конфигурация
│   │   └── database.py        # PostgreSQL connection pool
│   └── utils/
│       └── logger.py          # Логирование
├── migrations/                # SQL миграции
│   ├── 001_initial.sql        # Базовые таблицы
│   ├── 002_add_whitelist.sql  # Whitelist
│   ├── 003_add_claude_config.sql # Claude конфигурация
│   └── 004_add_key_sharing.sql # Shared keys
├── docker-compose.yml         # Docker Compose конфигурация
├── Dockerfile                 # Docker образ бота
├── requirements.txt           # Python зависимости
└── README.md                  # Документация
```

## 🗄️ База данных

### Таблицы
- **users** - пользователи бота (id, telegram_id, username, role)
- **api_keys** - зашифрованные API ключи (user_id, encrypted_key, base_url, model)
- **key_sharing** - связи shared ключей (owner_user_id, shared_with_user_id)
- **whitelist** - список разрешенных пользователей (telegram_id, added_by, notes)
- **audit_logs** - логи действий пользователей (user_id, action, details, success)

### Миграции
Миграции применяются автоматически при первом запуске. Для ручного применения:
```bash
docker exec -i postgres psql -U postgres -d claude_bot < migrations/001_initial.sql
```

## 📱 Использование

### Первый запуск

1. Напишите боту `/start`
2. Первый пользователь автоматически становится админом и добавляется в whitelist
3. Добавьте свой Claude API ключ: `/api_key_add`
4. Начните общение с Claude!

### Основные команды

#### 🤖 Claude AI
- `/ask <вопрос>` - задать вопрос Claude
- `/clear` - очистить историю диалога
- `/analyze <код>` - анализ кода
- `/review <код>` - code review
- `/fix <код>` - исправить код

#### 💬 Режим диалога
- Нажмите кнопку **"💬 Диалог с Claude"**
- Пишите сообщения без команд
- Claude автоматически предлагает выполнить нужные команды
- Подтверждайте выполнение через кнопки
- Нажмите **"🚪 Выйти из диалога"** для выхода

#### 🔑 Управление ключами
- `/api_key_add` - добавить свой API ключ
- `/api_key_show` - показать конфигурацию
- `/api_key_remove` - удалить ключ
- `/share_key @username [note]` - поделиться ключом с пользователем
- `/revoke_key @username` - отозвать доступ
- `/my_shares` - посмотреть предоставленные доступы

#### ⏰ Планировщик
- `/cron` - создать cron-задачу (интерактивно)
- `/reminder` - создать напоминание (интерактивно)
- `/cronlist` - список всех задач с кнопками удаления
- `/cronremove <task_id>` - удалить задачу

**Примеры cron выражений:**
- `*/5 * * * *` - каждые 5 минут
- `0 */2 * * *` - каждые 2 часа
- `0 9 * * 1-5` - в 9:00 по будням
- `30 14 * * *` - каждый день в 14:30

#### 📊 Мониторинг
- `/stats` - статистика системы
- `/docker` - Docker контейнеры
- `/health` - проверка здоровья
- `/my_logs` - мои действия
- `/my_stats` - моя статистика

#### 📁 Файлы
- `/ls [путь]` - список файлов
- `/pwd` - текущая директория
- `/cd <путь>` - перейти в директорию
- `/cat <файл>` - прочитать файл
- `/mkdir <имя>` - создать папку
- `/download <файл>` - скачать файл
- 📎 Отправить файл - загрузить файл в бот

#### 🔑 Админ (только для администраторов)
- `/users` - список пользователей
- `/make_admin <user_id>` - сделать админом
- `/whitelist_add <user> [note]` - добавить в whitelist
- `/whitelist_remove <user>` - удалить из whitelist
- `/whitelist` - показать whitelist
- `/audit_logs` - все логи
- `/audit_stats` - статистика аудита
- `/audit_user <user_id>` - логи пользователя

### Кнопки быстрого доступа

Бот предоставляет удобные кнопки внизу экрана:
- 💬 Диалог с Claude
- 📖 Помощь
- 📊 Статистика
- 👤 Профиль
- ⏰ Задачи
- 📁 Файлы
- 🗑 Очистить историю
- 🔑 Админ панель (для админов)

## 🔒 Безопасность

- **Шифрование API ключей** - все ключи хранятся в зашифрованном виде (Fernet/AES-256)
- **Whitelist система** - доступ только для разрешенных пользователей
- **Аудит действий** - все операции логируются с timestamp и user_id
- **Подтверждение команд** - bash команды требуют явного подтверждения через кнопки
- **Изоляция данных** - каждый пользователь видит только свои данные
- **Защита файловой системы** - whitelist директорий, защита от path traversal
- **Автоудаление ключей** - сообщения с API ключами автоматически удаляются
- **Маскирование** - ключи отображаются в замаскированном виде

## 🛠️ Разработка

### Локальная разработка

1. **Установите зависимости**
```bash
pip install -r requirements.txt
```

2. **Запустите PostgreSQL и Redis**
```bash
docker compose up -d postgres redis
```

3. **Примените миграции**
```bash
for f in migrations/*.sql; do
  docker exec -i postgres psql -U postgres -d claude_bot < "$f"
done
```

4. **Запустите бота**
```bash
python -m src.bot.main
```

### Добавление новых команд

1. Создайте обработчик в `src/bot/handlers/`
2. Зарегистрируйте роутер в `src/bot/main.py`
3. Добавьте команду в help меню в `src/bot/handlers/commands.py`
4. Добавьте кнопку, если нужно

### Добавление новых сервисов

1. Создайте сервис в `src/services/`
2. Импортируйте и используйте в обработчиках
3. Добавьте необходимые таблицы в новую миграцию

## 📊 Мониторинг и логи

### Просмотр логов
```bash
# Логи бота
docker logs bot -f

# Логи PostgreSQL
docker logs postgres -f

# Логи Redis
docker logs redis -f

# Все логи
docker compose logs -f
```

### Проверка состояния
```bash
# Статус контейнеров
docker compose ps

# Использование ресурсов
docker stats

# Проверка здоровья
docker compose exec bot python -c "print('OK')"
```

### Бэкап и восстановление

**Бэкап базы данных:**
```bash
docker exec postgres pg_dump -U postgres claude_bot > backup_$(date +%Y%m%d).sql
```

**Восстановление:**
```bash
docker exec -i postgres psql -U postgres claude_bot < backup_20260503.sql
```

**Очистка Redis кэша:**
```bash
docker exec redis redis-cli FLUSHDB
```

## 🔧 Troubleshooting

### Бот не запускается
1. Проверьте логи: `docker logs bot`
2. Убедитесь, что все переменные окружения установлены в `.env`
3. Проверьте доступность PostgreSQL: `docker compose ps postgres`
4. Проверьте доступность Redis: `docker compose ps redis`

### Команды не работают
1. Проверьте, что пользователь в whitelist: `/whitelist`
2. Проверьте логи аудита: `/my_logs`
3. Убедитесь, что API ключ добавлен: `/api_key_show`
4. Проверьте логи бота на наличие ошибок

### Планировщик не выполняет задачи
1. Проверьте список задач: `/cronlist`
2. Проверьте логи бота: `docker logs bot | grep scheduler`
3. Убедитесь, что задачи сохранены в Redis: `docker exec redis redis-cli KEYS "scheduled_jobs:*"`
4. Проверьте формат cron выражения

### База данных не подключается
1. Проверьте пароль в `.env`
2. Проверьте статус: `docker compose ps postgres`
3. Проверьте логи: `docker logs postgres`
4. Попробуйте подключиться вручную: `docker exec -it postgres psql -U postgres -d claude_bot`

### Shared keys не работают
1. Проверьте миграцию: `docker exec postgres psql -U postgres -d claude_bot -c "\d key_sharing"`
2. Проверьте доступы: `/my_shares`
3. Убедитесь, что владелец ключа добавил его: `/api_key_show`

## 🚀 Deployment

### Production рекомендации

1. **Используйте сильные пароли** для PostgreSQL
2. **Сгенерируйте уникальный ENCRYPTION_KEY**
3. **Настройте backup** базы данных (cron job)
4. **Мониторьте логи** и ресурсы
5. **Обновляйте зависимости** регулярно
6. **Используйте HTTPS** для webhook (опционально)
7. **Настройте firewall** для защиты портов

### Обновление

```bash
git pull
docker compose down
docker compose build --no-cache
docker compose up -d
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [Anthropic](https://www.anthropic.com/) - Claude AI
- [aiogram](https://github.com/aiogram/aiogram) - Telegram Bot framework
- [APScheduler](https://github.com/agronholm/apscheduler) - Task scheduler
- [asyncpg](https://github.com/MagicStack/asyncpg) - PostgreSQL driver
- [Redis](https://redis.io/) - Caching and job storage

## 📧 Support

Для вопросов и поддержки создайте issue в репозитории.

---

Made with ❤️ by [ferym](https://github.com/ferym)
