# DaVinci

> Local AI Coding Agent — ваш локальный Copilot

## Что это

**DaVinci** — мультиагентная система для помощи в написании кода, работающая полностью локально на Ollama. Вдохновлён архитектурой GitHub Squad.

## Возможности

- **4 специализированных агента**: Architect, Coder, Tester, Reviewer
- **Умный координатор**: LLM-based routing определяет лучшего агента
- **Независимый review**: Tester проверяет код Coder'а, Reviewer чинит ошибки
- **RAG контекст**: агенты понимают весь проект через индексацию
- **Память решений**: `.davinci/decisions.md` — общий мозг команды
- **Rich TUI**: progress bars, таблицы, live streaming
- **Веб-дашборд**: работа через браузер
- **100% локально**: никаких данных в облаке

## Установка

### Windows (рекомендуется)
```bash
# Клонируй проект
git clone https://github.com/fanat0976-eng/DaVinci.git
cd DaVinci

# Установи
install.bat
```

### Ручная установка
```bash
pip install -e .
```

### Требования
- Python 3.11+
- Ollama (запущенный)
- Модель: `qwen2.5:14b` (рекомендуется)

## Использование

### CLI
```bash
# Инициализация
cd my-project
davinci --init

# Индексация (RAG)
davinci --index

# Запрос
davinci "Добавь валидацию email в create_user"

# Принудительно указать агента
davinci --agent coder "Исправь баг в utils.py"
davinci --agent tester "Напиши тесты для auth"
davinci --agent reviewer "Проверь безопасность app.py"

# Статус
davinci --status

# Модели
davinci --models
```

### Веб-дашборд
```bash
# Запуск дашборда
davinci --dashboard

# Открой браузер: http://127.0.0.1:8080
```

### Быстрый запуск (Windows)
```bash
# Двойной клик на davinci.bat
davinci.bat "Твоя задача"
```

## Архитектура

```
Пользователь → LLM Router → Agent → LLM (Ollama)
                    ↓
              .davinci/
              decisions.md   (память решений)
              vectors.db     (RAG индекс)
              config.yaml    (настройки)
```

### Агенты

| Агент | Роль | Когда вызывается |
|-------|------|-------------------|
| Architect | Проектирует решения | Сложные задачи, "спроектируй", "создай" |
| Coder | Пишет код | По умолчанию |
| Tester | Пишет тесты, проверяет | "тест", "проверь" |
| Reviewer | Ищет баги, проблемы | "ревью", "баг", "ошибк" |

### Pipeline

1. **Router** (LLM) классифицирует задачу
2. **Architect** проектирует (если сложно)
3. **Coder** реализует
4. **Tester** проверяет (независимо!)
5. **Reviewer** чинит (если нашёл ошибки)

## Структура

```
DaVinci/
├── davinci/
│   ├── cli.py              # Точка входа
│   ├── coordinator.py      # Роутер + pipeline
│   ├── config.py           # Конфигурация
│   ├── dashboard.py        # Веб-дашборд
│   ├── agents/
│   │   ├── base.py         # BaseAgent ABC
│   │   ├── architect.py    # Проектирует
│   │   ├── coder.py        # Пишет код
│   │   ├── tester.py       # Тестирует
│   │   └── reviewer.py     # Ревьюит
│   ├── llm/
│   │   └── client.py       # Ollama client + rate limiting
│   ├── memory/
│   │   ├── decisions.py    # decisions.md
│   │   └── context.py      # Контекст проекта
│   ├── rag/
│   │   ├── indexer.py      # Индексация файлов
│   │   ├── embedder.py     # Ollama embeddings
│   │   ├── store.py        # SQLite vector store
│   │   └── retriever.py    # RAG retriever
│   └── tools/
│       └── file_tools.py   # Файловые операции
├── tests/                  # 62 тестов
├── davinci.bat             # Windows launcher
├── install.bat             # Установщик
└── pyproject.toml
```

## Тесты

```bash
pytest tests/ -v
```

## Конфигурация

`.davinci/config.yaml`:
```yaml
llm:
  base_url: "http://127.0.0.1:11434"
  model: "qwen2.5:14b"
  temperature: 0.3
  timeout: 120
agent:
  max_iterations: 5
```

## Лицензия

MIT
