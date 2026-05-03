# Claude Telegram Bot

Telegram-бот для управления Claude CLI с минимальными требованиями.

## 🎯 Описание

Полнофункциональный бот для работы с Claude AI через Telegram с управлением файлами, мониторингом и автоматизацией. Всё работает в Docker Compose на одном сервере.

## ✨ Основные возможности

- 🤖 **Claude AI интеграция** - работа с Claude CLI
- 📁 **Файловая система** - безопасное управление файлами
- 👥 **Аутентификация** - система ролей (admin/user)
- 📊 **Мониторинг** - системы и Docker контейнеров
- 🔔 **Алертинг** - уведомления в Telegram
- ⚙️ **Автоматизация** - cron задачи и триггеры
- 🔒 **Безопасность** - шифрование, валидация, аудит
- 💾 **Backup** - автоматическое резервное копирование

## 📋 Документация

### Начало работы
- **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - Обзор проекта и быстрый старт
- **[docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md)** - Полный план разработки

### Фазы разработки
1. [Фаза 1: Инфраструктура](docs/phases/PHASE_01_INFRASTRUCTURE.md) - 1-2 недели
2. [Фаза 2: Базовый бот](docs/phases/PHASE_02_BASIC_BOT.md) - 2-3 недели
3. [Фаза 3: Claude интеграция](docs/phases/PHASE_03_CLAUDE_INTEGRATION.md) - 2 недели
4. [Фаза 4: Файловая система](docs/phases/PHASE_04_FILE_SYSTEM.md) - 1-2 недели
5. [Фаза 5: Простой мониторинг](docs/phases/PHASE_05_SIMPLE_MONITORING.md) - 1 неделя
6. [Фаза 7: Автоматизация](docs/phases/PHASE_07_AUTOMATION.md) - 1-2 недели
7. [Фаза 8: Интеграции](docs/phases/PHASE_08_INTEGRATIONS.md) - 2 недели
8. [Фаза 9: Дополнительные фичи](docs/phases/PHASE_09_ADDITIONAL_FEATURES.md) - 1-2 недели
9. [Фаза 10: Финализация](docs/phases/PHASE_10_FINALIZATION.md) - 2-3 недели

## 💻 Минимальные требования

**Сервер:**
- CPU: 2 cores
- RAM: 4 GB
- Disk: 20 GB SSD
- OS: Ubuntu 20.04+

**Стоимость:** ~$10-20/месяц (VPS)

## 🛠️ Технологии

- Python 3.11+
- aiogram 3.x (Telegram Bot)
- PostgreSQL 15 (Alpine)
- Redis 7 (Alpine)
- Docker Compose

## 📊 Timeline

```
Месяц 1: Инфраструктура + Базовый бот
Месяц 2: Claude интеграция + Файлы → MVP готов! 🎉
Месяц 3: Мониторинг + Автоматизация
Месяц 4: Интеграции + Доп. фичи
Месяц 5: Финализация → Production! 🚀
```

## 🚀 Быстрый старт

### 1. Изучить документацию
```bash
cat PROJECT_OVERVIEW.md
cat docs/DEVELOPMENT_PLAN.md
```

### 2. Начать с Фазы 1
```bash
cat docs/phases/PHASE_01_INFRASTRUCTURE.md
```

### 3. Следовать плану
Фаза 1 → Фаза 2 → Фаза 3 → Фаза 4 = **MVP готов!**

## 📁 Структура проекта

```
claude-telegram/
├── README.md                    # Этот файл
├── PROJECT_OVERVIEW.md          # Обзор проекта
├── docs/
│   ├── DEVELOPMENT_PLAN.md      # План разработки
│   └── phases/                  # Фазы разработки
│       ├── PHASE_01_INFRASTRUCTURE.md
│       ├── PHASE_02_BASIC_BOT.md
│       ├── PHASE_03_CLAUDE_INTEGRATION.md
│       ├── PHASE_04_FILE_SYSTEM.md
│       ├── PHASE_05_SIMPLE_MONITORING.md
│       ├── PHASE_07_AUTOMATION.md
│       ├── PHASE_08_INTEGRATIONS.md
│       ├── PHASE_09_ADDITIONAL_FEATURES.md
│       └── PHASE_10_FINALIZATION.md
└── (исходный код будет создан в процессе разработки)
```

## 🎯 MVP (Минимальный продукт)

**Готов после Фазы 4 (2 месяца):**
- ✅ Базовый бот с аутентификацией
- ✅ Работа с Claude CLI
- ✅ Управление файлами
- ✅ Базовая безопасность

## 🔒 Безопасность

- Шифрование API ключей (AES-256)
- Path validation (защита от path traversal)
- Blacklist/Whitelist директорий
- Система подтверждений (5 уровней)
- Аудит всех действий
- Rate limiting

## 📈 Метрики успеха

- Uptime > 99%
- Response time < 2 сек
- Error rate < 1%
- Test coverage > 80%

## 🤝 Команда

**Минимум:** 1 Backend разработчик (Python)  
**Оптимально:** 1-2 Backend + 1 DevOps (part-time)

## 📝 Статус проекта

**Текущий этап:** ✅ Планирование завершено  
**Следующий шаг:** Начать Фазу 1 (Инфраструктура)

## 📞 Документация

Вся документация находится в папке `docs/`:
- [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) - Обзор
- [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md) - План
- [docs/phases/](docs/phases/) - Фазы разработки

---

**Версия:** 1.0  
**Дата:** 2026-05-03  
**Статус:** Готово к разработке! 🚀
