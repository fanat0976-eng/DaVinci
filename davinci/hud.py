"""DaVinci HUD — Tkinter-based desktop interface."""

import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
import sys
import io
from pathlib import Path


# === DaVinci Color Palette ===
# Not cyberpunk, not neon — our own industrial-technical aesthetic
COLORS = {
    "bg_dark": "#0d1117",      # Deep charcoal
    "bg_mid": "#161b22",       # Panel background
    "bg_light": "#21262d",     # Input background
    "border": "#30363d",       # Subtle borders
    "accent": "#d4a574",       # Warm copper — our signature
    "accent_dim": "#8b6914",   # Muted gold
    "text": "#c9d1d9",         # Light gray text
    "text_dim": "#6e7681",     # Dimmed text
    "success": "#7ee787",      # Green for OK
    "error": "#f85149",        # Red for errors
    "warning": "#d29922",      # Amber for warnings
    "coder": "#7ee787",        # Green agent
    "tester": "#d29922",       # Amber agent
    "reviewer": "#f85149",     # Red agent
    "architect": "#bc8cff",    # Purple agent
}

FONTS = {
    "title": ("Consolas", 14, "bold"),
    "body": ("Consolas", 11),
    "small": ("Consolas", 9),
    "label": ("Segoe UI", 10),
}


