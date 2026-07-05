## Summary

**DaVinci** — мультиагентная система для помощи в написании кода, работающая полностью локально на Ollama. Вдохновлён архитектурой GitHub Squad.

### Key Features

- **4 AI Agents**: Architect, Coder, Tester, Reviewer
- **LLM-based Routing**: модель сама определяет лучшего агента
- **Independent Review**: Tester проверяет код Coder'а, Reviewer чинит ошибки
- **RAG Pipeline**: индексация проекта для понимания контекста
- **Rich TUI**: progress bars, таблицы, live streaming
- **Tkinter HUD**: десктопный интерфейс с индустриальной эстетикой
- **Web Dashboard**: работа через браузер
- **Security**: path traversal blocking, bash command whitelist

### Architecture

```
User -> LLM Router -> Agent -> Ollama
              |
        .davinci/
        decisions.md (memory)
        vectors.db (RAG)
        config.yaml
```

### Entry Points

| Method | Command |
|--------|---------|
| HUD.bat | Double-click |
| CLI | `davinci "task"` |
| PowerShell | `.\davinci.ps1 "task"` |
| Dashboard | `davinci --dashboard` -> :8080 |

### Tests

- **62 tests passing**
- Security: path traversal, bash blocking, history limit
- LLM client: chat, stream, availability
- RAG: indexer, store, retriever
- Config: validation, load/save

### Tech Stack

- Python 3.11+
- Ollama (qwen2.5:14b + nomic-embed-text)
- Rich (CLI TUI)
- Tkinter (HUD)
- FastAPI (Dashboard)
- SQLite (Vector Store)

---

**License**: MIT
**Python**: 3.11+
