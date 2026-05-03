# Фаза 7: Автоматизация

**Длительность:** 1-2 недели  
**Цель:** Простая автоматизация через cron и базовые триггеры

## Задачи

### 7.1 Cron задачи (3-4 дня)

#### Простой планировщик
- [ ] Создать `src/services/scheduler_service.py`
- [ ] Использовать APScheduler (Python)
- [ ] Хранение задач в PostgreSQL
- [ ] Запуск в фоне

#### Команда /cron
- [ ] `/cron add "<schedule>" "<command>"` - добавить задачу
  - Пример: `/cron add "0 9 * * *" "/backup"`
  - Пример: `/cron add "*/30 * * * *" "/health"`
- [ ] `/cron list` - список задач
- [ ] `/cron remove <id>` - удалить задачу
- [ ] `/cron pause <id>` - приостановить
- [ ] `/cron resume <id>` - возобновить

#### Cron формат
- [ ] Поддержка стандартного cron формата
- [ ] Валидация расписания
- [ ] Человекочитаемое описание ("каждый день в 9:00")

#### История выполнения
- [ ] Сохранение результатов в БД
- [ ] `/cron history <id>` - история задачи
- [ ] Последние 10 выполнений
- [ ] Статус (success/failed)
- [ ] Время выполнения

### 7.2 Простые триггеры (2-3 дня)

#### File watcher
- [ ] Создать `src/services/watcher_service.py`
- [ ] Использовать watchdog (Python)
- [ ] Мониторинг указанных директорий
- [ ] События: created, modified, deleted

#### Команда /watch
- [ ] `/watch add <path> <command>` - добавить watcher
  - Пример: `/watch add "/app/logs" "/analyze logs"`
- [ ] `/watch list` - список watchers
- [ ] `/watch remove <id>` - удалить watcher

#### Webhook триггеры
- [ ] Endpoint `/webhooks/trigger/<id>`
- [ ] Создание webhook триггера
- [ ] `/trigger create <name> <command>` - создать триггер
- [ ] Получение URL для webhook
- [ ] Выполнение команды при вызове

### 7.3 Простые workflows (2-3 дня)

#### Последовательность команд
- [ ] Создать `src/services/workflow_service.py`
- [ ] Выполнение списка команд по порядку
- [ ] Остановка при ошибке

#### Команда /workflow
- [ ] `/workflow create <name>` - создать workflow
- [ ] Добавление шагов через диалог
- [ ] `/workflow run <name>` - запустить
- [ ] `/workflow list` - список workflows
- [ ] `/workflow delete <name>` - удалить

#### Пример workflow
```
Workflow: daily_report
1. /stats
2. /api_status
3. /health
4. Отправить отчет админу
```

#### Условия (опционально)
- [ ] Простые условия if/else
- [ ] Проверка результата предыдущего шага
- [ ] Пропуск шагов при условии

### 7.4 Уведомления (1-2 дня)

#### Scheduled notifications
- [ ] Отправка уведомлений по расписанию
- [ ] `/notify schedule "<time>" "<message>"`
- [ ] Напоминания
- [ ] Отчеты

#### Recurring notifications
- [ ] Повторяющиеся уведомления
- [ ] Ежедневные отчеты
- [ ] Еженедельные сводки

### 7.5 Автоматические действия (2 дня)

#### Auto-restart
- [ ] Автоматический перезапуск упавших контейнеров
- [ ] Проверка каждые 5 минут
- [ ] Максимум 3 попытки
- [ ] Уведомление админу

#### Auto-cleanup
- [ ] Очистка старых логов (> 7 дней)
- [ ] Очистка старых backups (> 30 дней)
- [ ] Очистка Redis cache
- [ ] Запуск раз в день

#### Auto-backup
- [ ] Автоматический backup каждый день в 3:00
- [ ] Уведомление о результате
- [ ] Проверка успешности

### 7.6 Тестирование (1 день)

#### Тесты
- [ ] Тесты scheduler
- [ ] Тесты watchers
- [ ] Тесты workflows
- [ ] Тесты автоматических действий

## Структура кода

```python
# src/services/scheduler_service.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
    
    async def add_job(self, schedule: str, command: str, user_id: int):
        job = self.scheduler.add_job(
            func=self.execute_command,
            trigger=CronTrigger.from_crontab(schedule),
            args=[command, user_id],
            id=f"job_{user_id}_{int(time.time())}"
        )
        await self.save_job_to_db(job, schedule, command, user_id)
        return job.id
    
    async def execute_command(self, command: str, user_id: int):
        # Execute bot command
        result = await bot.execute_command(command, user_id)
        await self.save_execution_result(result)

# src/services/watcher_service.py
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class WatcherService:
    def __init__(self):
        self.observer = Observer()
        self.watchers = {}
    
    async def add_watcher(self, path: str, command: str, user_id: int):
        handler = CommandHandler(command, user_id)
        self.observer.schedule(handler, path, recursive=True)
        self.observer.start()
```

## Минимальные требования

Дополнительные пакеты:
```
apscheduler==3.10.4
watchdog==3.0.0
```

Без дополнительных сервисов - всё в основном контейнере бота.

## Критерии завершения

- [ ] Cron задачи работают
- [ ] File watchers работают
- [ ] Webhook триггеры работают
- [ ] Workflows выполняются
- [ ] Уведомления отправляются
- [ ] Автоматические действия работают
- [ ] Тесты проходят

## Следующая фаза

После завершения автоматизации переходим к **Фазе 8: Интеграции**
