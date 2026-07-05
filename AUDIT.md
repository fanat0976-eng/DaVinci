# DaVinci — Полный аудит кодовой базы

> Дата: 2026-07-05
> Аудитор: Конструктор

---

## КРИТИЧЕСКИЕ БАГИ (must fix)

### 1. SQLite connections не закрываются при ошибках
**Файл**: `rag/store.py`
**Проблема**: `conn.close()` не в `finally` блоке. При ошибке в `search()` или `add()` connection утекает.

```python
# Текущий код (СЛОМАНО):
conn = sqlite3.connect(str(self.db_path))
rows = conn.execute(...).fetchall()
conn.close()  # Не дойдёт сюда при ошибке!

# Исправление:
conn = sqlite3.connect(str(self.db_path))
try:
    rows = conn.execute(...).fetchall()
finally:
    conn.close()
```

**Влияние**: Утечка файловых дескрипторов при долгой работе.

### 2. Path traversal — агент может писать за пределы проекта
**Файл**: `tools/file_tools.py:14-19`
**Проблема**: `_resolve()` разрешает абсолютные пути без проверки containment.

```python
# Агент может сделать:
[FILE: /etc/passwd] malicious content
# Или:
[FILE: ../../sibling-project/secret.py] stolen code
```

**Исправление**: Проверять `resolved.is_relative_to(self.project_dir)`.

### 3. Bash injection — нет блокировки опасных команд
**Файл**: `tools/file_tools.py:67-85`
**Проблема**: `run_bash()` выполняет ЛЮБУЮ команду без фильтрации.

```python
# Агент может сделать:
[BASH] rm -rf /
[BASH] Format-Volume -DriveLetter C
```

**Исправление**: Whitelist опасных команд, или хотя бы предупреждение.

### 4. _clean_content ломает content с markdown внутри
**Файл**: `agents/base.py:65-71`
**Проблема**: Regex `^```\w*\n` и `\n```$` удалит_legitimate markdown в контенте файла.

```python
# Если агент пишет README.md:
[FILE: README.md]
# Title
Some text with `code` and ```python
block```
More text

# _clean_content удалит ```python и ```, сломав формат
```

**Исправление**: Удалять markdown markers только если они обрамляют ВЕСЬ контент.

### 5. history накапливается бесконечно
**Файл**: `agents/base.py:56-57`
**Проблема**: `self.history` растёт с каждым вызовом `run()`. Нет лимита.

```python
# После 50 задач history будет содержать 100 сообщений
# Каждое следующее build_messages() будет отправлять всё больше токенов
```

**Исправление**: Добавить `max_history` и скользящее окно.

---

## СЕРЬЁЗНЫЕ ПРОБЛЕМЫ (should fix)

### 6. Coordinator.run() — else без elif (строка 159-165)
**Файл**: `coordinator.py:159-165`
**Проблема**: `elif agent_name == "tester"` стоит после `if agent_name != "tester" and results["pipeline"]:`, что делает его недостижимым когда `agent_name == "tester"` и `results["pipeline"]` пуст.

```python
# Текущий код:
if agent_name != "tester" and results["pipeline"]:
    ...
elif agent_name == "tester":  # Достижимо ТОЛЬКО если results["pipeline"] пуст
    ...
```

**Исправление**: Переструктурировать логику.

### 7. Нет обработки ошибок LLM в pipeline
**Файл**: `coordinator.py:122-157`
**Проблема**: Если LLM падает на шаге architect, весь pipeline ломается. Нет graceful degradation.

**Исправление**: Try/except вокруг каждого шага pipeline с fallback.

### 8. _is_complex() делает LLM call для КАЖДОЙ задачи
**Файл**: `coordinator.py:197-226`
**Проблема**: Даже для простых задач ("fix typo") делается LLM call для определения сложности. +1-2 сек задержка.

**Исправление**: Кэшировать результат, или использовать keyword fallback first.

### 9. edit_file() — replace() заменяет ПЕРВОЕ вхождение
**Файл**: `tools/file_tools.py:47`
**Проблема**: `content.replace(old, new, 1)` заменяет только первое вхождение. Если old текст встречается несколько раз — непредсказуемо.

**Исправление**: Требовать уникальный old текст, или заменять все вхождения.

### 10. Vector store — cosine similarity O(n) на КАЖДЫЙ поиск
**Файл**: `rag/store.py:71-108`
**Проблема**: При большом количестве чанков (1000+) каждый поиск — полный scan. Нет индексации.

**Исправление**: Для MVP терпимо, но для production нужен HNSW или IVFFlat.

