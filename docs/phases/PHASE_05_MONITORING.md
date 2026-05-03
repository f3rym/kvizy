# Фаза 5: Мониторинг

**Длительность:** 3 недели  
**Цель:** Реализация системного мониторинга, мониторинга Claude API и алертинга

## Задачи

### 5.1 Системный мониторинг (4-5 дней)

#### Сбор метрик
- [ ] Создать `src/services/monitor_service.py`
- [ ] CPU usage (psutil)
- [ ] Memory usage (total, available, percent)
- [ ] Disk space (total, used, free)
- [ ] Network I/O (bytes sent/received)
- [ ] Process count
- [ ] Load average
- [ ] Uptime

#### Команда /status
- [ ] Handler для `/status`
- [ ] Текущие метрики системы
- [ ] Форматированный вывод
- [ ] Цветовые индикаторы (🟢🟡🔴)
- [ ] Графики (ASCII art или изображения)
- [ ] Обновление в реальном времени (inline update)

#### Мониторинг сервисов
- [ ] PostgreSQL status
- [ ] Redis status
- [ ] MongoDB status
- [ ] RabbitMQ status
- [ ] Bot status
- [ ] API status
- [ ] Health checks для каждого сервиса

#### Активные сессии
- [ ] Количество активных пользователей
- [ ] Список активных сессий
- [ ] Время последней активности
- [ ] Команда `/sessions` для просмотра

#### Очереди задач
- [ ] Размер очереди Celery
- [ ] Pending tasks
- [ ] Running tasks
- [ ] Failed tasks
- [ ] Worker status
- [ ] Команда `/queue_status`

### 5.2 Мониторинг Claude API (3-4 дня)

#### Метрики API
- [ ] Создать `src/services/api_metrics_service.py`
- [ ] Request count (total, today, week, month)
- [ ] Token usage:
  - Input tokens
  - Output tokens
  - Total tokens
- [ ] Cost calculation по моделям
- [ ] Response time (avg, min, max, p95, p99)
- [ ] Error rate
- [ ] Success rate
- [ ] Cache hit rate

#### Команда /api_status
- [ ] Handler для `/api_status`
- [ ] Текущий статус API
- [ ] Использование за период
- [ ] Стоимость
- [ ] Rate limit status
- [ ] Графики использования
- [ ] Прогноз расходов

#### Rate limit tracking
- [ ] Отслеживание лимитов Claude API
- [ ] Предупреждение при приближении к лимиту
- [ ] Автоматическое throttling
- [ ] Очередь запросов при достижении лимита

#### Cost tracking
- [ ] Расчет стоимости по моделям:
  - Opus: $15/$75 per 1M tokens
  - Sonnet: $3/$15 per 1M tokens
  - Haiku: $0.25/$1.25 per 1M tokens
- [ ] Дневной/недельный/месячный бюджет
- [ ] Алерты при превышении бюджета
- [ ] Per-user cost tracking
- [ ] Команда `/cost_report`

### 5.3 Prometheus интеграция (3-4 дня)

#### Экспорт метрик
- [ ] Установить prometheus-client
- [ ] Создать `/metrics` endpoint в FastAPI
- [ ] Экспорт системных метрик
- [ ] Экспорт application метрик:
  - Request count
  - Response time
  - Error count
  - Active users
  - Queue length
- [ ] Экспорт Claude API метрик
- [ ] Custom metrics

#### Prometheus конфигурация
- [ ] Создать `config/prometheus.yml`
- [ ] Настроить scrape configs
- [ ] Настроить retention
- [ ] Настроить alerting rules

#### Метрики приложения
```python
from prometheus_client import Counter, Histogram, Gauge

request_count = Counter('bot_requests_total', 'Total requests', ['command', 'user_role'])
response_time = Histogram('bot_response_seconds', 'Response time')
active_users = Gauge('bot_active_users', 'Active users')
claude_tokens = Counter('claude_tokens_total', 'Claude tokens', ['type', 'model'])
```

### 5.4 Grafana дашборды (3-4 дня)

#### Установка и настройка
- [ ] Установить Grafana
- [ ] Подключить Prometheus data source
- [ ] Настроить authentication
- [ ] Настроить permissions

#### System Dashboard
- [ ] CPU usage graph
- [ ] Memory usage graph
- [ ] Disk usage graph
- [ ] Network I/O graph
- [ ] Load average
- [ ] Process count

