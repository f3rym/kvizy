# Фаза 9: Дополнительные фичи

**Длительность:** 1-2 недели  
**Цель:** Полезные дополнительные возможности

## Задачи

### 9.1 Шаблоны и сниппеты (2-3 дня)

#### Шаблоны промптов
- [ ] Создать `src/services/template_service.py`
- [ ] Хранение шаблонов в БД
- [ ] Переменные в шаблонах: `{variable}`

#### Команда /template
- [ ] `/template create <name> "<text>"` - создать шаблон
  - Пример: `/template create code_review "Review this code: {code}"`
- [ ] `/template list` - список шаблонов
- [ ] `/template use <name>` - использовать шаблон
- [ ] `/template delete <name>` - удалить

#### Использование шаблонов
- [ ] Подстановка переменных
- [ ] Интерактивный ввод значений
- [ ] Отправка в Claude

#### Предустановленные шаблоны
- [ ] Code review
- [ ] Bug fix
- [ ] Documentation
- [ ] Test generation
- [ ] Refactoring

### 9.2 Макросы (2 дня)

#### Запись макросов
- [ ] `/macro record <name>` - начать запись
- [ ] Запись последовательности команд
- [ ] `/macro stop` - остановить запись
- [ ] Сохранение в БД

#### Воспроизведение
- [ ] `/macro play <name>` - воспроизвести
- [ ] `/macro list` - список макросов
- [ ] `/macro delete <name>` - удалить

#### Параметры макросов
- [ ] Переменные в макросах
- [ ] Запрос значений при воспроизведении

### 9.3 Экспорт и импорт (2 дня)

#### Экспорт данных
- [ ] `/export config` - экспорт конфигурации
- [ ] `/export templates` - экспорт шаблонов
- [ ] `/export macros` - экспорт макросов
- [ ] Формат JSON
- [ ] Отправка файла в Telegram

#### Импорт данных
- [ ] `/import` - начать импорт
- [ ] Загрузка JSON файла
- [ ] Валидация данных
- [ ] Импорт в БД
- [ ] Подтверждение

### 9.4 Поиск и фильтрация (2 дня)

#### Поиск по истории
- [ ] `/search "<query>"` - поиск по истории команд
- [ ] Поиск по диалогам с Claude
- [ ] Поиск по файлам
- [ ] Результаты с контекстом

#### Фильтры
- [ ] Фильтрация по дате
- [ ] Фильтрация по пользователю (Admin)
- [ ] Фильтрация по типу команды
- [ ] Сортировка результатов

### 9.5 Избранное (1-2 дня)

#### Favorites
- [ ] `/fav add <type> <id>` - добавить в избранное
  - Файлы
  - Директории
  - Команды
  - Диалоги
- [ ] `/fav list` - список избранного
- [ ] `/fav remove <id>` - удалить
- [ ] Быстрый доступ к избранному

### 9.6 Заметки (1-2 дня)

#### Простые заметки
- [ ] `/note add "<text>"` - добавить заметку
- [ ] `/note list` - список заметок
- [ ] `/note view <id>` - просмотр заметки
- [ ] `/note delete <id>` - удалить
- [ ] `/note search "<query>"` - поиск

#### Теги
- [ ] Добавление тегов к заметкам
- [ ] Фильтрация по тегам
- [ ] `/note tag <id> <tag>` - добавить тег

### 9.7 Быстрые команды (1 день)

#### Алиасы
- [ ] `/alias create <name> "<command>"` - создать алиас
  - Пример: `/alias create s "/status"`
- [ ] `/alias list` - список алиасов
- [ ] `/alias delete <name>` - удалить
- [ ] Использование: просто написать алиас

#### Shortcuts
- [ ] Быстрые кнопки для частых команд
- [ ] Настраиваемое главное меню
- [ ] Персональные shortcuts

### 9.8 Мультиязычность (опционально, 2 дня)

#### Поддержка языков
- [ ] Русский (по умолчанию)
- [ ] Английский
- [ ] Хранение переводов в JSON

#### Команда /language
- [ ] `/language` - выбор языка
- [ ] Inline кнопки с языками
- [ ] Сохранение выбора

#### Переводы
- [ ] Перевод всех сообщений бота
- [ ] Перевод команд (опционально)
- [ ] Перевод справки

### 9.9 Помощь и документация (1 день)

#### Улучшенная справка
- [ ] `/help` - главная справка
- [ ] `/help <command>` - справка по команде
- [ ] Примеры использования
- [ ] Категории команд

#### Интерактивная справка
- [ ] Inline кнопки с категориями
- [ ] Поиск по командам
- [ ] Часто задаваемые вопросы

#### Туториал
- [ ] `/tutorial` - интерактивный туториал
- [ ] Пошаговое знакомство с ботом
- [ ] Для новых пользователей

### 9.10 Тестирование (1 день)

#### Тесты
- [ ] Тесты шаблонов
- [ ] Тесты макросов
- [ ] Тесты экспорта/импорта
- [ ] Тесты поиска

## Структура кода

```python
# src/services/template_service.py
import re

class TemplateService:
    async def create_template(self, name: str, text: str, user_id: int):
        # Find variables in template
        variables = re.findall(r'\{(\w+)\}', text)
        
        await db.execute(
            "INSERT INTO templates (name, text, variables, user_id) VALUES (?, ?, ?, ?)",
            (name, text, json.dumps(variables), user_id)
        )
    
    async def use_template(self, name: str, values: dict):
        template = await self.get_template(name)
        
        # Replace variables
        text = template.text
        for var, value in values.items():
            text = text.replace(f'{{{var}}}', value)
        
        return text

# src/services/macro_service.py
class MacroService:
    def __init__(self):
        self.recording = {}
    
    async def start_recording(self, user_id: int, name: str):
        self.recording[user_id] = {
            'name': name,
            'commands': []
        }
    
    async def record_command(self, user_id: int, command: str):
        if user_id in self.recording:
            self.recording[user_id]['commands'].append(command)
    
    async def stop_recording(self, user_id: int):
        macro = self.recording.pop(user_id)
        await self.save_macro(macro, user_id)
```

## Минимальные требования

Без дополнительных зависимостей - используем существующий стек.

## Критерии завершения

- [ ] Шаблоны работают
- [ ] Макросы работают
- [ ] Экспорт/импорт работает
- [ ] Поиск работает
- [ ] Избранное работает
- [ ] Заметки работают
- [ ] Алиасы работают
- [ ] Справка улучшена
- [ ] Тесты проходят

## Следующая фаза

После завершения дополнительных фич переходим к **Фазе 10: Финализация**