---

## ЗАГЛУШКИ И НЕДОРАБОТКИ

### 11. config.agent.max_iterations не используется
**Файл**: `config.py:22`
**Проблема**: `max_iterations = 5` задано, но нигде не проверяется. Агент может зациклиться.

### 12. config.agent.allowed_extensions не используется
**Файл**: `config.py:24-30`
**Проблема**: Список расширений задан, но `file_tools.py` не проверяет его.

### 13. Embedder.models не используется
**Файл**: `llm/client.py:69-81`
**Проблема**: `embed()` хардкодит `"nomic-embed-text"` вместо использования `config.llm.embedding_model`.

### 14. run_stream() не парсит действия
**Файл**: `coordinator.py:182-195`
**Проблема**: `run_stream()` возвращает токены, но CLI парсит действия отдельно. Дублирование логики.

### 15. Нет тестов для LLM client
**Проблема**: `llm/client.py` не имеет unit тестов. Все тесты мокают LLM.

---

## НАРУШЕНИЯ КОДИНГ-СТИЛЯ

### 16. Импорт yaml внутри методов
**Файл**: `config.py:58,82`
**Проблема**: `import yaml` внутри `load()` и `save()`. Должен быть на уровне модуля.

### 17. Bare except в config.load()
**Файл**: `config.py:69`
**Проблема**: `except Exception: pass` — глотает ВСЕ ошибки, включая SyntaxError в YAML.

### 18. Неконсистентные type hints
**Файл**: `config.py:39` — `davinci_dir: Path = field(default=None)` — None не Path.
**Файл**: `coordinator.py:92` — `force_agent: str | None` — OK, но `run()` не возвращает типизированный dict.

### 19. magic numbers без констант
**Файл**: `rag/indexer.py:46` — `chunk_size=50, chunk_overlap=10`
**Файл**: `memory/context.py:27` — `content[:5000]`
**Файл**: `coordinator.py:142` — `response[:2000]`

### 20. Отсутствует __all__ в __init__.py
**Файл**: `rag/__init__.py`, `memory/__init__.py`
**Проблема**: Пустые `__init__.py` без `__all__`.

---

## ПРОБЛЕМЫ БЕЗОПАСНОСТИ

### 21. Нет санитизации путей от LLM
**Проблема**: LLM может вернуть пути с `..`, абсолютные пути, symlink traversal.

### 22. Bash tool — полный доступ к системе
**Проблема**: Агент может выполнить `rm -rf`, `Format-Volume`, `Invoke-WebRequest` с данными.

### 23. Нет rate limiting на LLM calls
**Проблема**: Бесконечные retry или параллельные вызовы могут перегрузить Ollama.

---

## МЕТРИКИ ПОКРЫТИЯ

| Модуль | Тестов | Покрытие (оценка) |
|--------|--------|-------------------|
| agents/base.py | 6 | ~70% (parse_actions, execute_action) |
| agents/coder.py | 1 | ~20% (только system_prompt) |
| agents/architect.py | 1 | ~20% |
| agents/tester.py | 1 | ~20% |
| agents/reviewer.py | 1 | ~20% |
| config.py | 3 | ~80% |
| llm/client.py | 0 | 0% (все мокают) |
| tools/file_tools.py | 6 | ~90% |
| rag/indexer.py | 4 | ~80% |
| rag/store.py | 4 | ~85% |
| rag/retriever.py | 0 | 0% |
| rag/embedder.py | 0 | 0% |
| memory/decisions.py | 4 | ~90% |
| memory/context.py | 2 | ~60% |
| coordinator.py | 1 | ~30% |
| cli.py | 0 | 0% |

**Общее покрытие: ~45%** (цель: 70%+)

---

## ПЛАН ИСПРАВЛЕНИЙ

### Priority 1 (Критические — сейчас):
1. Path traversal check в file_tools.py
2. SQLite connection в try/finally
3. Bash command whitelist
4. History limit в base.py
5. Fix coordinator.py elif bug

### Priority 2 (Серьёзные — сегодня):
6. Graceful degradation в pipeline
7. LLM call caching для _is_complex
8. Edit uniqueness check
9. Add missing tests (LLM, Retriever, Embedder)

### Priority 3 (Polish — завтра):
10. Config validation
11. Rate limiting
12. Path sanitization
13. Remove magic numbers

---

*Аудит завершён: 2026-07-05*
*Найдено: 5 критических, 5 серьёзных, 5 заглушек, 5 нарушений стиля, 3 проблемы безопасности*
