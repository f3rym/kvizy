# Фаза 5: Простой мониторинг (упрощенная)

**Длительность:** 1 неделя  
**Цель:** Базовый мониторинг без сложных систем

## Упрощенный подход

Минимальный функционал:
- Мониторинг своих Docker контейнеров
- Простые алерты в Telegram
- Базовая статистика
- Без Prometheus/Grafana
- Без ELK Stack

## Задачи

### 5.1 Мониторинг системы (2 дня)

#### src/services/monitor_service.py
```python
import psutil
import docker

class MonitorService:
    def __init__(self):
        self.docker_client = docker.from_env()
    
    async def get_system_stats(self):
        return {
            'cpu': psutil.cpu_percent(interval=1),
            'memory': psutil.virtual_memory().percent,
            'disk': psutil.disk_usage('/').percent
        }
    
    async def get_docker_stats(self):
        containers = self.docker_client.containers.list()
        stats = []
        for c in containers:
            stats.append({
                'name': c.name,
                'status': c.status,
                'cpu': self._get_cpu_usage(c),
                'memory': self._get_memory_usage(c)
            })
        return stats
```

#### Команда /status
```python
@router.message(Command("status"))
async def status_handler(message: Message):
    stats = await monitor_service.get_system_stats()
    docker_stats = await monitor_service.get_docker_stats()
    
    text = f"""
📊 Статус системы

💻 Система:
CPU: {stats['cpu']}%
Memory: {stats['memory']}%
Disk: {stats['disk']}%

🐳 Docker:
"""
    for c in docker_stats:
        emoji = "🟢" if c['status'] == 'running' else "🔴"
        text += f"{emoji} {c['name']}: {c['status']}\n"
    
    await message.answer(text)
```

- [ ] Команда `/status`
- [ ] Системные метрики
- [ ] Docker контейнеры
- [ ] Простой текстовый вывод

### 5.2 Простые алерты (2 дня)

#### Background task для проверок
```python
async def health_check_task():
    while True:
        try:
            # Проверка системы
            stats = await monitor_service.get_system_stats()
            
            if stats['disk'] > 90:
                await send_alert("⚠️ Диск заполнен на 90%!")
            
            if stats['memory'] > 90:
                await send_alert("⚠️ Память заполнена на 90%!")
            
            # Проверка контейнеров
            containers = docker_client.containers.list(all=True)
            for c in containers:
                if c.status != 'running':
                    await send_alert(f"🔴 Контейнер {c.name} не запущен!")
        
        except Exception as e:
            logging.error(f"Health check error: {e}")
        
        await asyncio.sleep(300)  # Каждые 5 минут
```

#### Отправка алертов
```python
async def send_alert(message: str):
    # Отправить всем админам
    admins = await db.fetch("SELECT telegram_id FROM users WHERE role = 'admin'")
    for admin in admins:
        await bot.send_message(admin['telegram_id'], message)
```

- [ ] Background task для проверок
- [ ] Проверка каждые 5 минут
- [ ] Алерты в Telegram админам
- [ ] Простые условия (disk > 90%, memory > 90%, контейнер down)

### 5.3 Логи (1 день)

#### Команда /logs
```python
@router.message(Command("logs"))
async def logs_handler(message: Message):
    # Последние 50 строк из лог файла
    with open('logs/bot.log', 'r') as f:
        lines = f.readlines()[-50:]
    
    text = "📋 Последние логи:\n\n"
    text += "".join(lines)
    
    await message.answer(text)
```

- [ ] Команда `/logs` - последние 50 строк
- [ ] Команда `/logs <container>` - логи Docker контейнера

### 5.4 Backup (2 дня)

#### Простой backup PostgreSQL
```python
import subprocess
from datetime import datetime

async def backup_database():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"/app/backups/db_{timestamp}.sql"
    
    cmd = [
        "pg_dump",
        "-h", "postgres",
        "-U", "postgres",
        "-d", "claude_bot",
        "-f", backup_file
    ]
    
    subprocess.run(cmd, check=True)
    return backup_file
```

#### Команды
- [ ] `/backup` - создать backup
- [ ] `/backup_list` - список backups
- [ ] `/restore <id>` - восстановить (Admin only)

#### Автоматический backup
- [ ] Cron задача: каждый день в 3:00
- [ ] Хранение последних 7 backups
- [ ] Удаление старых

### 5.5 Статистика (1 день)

#### Простые счетчики в Redis
```python
async def track_command(user_id: int, command: str):
    # Общие счетчики
    await redis.incr("stats:total_commands")
    await redis.incr(f"stats:command:{command}")
    
    # По пользователю
    await redis.incr(f"stats:user:{user_id}:commands")
```

#### Команда /stats
```python
@router.message(Command("stats"))
async def stats_handler(message: Message):
    total = await redis.get("stats:total_commands")
    
    text = f"""
📈 Статистика

Всего команд: {total}

Топ команд:
"""
    
    # Топ 5 команд
    commands = await redis.keys("stats:command:*")
    top = []
    for cmd in commands:
        count = await redis.get(cmd)
        top.append((cmd.split(':')[-1], int(count)))
    
    top.sort(key=lambda x: x[1], reverse=True)
    
    for cmd, count in top[:5]:
        text += f"/{cmd}: {count}\n"
    
    await message.answer(text)
```

- [ ] Команда `/stats`
- [ ] Общая статистика
- [ ] Топ команд
- [ ] Статистика по пользователю

### 5.6 Тестирование (1 день)

#### Тесты
```python
@pytest.mark.asyncio
async def test_system_stats():
    service = MonitorService()
    stats = await service.get_system_stats()
    assert 'cpu' in stats
    assert 'memory' in stats
    assert 'disk' in stats
```

- [ ] Тесты мониторинга
- [ ] Тесты backup
- [ ] Тесты статистики

## Структура кода

```
src/
├── services/
│   ├── monitor_service.py
│   ├── backup_service.py
│   └── stats_service.py
└── bot/
    └── handlers/
        └── monitoring.py
```

## Минимальные требования

Дополнительные пакеты:
```
psutil==5.9.6
docker==7.0.0
```

## Критерии завершения

- [ ] Мониторинг системы работает
- [ ] Docker мониторинг работает
- [ ] Алерты отправляются
- [ ] Логи доступны
- [ ] Backup/restore работает
- [ ] Статистика собирается
- [ ] Тесты проходят

## Следующая фаза

После завершения мониторинга переходим к **Фазе 7: Автоматизация**

---

**Примечание:** Фазы 6 (Кластерный мониторинг) пропускаем, так как работаем без Kubernetes.
