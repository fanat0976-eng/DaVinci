"""DaVinci Dashboard — simple web UI for running tasks."""

import json
from pathlib import Path

from rich.console import Console

console = Console()

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DaVinci - AI Coding Agent</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: #0a0a0f;
            color: #e0e0e0;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 20px 30px;
            border-bottom: 2px solid #0f3460;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .logo { font-size: 28px; }
        .title { font-size: 24px; font-weight: 600; color: #e94560; }
        .subtitle { color: #888; font-size: 14px; }
        .container { max-width: 1200px; margin: 0 auto; padding: 30px; }
        .status-bar {
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: #1a1a2e;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 15px 20px;
            flex: 1;
        }
        .status-card .label { color: #888; font-size: 12px; text-transform: uppercase; }
        .status-card .value { font-size: 18px; font-weight: 600; margin-top: 5px; }
        .status-card .value.ok { color: #4ade80; }
        .status-card .value.warn { color: #fbbf24; }
        .status-card .value.error { color: #ef4444; }
        .input-section {
            background: #1a1a2e;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .input-section h3 { margin-bottom: 15px; color: #e94560; }
        textarea {
            width: 100%;
            height: 100px;
            background: #0f0f1a;
            border: 1px solid #444;
            border-radius: 6px;
            color: #e0e0e0;
            padding: 12px;
            font-family: 'Consolas', monospace;
            font-size: 14px;
            resize: vertical;
        }
        textarea:focus { outline: none; border-color: #e94560; }
        .btn-row { display: flex; gap: 10px; margin-top: 15px; }
        .btn {
            padding: 10px 24px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-primary {
            background: #e94560;
            color: white;
        }
        .btn-primary:hover { background: #d63851; }
        .btn-secondary {
            background: #333;
            color: #e0e0e0;
        }
        .btn-secondary:hover { background: #444; }
        .output-section {
            background: #1a1a2e;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 20px;
        }
        .output-section h3 { margin-bottom: 15px; color: #e94560; }
        #output {
            background: #0f0f1a;
            border: 1px solid #444;
            border-radius: 6px;
            padding: 15px;
            font-family: 'Consolas', monospace;
            font-size: 13px;
            min-height: 300px;
            max-height: 500px;
            overflow-y: auto;
            white-space: pre-wrap;
            line-height: 1.5;
        }
        .agent-tag {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            margin-right: 5px;
        }
        .agent-coder { background: #166534; color: #4ade80; }
        .agent-tester { background: #854d0e; color: #fbbf24; }
        .agent-reviewer { background: #991b1b; color: #fca5a5; }
        .agent-architect { background: #581c87; color: #c084fc; }
        .spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid #444;
            border-top-color: #e94560;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin-right: 8px;
            vertical-align: middle;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">🎨</div>
        <div>
            <div class="title">DaVinci</div>
            <div class="subtitle">Local AI Coding Agent</div>
        </div>
    </div>
    <div class="container">
        <div class="status-bar">
            <div class="status-card">
                <div class="label">Ollama</div>
                <div class="value" id="ollama-status">Checking...</div>
            </div>
            <div class="status-card">
                <div class="label">Model</div>
                <div class="value" id="model-name">-</div>
            </div>
            <div class="status-card">
                <div class="label">RAG Chunks</div>
                <div class="value" id="rag-chunks">-</div>
            </div>
        </div>
        <div class="input-section">
            <h3>Task</h3>
            <textarea id="task-input" placeholder="Describe what you want to do...&#10;Example: Add email validation to create_user function"></textarea>
            <div class="btn-row">
                <button class="btn btn-primary" onclick="runTask()">Run</button>
                <button class="btn btn-secondary" onclick="runTask(true)">Run (no stream)</button>
                <button class="btn btn-secondary" onclick="indexProject()">Index RAG</button>
            </div>
        </div>
        <div class="output-section">
            <h3>Output</h3>
            <div id="output">Ready. Enter a task and click Run.</div>
        </div>
    </div>
    <script>
        const output = document.getElementById('output');
        const taskInput = document.getElementById('task-input');

        // Load status on page load
        fetchStatus();

        async function fetchStatus() {
            try {
                const resp = await fetch('/api/status');
                const data = await resp.json();
                document.getElementById('ollama-status').textContent = data.ollama ? 'Connected' : 'Offline';
                document.getElementById('ollama-status').className = 'value ' + (data.ollama ? 'ok' : 'error');
                document.getElementById('model-name').textContent = data.model;
                document.getElementById('rag-chunks').textContent = data.rag_chunks || 'Not indexed';
            } catch (e) {
                document.getElementById('ollama-status').textContent = 'Error';
                document.getElementById('ollama-status').className = 'value error';
            }
        }

        async function runTask(noStream = false) {
            const task = taskInput.value.trim();
            if (!task) return;

            output.innerHTML = '<span class="spinner"></span> Processing...';
            const btn = document.querySelector('.btn-primary');
            btn.disabled = true;

            try {
                const resp = await fetch('/api/run', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({task, stream: !noStream})
                });

                if (!resp.ok) {
                    const err = await resp.json();
                    output.textContent = 'Error: ' + (err.error || 'Unknown error');
                    return;
                }

                if (noStream) {
                    const data = await resp.json();
                    output.textContent = data.response || '(no response)';
                } else {
                    // Streaming
                    const reader = resp.body.getReader();
                    const decoder = new TextDecoder();
                    output.textContent = '';
                    while (true) {
                        const {done, value} = await reader.read();
                        if (done) break;
                        output.textContent += decoder.decode(value, {stream: true});
                        output.scrollTop = output.scrollHeight;
                    }
                }
            } catch (e) {
                output.textContent = 'Error: ' + e.message;
            } finally {
                btn.disabled = false;
            }
        }

        async function indexProject() {
            output.innerHTML = '<span class="spinner"></span> Indexing project...';
            try {
                const resp = await fetch('/api/index', {method: 'POST'});
                const data = await resp.json();
                output.textContent = 'Indexed ' + data.chunks + ' chunks';
                fetchStatus();
            } catch (e) {
                output.textContent = 'Error: ' + e.message;
            }
        }

        // Ctrl+Enter to run
        taskInput.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') runTask();
        });
    </script>
</body>
</html>"""


def create_app(project_dir: Path):
    """Create FastAPI app for dashboard."""
    try:
        from fastapi import FastAPI
        from fastapi.responses import HTMLResponse, StreamingResponse
        from fastapi.middleware.cors import CORSMiddleware
    except ImportError:
        console.print("[red]FastAPI not installed. Run: pip install fastapi uvicorn[/red]")
        return None

    from .config import Config
    from .coordinator import Coordinator

    app = FastAPI(title="DaVinci Dashboard")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

    @app.get("/", response_class=HTMLResponse)
    async def index():
        return DASHBOARD_HTML

    @app.get("/api/status")
    async def status():
        config = Config.load(project_dir)
        from .llm.client import LLMClient
        client = LLMClient(config.llm.base_url, config.llm.model)
        ollama_ok = client.is_available()

        from .rag.retriever import Retriever
        retriever = Retriever(project_dir, config.llm.base_url)
        rag_stats = retriever.stats()

        return {
            "ollama": ollama_ok,
            "model": config.llm.model,
            "rag_chunks": rag_stats["chunks"] if rag_stats["indexed"] else None,
        }

    @app.post("/api/index")
    async def index_project():
        config = Config.load(project_dir)
        coordinator = Coordinator(config)
        count = coordinator.index()
        return {"chunks": count}

    @app.post("/api/run")
    async def run_task(body: dict):
        task = body.get("task", "")
        stream = body.get("stream", True)

        config = Config.load(project_dir)
        coordinator = Coordinator(config)

        if stream:
            def generate():
                agent_name = coordinator.route(task)
                agent = getattr(coordinator, agent_name)
                context = coordinator.context.gather(task)
                if coordinator.retriever.is_indexed():
                    rag_context = coordinator.retriever.get_context(task, top_k=3)
                    context += f"\n\n{rag_context}"
                messages = agent.build_messages(task, context)
                for token in coordinator.llm.chat_stream(messages):
                    yield token

            return StreamingResponse(generate(), media_type="text/plain")
        else:
            result = coordinator.run(task)
            return {"response": result["response"], "actions": result.get("actions", [])}

    return app


def cmd_dashboard(project_dir: Path, port: int = 8080):
    """Start dashboard server."""
    app = create_app(project_dir)
    if app is None:
        return

    import uvicorn
    console.print(f"[bold green]DaVinci Dashboard[/bold green]")
    console.print(f"[dim]http://127.0.0.1:{port}[/dim]")
    console.print(f"[dim]Press Ctrl+C to stop[/dim]")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