#### Application Dashboard
- [ ] Request rate
- [ ] Response time (p50, p95, p99)
- [ ] Error rate
- [ ] Active users
- [ ] Queue length
- [ ] Top commands
- [ ] Top users

#### Claude API Dashboard
- [ ] Request count by model
- [ ] Token usage by model
- [ ] Cost over time
- [ ] Response time by model
- [ ] Error rate by model
- [ ] Cache hit rate

#### Alerts Dashboard
- [ ] Active alerts
- [ ] Alert history
- [ ] Alert severity distribution
- [ ] MTTR (Mean Time To Resolution)

#### Команда /dashboard
- [ ] Handler для `/dashboard`
- [ ] Генерация snapshot дашборда
- [ ] Отправка изображения в Telegram
- [ ] Ссылка на live dashboard

### 5.5 Алертинг (4-5 дней)

#### Alert Service
- [ ] Создать `src/services/alert_service.py`
- [ ] Определение alert rules
- [ ] Проверка условий
- [ ] Отправка уведомлений
- [ ] Escalation logic
- [ ] Alert grouping
- [ ] Alert deduplication

#### Типы алертов

**Критические:**
- [ ] API key expired/invalid
- [ ] Disk space < 10%
- [ ] Memory usage > 90%
- [ ] Service down
- [ ] Database connection lost
- [ ] Security breach attempt
- [ ] Error rate > 10%

**Предупреждения:**
- [ ] High error rate (> 5%)
- [ ] Slow response time (> 30s)
- [ ] Token limit approaching (> 80%)
- [ ] Disk space < 20%
- [ ] Memory usage > 75%
- [ ] Unusual activity pattern
- [ ] Cost threshold approaching

**Информационные:**
- [ ] Daily usage report
- [ ] Weekly summary
- [ ] Cost threshold reached
- [ ] New user registered
- [ ] Backup completed
- [ ] Update available

#### Команда /alerts
- [ ] Handler для `/alerts`
- [ ] Список активных алертов
- [ ] История алертов
- [ ] Фильтрация по severity
- [ ] Acknowledge alert
- [ ] Resolve alert
- [ ] Mute alert

#### Каналы уведомлений

**Telegram:**
- [ ] Отправка в личные сообщения
- [ ] Отправка в группу (для команды)
- [ ] Форматирование сообщений
- [ ] Inline кнопки для действий

**Email:**
- [ ] SMTP настройка
- [ ] HTML шаблоны
- [ ] Отправка критических алертов
- [ ] Digest emails

**Webhook:**
- [ ] Интеграция со Slack
- [ ] Интеграция с Discord
- [ ] Интеграция с Microsoft Teams
- [ ] Custom webhooks

**SMS (опционально):**
- [ ] Интеграция с Twilio
- [ ] Только для критических алертов
- [ ] Rate limiting для SMS

**PagerDuty (опционально):**
- [ ] Интеграция с PagerDuty
- [ ] Escalation policies
- [ ] On-call schedules

#### Alert Rules
```yaml
# config/alert_rules.yml
alerts:
  - name: high_memory_usage
    condition: memory_percent > 90
    severity: critical
    channels: [telegram, email, pagerduty]
    message: "Memory usage is critically high: {value}%"
  
  - name: api_cost_high
    condition: daily_cost > 100
    severity: warning
    channels: [telegram, email]
    message: "Daily API cost exceeded $100: ${value}"
```

### 5.6 Логирование (2-3 дня)

#### Structured logging
- [ ] JSON формат логов
- [ ] Correlation ID для запросов
- [ ] Контекстная информация:
  - user_id
  - command
  - timestamp
  - duration
  - result

#### Log levels
- [ ] DEBUG - детальная информация
- [ ] INFO - общая информация
- [ ] WARNING - предупреждения
- [ ] ERROR - ошибки
- [ ] CRITICAL - критические ошибки

#### Команда /logs
- [ ] Handler для `/logs`
- [ ] Просмотр последних логов
- [ ] Фильтрация по уровню
- [ ] Фильтрация по пользователю
- [ ] Фильтрация по времени
- [ ] Поиск по тексту
- [ ] Экспорт логов

#### Log rotation
- [ ] Ротация по размеру (100MB)
- [ ] Ротация по времени (daily)
- [ ] Сжатие старых логов
- [ ] Удаление старых логов (> 30 дней)

### 5.7 ELK Stack интеграция (опционально, 3-4 дня)

