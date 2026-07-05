# DaVinci

> Local AI Coding Agent — ваш локальный Copilot

## Что это

**DaVinci** — мультиагентная система для помощи в написании кода, работающая полностью локально на Ollama. Вдохновлён архитектурой GitHub Squad.

## Возможности

- **4 специализированных агента**: Architect, Coder, Tester, Reviewer
- **Умный координатор**: анализирует задачу и направляет к нужному агенту
- **Независимый review**: Tester проверяет код Coder'а, Reviewer чинит ошибки
- **Память решений**: `.davinci/decisions.md` — общий мозг команды
- **RAG контекст**: агенты понимают структуру проекта
- **100% локально**: никаких данных в облаке

## Установка

```bash
cd DaVinci
pip install -e .
```

## Требования

- Python 3.11+
- Ollama (запущенный)
- Модель: `qwen2.5:14b` (рекомендуется)

## Использование

```bash
# Инициализация
cd my-project
davinci --init

# Запрос
davinci "Добавь валидацию email в registrations.py"

# Специфичный агент
davinci --agent architect "Спроектируй систему аутентификации"
davinci --agent tester "Напиши тесты для auth модуля"
davinci --agent reviewer "Проверь безопасность app.py"

# Список моделей
davinci --models
```

## Архитектура

```
Пользователь → Coordinator → Agent → LLM (Ollama)
                    ↓
              .davinci/
              decisions.md  (общая память)
              config.yaml   (настройки)
```

### Агенты

| Агент | Роль | Когда вызывается |
|-------|------|-------------------|
| Architect | Проектирует решения | Сложные задачи, "спроектируй", "создай" |
| Coder | Пишет код | По умолчанию |
| Tester | Пишет тесты, проверяет | "тест", "проверь" |
| Reviewer | Ищет баги, проблемы | "ревью", "баг", "ошибк" |

### Pipeline

1. Coordinator анализирует задачу
2. Architect проектирует (если сложно)
3. Coder реализует
4. Tester проверяет (независимо!)
5. Reviewer чинит (если нашёл ошибки)

## Структура

```
DaVinci/
├── davinci/
│   ├── cli.py              # Точка входа
│   ├── coordinator.py      # Роутер + pipeline
│   ├── config.py           # Конфигурация
│   ├── agents/
│   │   ├── base.py         # BaseAgent ABC
│   │   ├── architect.py    # Проектирует
│   │   ├── coder.py        # Пишет код
│   │   ├── tester.py       # Тестирует
│   │   └── reviewer.py     # Ревьюит
│   ├── llm/
│   │   └── client.py       # Ollama client
│   ├── memory/
│   │   ├── decisions.py    # decisions.md
│   │   └── context.py      # Контекст проекта
│   └── tools/
│       └── file_tools.py   # Файловые операции
├── tests/                  # 28 тестов
└── pyproject.toml
```

## Ключевые паттерны

### Drop-box Memory (из Squad)
Каждое решение записывается в `.davinci/decisions.md` — версионируется с кодом.

### Independent Review (из Squad)
Tester проверяет Coder'а. Если ошибки — Reviewer чинит (не Coder!). Независимость контекстов.

### Context Replication
Каждый агент получает полный контекст проекта через ContextManager.

## Тесты

```bash
pytest tests/ -v
```

## Лицензия

MIT
