# Фаза 6: Простой мониторинг и алертинг

**Длительность:** 1-2 недели  
**Цель:** Базовый мониторинг Docker контейнеров и простые алерты

## Упрощенная архитектура

Всё работает в Docker Compose на одной машине:
- Telegram Bot (Python)
- PostgreSQL (один контейнер)
- Redis (один контейнер)
- Простой мониторинг без Prometheus/Grafana

## Задачи

### 6.1 Docker мониторинг (3-4 дня)

#### Мониторинг своих контейнеров
- [ ] Создать `src/services/simple_monitor_service.py`
- [ ] Использовать Docker SDK для Python
- [ ] Мониторинг контейнеров проекта:
  - bot
  - postgres
  - redis
- [ ] Статус контейнеров (running/stopped)
- [ ] CPU и Memory usage
- [ ] Uptime

#### Команда /docker_status
- [ ] Handler для `/docker_status`
- [ ] Список контейнеров проекта
- [ ] Статус каждого
- [ ] Использование ресурсов
- [ ] Простой текстовый вывод

#### Команда /docker_logs
- [ ] `/docker_logs <container>` - логи контейнера
- [ ] Последние 50 строк
- [ ] Простой текстовый вывод

#### Команда /docker_restart
- [ ] `/docker_restart <container>` - перезапуск (Admin only)
- [ ] Подтверждение
- [ ] Только для контейнеров проекта

### 6.2 Простые алерты (2-3 дня)

#### Базовые проверки
- [ ] Проверка каждые 5 минут:
  - Контейнеры запущены?
  - PostgreSQL доступна?
  - Redis доступен?
  - Disk space > 10%?
  - Memory < 90%?

#### Уведомления в Telegram
- [ ] Отправка сообщения админу при проблеме
- [ ] Простой текст с описанием проблемы
- [ ] Кнопка "Перезапустить" для контейнеров

#### Команда /health
- [ ] Handler для `/health`
- [ ] Проверка всех сервисов
- [ ] Зеленый/красный статус
- [ ] Простой вывод

### 6.3 Логи и история (2 дня)

#### Простое логирование
- [ ] Логи в файлы
- [ ] Ротация логов (daily)
- [ ] Хранение 7 дней
- [ ] Команда `/logs` для просмотра

#### История команд
- [ ] Сохранение в PostgreSQL
- [ ] Команда `/history` - последние 20 команд
- [ ] Кто, что, когда

### 6.4 Backup (2 дня)

#### Простой backup
- [ ] Backup PostgreSQL (pg_dump)
- [ ] Backup конфигураций
- [ ] Сохранение в `/backups`
- [ ] Команда `/backup` - создать backup
- [ ] Команда `/backup_list` - список backups
- [ ] Автоматический backup раз в день

#### Restore
- [ ] Команда `/restore <backup_id>`
- [ ] Подтверждение Level 4
- [ ] Восстановление из backup

### 6.5 Простая статистика (1-2 дня)

#### Счетчики в Redis
- [ ] Количество запросов
- [ ] Количество токенов Claude
- [ ] Стоимость
- [ ] Ошибки

#### Команда /stats
- [ ] Статистика за сегодня/неделю/месяц
- [ ] Простой текстовый вывод
- [ ] Топ команд
- [ ] Топ пользователей

### 6.6 Тестирование (1 день)

#### Базовые тесты
- [ ] Тесты мониторинга
- [ ] Тесты алертов
- [ ] Тесты backup/restore

## Минимальные требования

**Сервер:**
- 2 CPU cores
- 4 GB RAM
- 20 GB disk
- Ubuntu 20.04+

**Docker Compose:**
```yaml
version: '3.8'
services:
  bot:
    build: .
    restart: always
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs
      - ./backups:/app/backups
  
  postgres:
    image: postgres:15-alpine
    restart: always
    environment:
      POSTGRES_DB: claude_bot
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

## Структура кода

```python
# src/services/simple_monitor_service.py
import docker
import psutil

class SimpleMonitorService:
    def __init__(self):
        self.docker_client = docker.from_env()
    
    async def check_health(self):
        health = {
            'containers': await self.check_containers(),
            'postgres': await self.check_postgres(),
            'redis': await self.check_redis(),
            'disk': await self.check_disk(),
            'memory': await self.check_memory()
        }
        return health
    
    async def check_containers(self):
        containers = self.docker_client.containers.list()
        return {c.name: c.status for c in containers}
    
    async def check_disk(self):
        disk = psutil.disk_usage('/')
        return disk.percent < 90  # OK if < 90%
    
    async def send_alert_if_needed(self, health):
        if not all(health.values()):
            await self.send_telegram_alert(health)
```

## Критерии завершения

- [ ] Docker мониторинг работает
- [ ] Простые алерты работают
- [ ] Логи сохраняются
- [ ] Backup/restore работает
- [ ] Статистика собирается
- [ ] Всё работает в Docker Compose

## Следующая фаза

После завершения простого мониторинга переходим к **Фазе 7: Автоматизация**
