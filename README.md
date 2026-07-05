# DaVinci

> Local AI Coding Agent — ваш локальный Copilot, работающий полностью офлайн

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-62%20passing-brightgreen.svg)](tests/)

## Что это

**DaVinci** — мультиагентная система для помощи в написании кода, работающая полностью локально на [Ollama](https://ollama.com). Вдохновлён архитектурой [GitHub Squad](https://github.blog/ai-and-ml/github-copilot/how-squad-runs-coordinated-ai-agents-inside-your-repository/).

### Ключевые особенности

- **4 специализированных агента**: Architect, Coder, Tester, Reviewer
- **LLM-based routing**: модель сама определяет лучшего агента для задачи
- **Независимый review**: Tester проверяет код Coder'а, Reviewer чинит ошибки
- **RAG контекст**: агенты понимают весь проект через индексацию
- **Память решений**: `.davinci/decisions.md` — общий мозг команды
- **Rich TUI**: progress bars, таблицы, live streaming
- **Tkinter HUD**: десктопный интерфейс с индустриальной эстетикой
- **Веб-дашборд**: работа через браузер
- **100% локально**: никаких данных в облаке

## Быстрый старт

### Установка

```bash
# Клонируй проект
git clone https://github.com/fanat0976-eng/DaVinci.git
cd DaVinci

# Установи зависимости
pip install -e .

# Или используй установщик (Windows)
install.bat
```

### Требования

- Python 3.11+
- [Ollama](https://ollama.com) (запущенный)
- Модель: `qwen2.5:14b` (рекомендуется)

```bash
# Установи Ollama и модель
ollama pull qwen2.5:14b
ollama pull nomic-embed-text
```

### Использование

#### CLI
```bash
# Инициализация в проекте
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

# Статус проекта
davinci --status

# Список моделей
davinci --models
```

#### Tkinter HUD
```bash
# Запуск десктопного интерфейса
HUD.bat

# Или из терминала
python -m davinci.hud
```

#### Веб-дашборд
```bash
# Запуск дашборда
davinci --dashboard

# Открой браузер: http://127.0.0.1:8080
```

## Архитектура

```
Пользователь
     │
     ▼
┌─────────────────────────────────────────┐
│           LLM Router (qwen2.5)          │
│  Классифицирует задачу → лучший агент   │
└────────┬────────────┬──────────┬────────┘
         │            │          │
    ┌────▼────┐  ┌────▼────┐  ┌─▼──────────┐
    │ARCHITECT│  │  CODER  │  │  TESTER    │
    │Проекти- │  │Пишет    │  │Тестирует   │
    │рует     │  │код      │  │+ ревью     │
    └─────────┘  └─────────┘  └────────────┘
                    │
              ┌─────▼─────┐
              │  REVIEWER  │
              │Ищет баги   │
              └────────────┘
                    │
              ┌─────▼─────┐
              │   RAG     │
              │Контекст   │
              │проекта    │
              └───────────┘
```

### Агенты

| Агент | Роль | Когда вызывается |
|-------|------|-------------------|
| **Architect** | Проектирует решения | Сложные задачи, проектирование систем |
| **Coder** | Пишет код | По умолчанию |
| **Tester** | Пишет тесты, проверяет | Задачи связанные с тестированием |
| **Reviewer** | Ищет баги, проблемы | Ревью, поиск ошибок |

### Pipeline

1. **Router** (LLM) классифицирует задачу
2. **Architect** проектирует (если задача сложная)
3. **Coder** реализует
4. **Tester** проверяет (независимо!)
5. **Reviewer** чинит (если нашёл ошибки)

## Структура проекта

```
DaVinci/
├── davinci/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py              # CLI интерфейс
│   ├── coordinator.py      # Роутер + pipeline
│   ├── config.py           # Конфигурация
│   ├── dashboard.py        # Веб-дашборд
│   ├── hud.py              # Tkinter HUD
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
├── tests/                  # 62 теста
├── davinci.bat             # Windows launcher
├── davinci.ps1             # PowerShell launcher
├── HUD.bat                 # HUD launcher
├── install.bat             # Установщик
├── pyproject.toml
├── LICENSE
├── README.md
└── AUDIT.md
```

## Конфигурация

`.davinci/config.yaml`:

```yaml
llm:
  base_url: "http://127.0.0.1:11434"
  model: "qwen2.5:14b"
  embedding_model: "nomic-embed-text"
  temperature: 0.3
  max_tokens: 4096
  timeout: 120

agent:
  max_iterations: 5
  max_file_size: 100000
```

### Переменные окружения

```bash
OLLAMA_BASE_URL=http://127.0.0.1:11434  # URL Ollama
DAVINCI_MODEL=qwen2.5:14b                # Модель по умолчанию
```

## Тесты

```bash
# Запуск всех тестов
pytest tests/ -v

# С ковереджем
pytest tests/ --cov=davinci --cov-report=term-missing
```

## Безопасность

- **Path traversal**: блокировка записи за пределы проекта
- **Bash injection**: whitelist опасных команд
- **Rate limiting**: 10 запросов в секунду
- **History limit**: не более 20 сообщений в истории

## Лицензия

[MIT](LICENSE)

## Автор

**fanat0976-eng** — [GitHub](https://github.com/fanat0976-eng)