class DaVinciHUD:
    """Desktop HUD for DaVinci AI Coding Agent."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DaVinci HUD")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)
        self.root.configure(bg=COLORS["bg_dark"])

        self.project_dir = Path.cwd()
        self._build_ui()

    def _build_ui(self):
        """Build the HUD interface."""
        # === Header ===
        header = tk.Frame(self.root, bg=COLORS["bg_mid"], height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header, text="DaVinci", font=FONTS["title"],
            bg=COLORS["bg_mid"], fg=COLORS["accent"]
        ).pack(side=tk.LEFT, padx=15, pady=10)

        tk.Label(
            header, text="AI Coding Agent", font=FONTS["small"],
            bg=COLORS["bg_mid"], fg=COLORS["text_dim"]
        ).pack(side=tk.LEFT, pady=10)

        # Status indicators
        self.status_frame = tk.Frame(header, bg=COLORS["bg_mid"])
        self.status_frame.pack(side=tk.RIGHT, padx=15)

        self.ollama_label = tk.Label(
            self.status_frame, text="OLLAMA: ...", font=FONTS["small"],
            bg=COLORS["bg_mid"], fg=COLORS["text_dim"]
        )
        self.ollama_label.pack(side=tk.RIGHT)

        # === Main area ===
        main = tk.Frame(self.root, bg=COLORS["bg_dark"])
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left panel — task input
        left = tk.Frame(main, bg=COLORS["bg_dark"], width=350)
        left.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        left.pack_propagate(False)

        # Task label
        tk.Label(
            left, text="TASK", font=FONTS["small"],
            bg=COLORS["bg_dark"], fg=COLORS["accent"]
        ).pack(anchor=tk.W, pady=(5, 2))

        # Task input
        self.task_input = tk.Text(
            left, height=6, font=FONTS["body"],
            bg=COLORS["bg_light"], fg=COLORS["text"],
            insertbackground=COLORS["accent"],
            borderwidth=1, relief=tk.FLAT,
            padx=10, pady=8,
            wrap=tk.WORD,
        )
        self.task_input.pack(fill=tk.X, pady=(0, 8))
        self.task_input.bind("<Control-Return>", lambda e: self._run_task())

        # Agent selector
        agent_frame = tk.Frame(left, bg=COLORS["bg_dark"])
        agent_frame.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            agent_frame, text="AGENT", font=FONTS["small"],
            bg=COLORS["bg_dark"], fg=COLORS["text_dim"]
        ).pack(side=tk.LEFT)

        self.agent_var = tk.StringVar(value="auto")
        agents = ["auto", "coder", "architect", "tester", "reviewer"]
        self.agent_menu = ttk.Combobox(
            agent_frame, textvariable=self.agent_var,
            values=agents, state="readonly", width=12
        )
        self.agent_menu.pack(side=tk.RIGHT)

        # Buttons
        btn_frame = tk.Frame(left, bg=COLORS["bg_dark"])
        btn_frame.pack(fill=tk.X, pady=(0, 8))

        self.run_btn = tk.Button(
            btn_frame, text="RUN", font=FONTS["label"],
            bg=COLORS["accent"], fg=COLORS["bg_dark"],
            activebackground=COLORS["accent_dim"],
            borderwidth=0, padx=20, pady=6,
            command=self._run_task,
        )
        self.run_btn.pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(
            btn_frame, text="INDEX", font=FONTS["label"],
            bg=COLORS["bg_light"], fg=COLORS["text"],
            activebackground=COLORS["border"],
            borderwidth=0, padx=15, pady=6,
            command=self._index_project,
        ).pack(side=tk.LEFT, padx=(0, 5))

        tk.Button(
            btn_frame, text="STATUS", font=FONTS["label"],
            bg=COLORS["bg_light"], fg=COLORS["text"],
            activebackground=COLORS["border"],
            borderwidth=0, padx=15, pady=6,
            command=self._show_status,
        ).pack(side=tk.LEFT)

        # Quick actions
        tk.Label(
            left, text="QUICK ACTIONS", font=FONTS["small"],
            bg=COLORS["bg_dark"], fg=COLORS["text_dim"]
        ).pack(anchor=tk.W, pady=(10, 4))

        quick_frame = tk.Frame(left, bg=COLORS["bg_dark"])
        quick_frame.pack(fill=tk.X)

        for text, task in [
            ("Tests", "Write tests for all functions"),
            ("Review", "Code review for security issues"),
            ("Fix", "Find and fix bugs in the code"),
        ]:
            tk.Button(
                quick_frame, text=text, font=FONTS["small"],
                bg=COLORS["bg_light"], fg=COLORS["text_dim"],
                activebackground=COLORS["border"],
                borderwidth=0, padx=10, pady=3,
                command=lambda t=task: self._quick_task(t),
            ).pack(side=tk.LEFT, padx=(0, 3))

        # Right panel — output
        right = tk.Frame(main, bg=COLORS["bg_dark"])
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))

        tk.Label(
            right, text="OUTPUT", font=FONTS["small"],
            bg=COLORS["bg_dark"], fg=COLORS["accent"]
        ).pack(anchor=tk.W, pady=(5, 2))

        # Output text area
        self.output = scrolledtext.ScrolledText(
            right, font=FONTS["body"],
            bg=COLORS["bg_mid"], fg=COLORS["text"],
            insertbackground=COLORS["accent"],
            borderwidth=1, relief=tk.FLAT,
            padx=10, pady=8,
            wrap=tk.WORD,
            state=tk.DISABLED,
        )
        self.output.pack(fill=tk.BOTH, expand=True)

        # Configure text tags for colored output
        self.output.tag_configure("agent_coder", foreground=COLORS["coder"])
        self.output.tag_configure("agent_tester", foreground=COLORS["tester"])
        self.output.tag_configure("agent_reviewer", foreground=COLORS["reviewer"])
        self.output.tag_configure("agent_architect", foreground=COLORS["architect"])
        self.output.tag_configure("accent", foreground=COLORS["accent"])
        self.output.tag_configure("dim", foreground=COLORS["text_dim"])
        self.output.tag_configure("error", foreground=COLORS["error"])
        self.output.tag_configure("success", foreground=COLORS["success"])

        # === Footer ===
        footer = tk.Frame(self.root, bg=COLORS["bg_mid"], height=30)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)

        self.footer_label = tk.Label(
            footer, text="Ready", font=FONTS["small"],
            bg=COLORS["bg_mid"], fg=COLORS["text_dim"]
        )
        self.footer_label.pack(side=tk.LEFT, padx=15)

        tk.Label(
            footer, text="Ctrl+Enter to run", font=FONTS["small"],
            bg=COLORS["bg_mid"], fg=COLORS["text_dim"]
        ).pack(side=tk.RIGHT, padx=15)

    def _log(self, text: str, tag: str = None):
        """Append text to output area."""
        self.output.configure(state=tk.NORMAL)
        if tag:
            self.output.insert(tk.END, text, tag)
        else:
            self.output.insert(tk.END, text)
        self.output.see(tk.END)
        self.output.configure(state=tk.DISABLED)

    def _clear_output(self):
        """Clear output area."""
        self.output.configure(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.configure(state=tk.DISABLED)

    def _set_status(self, text: str, color: str = None):
        """Update footer status."""
        self.footer_label.config(text=text, fg=color or COLORS["text_dim"])

    def _run_task(self):
        """Run task in background thread."""
        task = self.task_input.get("1.0", tk.END).strip()
        if not task:
            return

        agent = self.agent_var.get()
        self._clear_output()
        self._set_status(f"Running ({agent})...", COLORS["accent"])
        self.run_btn.config(state=tk.DISABLED)

        def worker():
            try:
                # Redirect stdout to capture prints
                old_stdout = sys.stdout
                sys.stdout = buffer = io.StringIO()

                from .config import Config
                from .coordinator import Coordinator

                config = Config.load(self.project_dir)
                coordinator = Coordinator(config)

                # Route
                agent_name = agent if agent != "auto" else coordinator.route(task)
                self.root.after(0, self._log, f"[{agent_name.upper()}] ", f"agent_{agent_name}")
                self.root.after(0, self._log, f"{task}\n\n", None)

                # Execute
                result = coordinator.run(task, force_agent=agent if agent != "auto" else None)

                # Restore stdout
                sys.stdout = old_stdout

                # Show response
                self.root.after(0, self._log, result["response"], None)

                # Show actions
                if result.get("actions"):
                    self.root.after(0, self._log, "\n\n--- Actions ---\n", "accent")
                    for action in result["actions"]:
                        if action["type"] == "write":
                            self.root.after(0, self._log, f"  + {action['path']}\n", "success")
                        elif action["type"] == "edit":
                            self.root.after(0, self._log, f"  ~ {action['path']}\n", "accent")
                        elif action["type"] == "bash":
                            self.root.after(0, self._log, f"  $ {action['command'][:50]}\n", "dim")

                self.root.after(0, self._set_status, "Done", COLORS["success"])

            except Exception as e:
                sys.stdout = old_stdout
                self.root.after(0, self._log, f"\nERROR: {e}\n", "error")
                self.root.after(0, self._set_status, "Error", COLORS["error"])
            finally:
                self.root.after(0, lambda: self.run_btn.config(state=tk.NORMAL))

        threading.Thread(target=worker, daemon=True).start()

    def _quick_task(self, task: str):
        """Run a quick action."""
        self.task_input.delete("1.0", tk.END)
        self.task_input.insert("1.0", task)
        self._run_task()

    def _index_project(self):
        """Index project for RAG."""
        self._clear_output()
        self._set_status("Indexing...", COLORS["accent"])

        def worker():
            try:
                from .config import Config
                from .coordinator import Coordinator

                config = Config.load(self.project_dir)
                coordinator = Coordinator(config)
                count = coordinator.index()

                self.root.after(0, self._log, f"Indexed {count} chunks\n", "success")
                self.root.after(0, self._set_status, "Indexed", COLORS["success"])
            except Exception as e:
                self.root.after(0, self._log, f"Error: {e}\n", "error")
                self.root.after(0, self._set_status, "Error", COLORS["error"])

        threading.Thread(target=worker, daemon=True).start()

    def _show_status(self):
        """Show project status."""
        self._clear_output()
        self._log("=== DaVinci Status ===\n\n", "accent")

        try:
            from .config import Config
            from .llm.client import LLMClient
            from .rag.retriever import Retriever

            config = Config.load(self.project_dir)
            client = LLMClient(config.llm.base_url, config.llm.model)
            ollama_ok = client.is_available()

            self._log(f"Project:  {self.project_dir}\n", None)
            self._log(f"Ollama:   {'Connected' if ollama_ok else 'Offline'}\n",
                       "success" if ollama_ok else "error")
            self._log(f"Model:    {config.llm.model}\n", None)

            retriever = Retriever(self.project_dir, config.llm.base_url)
            stats = retriever.stats()
            self._log(f"RAG:      {stats['chunks']} chunks\n" if stats["indexed"]
                       else "RAG:      Not indexed\n", None)

        except Exception as e:
            self._log(f"Error: {e}\n", "error")

    def run(self):
        """Start the HUD."""
        self._show_status()
        self.root.mainloop()


def main():
    """Entry point for HUD."""
    hud = DaVinciHUD()
    hud.run()


if __name__ == "__main__":
    main()
