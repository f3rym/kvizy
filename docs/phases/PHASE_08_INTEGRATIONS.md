# Фаза 8: Базовые интеграции

**Длительность:** 2 недели  
**Цель:** Простые интеграции с Git и базами данных

## Задачи

### 8.1 Git интеграция (4-5 дней)

#### Git команды
- [ ] Создать `src/services/git_service.py`
- [ ] Использовать GitPython
- [ ] Работа с локальными репозиториями

#### Базовые команды
- [ ] `/git status` - статус репозитория
- [ ] `/git log` - последние 10 коммитов
- [ ] `/git diff` - изменения
- [ ] `/git branch` - список веток
- [ ] `/git checkout <branch>` - переключить ветку

#### Команды изменений (с подтверждением)
- [ ] `/git add <files>` - добавить файлы
- [ ] `/git commit "<message>"` - создать коммит
- [ ] `/git push` - отправить на remote
- [ ] `/git pull` - получить изменения
- [ ] Подтверждение Level 2 для push

#### Информация
- [ ] `/git remote` - список remotes
- [ ] `/git show <commit>` - показать коммит
- [ ] `/git blame <file>` - кто изменял строки

### 8.2 GitHub интеграция (опционально, 2-3 дня)

#### GitHub API
- [ ] Использовать PyGithub
- [ ] Personal access token
- [ ] Базовые операции

#### Команды
- [ ] `/github repos` - список репозиториев
- [ ] `/github issues` - список issues
- [ ] `/github prs` - список pull requests
- [ ] `/github create_issue "<title>" "<body>"` - создать issue

#### Webhooks (опционально)
- [ ] Endpoint `/webhooks/github`
- [ ] Уведомления о push
- [ ] Уведомления о PR
- [ ] Уведомления о issues

### 8.3 Database интеграция (3-4 дней)

#### PostgreSQL queries
- [ ] Создать `src/services/db_query_service.py`
- [ ] Безопасное выполнение запросов
- [ ] Только SELECT запросы для обычных пользователей
- [ ] INSERT/UPDATE/DELETE только для Admin

#### Команда /db
- [ ] `/db query "<sql>"` - выполнить запрос
- [ ] Валидация SQL
- [ ] Ограничение результатов (100 строк)
- [ ] Форматированный вывод (таблица)
- [ ] Экспорт в CSV

#### Безопасность
- [ ] Запрет DROP/TRUNCATE
- [ ] Запрет изменения системных таблиц
- [ ] Timeout для запросов (30 сек)
- [ ] Логирование всех запросов

#### Информация о БД
- [ ] `/db tables` - список таблиц
- [ ] `/db describe <table>` - структура таблицы
- [ ] `/db size` - размер БД
- [ ] `/db stats` - статистика

### 8.4 Redis интеграция (1-2 дня)

#### Redis команды
- [ ] `/redis get <key>` - получить значение
- [ ] `/redis set <key> <value>` - установить (Admin)
- [ ] `/redis del <key>` - удалить (Admin)
- [ ] `/redis keys <pattern>` - поиск ключей
- [ ] `/redis info` - информация о Redis

#### Cache management
- [ ] `/cache clear` - очистить весь кэш (Admin)
- [ ] `/cache stats` - статистика кэша
- [ ] Просмотр кэшированных данных

### 8.5 Webhook интеграции (2-3 дня)

#### Outgoing webhooks
- [ ] Создать `src/services/webhook_service.py`
- [ ] Отправка HTTP POST запросов
- [ ] Retry механизм
- [ ] Timeout

#### Команда /webhook
- [ ] `/webhook create <name> <url>` - создать webhook
- [ ] `/webhook list` - список webhooks
- [ ] `/webhook test <name>` - тестовый запрос
- [ ] `/webhook delete <name>` - удалить

#### Incoming webhooks
- [ ] Endpoint `/webhooks/incoming/<id>`
- [ ] Обработка входящих запросов
- [ ] Выполнение команд
- [ ] Уведомления

#### Интеграция со Slack (опционально)
- [ ] Отправка сообщений в Slack
- [ ] Webhook URL
- [ ] Форматирование сообщений

### 8.6 Email уведомления (опционально, 1-2 дня)

#### SMTP настройка
- [ ] Конфигурация SMTP
- [ ] Отправка email
- [ ] HTML шаблоны

#### Команда /email
- [ ] `/email send <to> "<subject>" "<body>"` - отправить
- [ ] `/email test` - тестовое письмо
- [ ] Отправка отчетов по email

### 8.7 Тестирование (1 день)

#### Тесты
- [ ] Тесты Git операций
- [ ] Тесты DB queries
- [ ] Тесты webhooks
- [ ] Mock внешних сервисов

## Структура кода

```python
# src/services/git_service.py
from git import Repo

class GitService:
    def __init__(self, repo_path: str):
        self.repo = Repo(repo_path)
    
    async def get_status(self):
        return {
            'branch': self.repo.active_branch.name,
            'modified': [item.a_path for item in self.repo.index.diff(None)],
            'untracked': self.repo.untracked_files
        }
    
    async def commit(self, message: str, files: list):
        self.repo.index.add(files)
        commit = self.repo.index.commit(message)
        return commit.hexsha

# src/services/db_query_service.py
class DBQueryService:
    FORBIDDEN_KEYWORDS = ['DROP', 'TRUNCATE', 'DELETE', 'UPDATE', 'INSERT']
    
    async def execute_query(self, sql: str, user: User):
        # Validate SQL
        if user.role != 'admin':
            if any(kw in sql.upper() for kw in self.FORBIDDEN_KEYWORDS):
                raise PermissionError("Only SELECT allowed")
        
        # Execute with timeout
        async with asyncio.timeout(30):
            result = await db.execute(sql)
        
        return result.fetchmany(100)  # Limit results
```

## Минимальные требования

Дополнительные пакеты:
```
gitpython==3.1.40
PyGithub==2.1.1  # опционально
aiosmtplib==3.0.1  # опционально
```

## Критерии завершения

- [ ] Git команды работают
- [ ] Database queries работают
- [ ] Redis команды работают
- [ ] Webhooks работают
- [ ] Тесты проходят

## Следующая фаза

После завершения интеграций переходим к **Фазе 9: Дополнительные фичи**