#### Elasticsearch
- [ ] Установка Elasticsearch
- [ ] Создание индексов
- [ ] Mapping для логов
- [ ] Retention policy

#### Logstash
- [ ] Установка Logstash
- [ ] Input configuration (file, redis)
- [ ] Filters (grok, json)
- [ ] Output to Elasticsearch

#### Kibana
- [ ] Установка Kibana
- [ ] Создание index patterns
- [ ] Создание visualizations
- [ ] Создание dashboards
- [ ] Saved searches

#### Filebeat (альтернатива Logstash)
- [ ] Установка Filebeat
- [ ] Конфигурация inputs
- [ ] Отправка в Elasticsearch

### 5.8 Tracing (опционально, 2-3 дня)

#### Jaeger интеграция
- [ ] Установка Jaeger
- [ ] Инструментация кода
- [ ] Trace context propagation
- [ ] Span creation для операций
- [ ] Tags и logs в spans

#### Distributed tracing
- [ ] Трейсинг через все сервисы
- [ ] Bot → Service → Database
- [ ] Bot → Claude CLI
- [ ] API → Service → Database

### 5.9 Error tracking (2 дня)

#### Sentry интеграция
- [ ] Настройка Sentry SDK
- [ ] Автоматический capture exceptions
- [ ] Breadcrumbs
- [ ] User context
- [ ] Tags (environment, version)
- [ ] Release tracking

#### Error grouping
- [ ] Группировка похожих ошибок
- [ ] Fingerprinting
- [ ] Issue tracking
- [ ] Notifications в Telegram

### 5.10 Тестирование (2 дня)

#### Unit тесты
- [ ] Тесты для monitor_service
- [ ] Тесты для alert_service
- [ ] Тесты для metrics_service
- [ ] Mock внешних зависимостей

#### Integration тесты
- [ ] Тесты сбора метрик
- [ ] Тесты алертинга
- [ ] Тесты Prometheus экспорта
- [ ] Тесты уведомлений

#### Load тесты
- [ ] Нагрузочное тестирование
- [ ] Проверка метрик под нагрузкой
- [ ] Проверка алертов под нагрузкой

## Структура кода

```python
# src/services/monitor_service.py
import psutil
from prometheus_client import Gauge

class MonitorService:
    def __init__(self):
        self.cpu_gauge = Gauge('system_cpu_percent', 'CPU usage')
        self.memory_gauge = Gauge('system_memory_percent', 'Memory usage')
        self.disk_gauge = Gauge('system_disk_percent', 'Disk usage')
    
    async def collect_metrics(self):
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        
        self.cpu_gauge.set(cpu)
        self.memory_gauge.set(memory)
        self.disk_gauge.set(disk)
        
        return {
            'cpu': cpu,
            'memory': memory,
            'disk': disk
        }

# src/services/alert_service.py
class AlertService:
    async def check_alerts(self):
        metrics = await monitor_service.collect_metrics()
        
        if metrics['memory'] > 90:
            await self.send_alert(
                severity='critical',
                message=f"Memory usage critical: {metrics['memory']}%",
                channels=['telegram', 'email', 'pagerduty']
            )
    
    async def send_alert(self, severity, message, channels):
        for channel in channels:
            if channel == 'telegram':
                await self.send_telegram_alert(severity, message)
            elif channel == 'email':
                await self.send_email_alert(severity, message)
```

## Критерии завершения фазы

- [ ] Системный мониторинг работает
- [ ] Claude API мониторинг работает
- [ ] Prometheus экспортирует метрики
- [ ] Grafana дашборды созданы
- [ ] Алертинг настроен и работает
- [ ] Все каналы уведомлений работают
- [ ] Логирование настроено
- [ ] Error tracking работает
- [ ] Тесты написаны и проходят

## Метрики успеха

- Сбор метрик каждые 10 секунд
- Алерты отправляются < 1 минуты после события
- 100% критических алертов доставляются
- Grafana дашборды обновляются в реальном времени
- 0 пропущенных критических событий

## Риски и митигация

**Риск:** Перегрузка системы мониторингом  
**Митигация:** Оптимизация частоты сбора, агрегация метрик

**Риск:** Alert fatigue  
**Митигация:** Правильные thresholds, группировка, deduplication

**Риск:** Потеря метрик  
**Митигация:** Буферизация, retry механизм, persistence

## Следующая фаза

После завершения мониторинга переходим к **Фазе 6: Кластерный мониторинг**
