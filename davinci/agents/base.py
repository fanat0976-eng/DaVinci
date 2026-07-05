"""Base agent class for DaVinci."""

import json
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..llm.client import LLMClient
from ..tools.file_tools import FileTools


class BaseAgent(ABC):
    """Base class for all DaVinci agents."""

    ROLE: str = "base"
    DESCRIPTION: str = "Base agent"

    def __init__(self, llm: LLMClient, project_dir: Path):
        self.llm = llm
        self.project_dir = project_dir
        self.files = FileTools(project_dir)
        self.history: list[dict] = []

    @abstractmethod
    def system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        ...

    def build_messages(self, task: str, context: str = "") -> list[dict]:
        """Build message list for LLM."""
        system = self.system_prompt()
        if context:
            system += f"\n\n## Project Context\n{context}"

        messages = [{"role": "system", "content": system}]
        messages.extend(self.history)
        messages.append({"role": "user", "content": task})
        return messages

    def run(self, task: str, context: str = "") -> dict[str, Any]:
        """Execute the agent's task. Returns result dict."""
        messages = self.build_messages(task, context)
        response = self.llm.chat(messages)

        # Parse actions from response
        actions = self.parse_actions(response)

        # Execute actions
        results = []
        for action in actions:
            result = self.execute_action(action)
            results.append(result)

        # Record in history
        self.history.append({"role": "user", "content": task})
        self.history.append({"role": "assistant", "content": response})

        return {
            "response": response,
            "actions": actions,
            "results": results,
        }

    @staticmethod
    def _clean_content(content: str) -> str:
        """Remove markdown code blocks from content."""
        # Remove ```python ... ``` or ``` ... ```
        content = re.sub(r'^```\w*\n', '', content.strip())
        content = re.sub(r'\n```$', '', content)
        return content.strip()

    def parse_actions(self, response: str) -> list[dict]:
        """Parse tool calls from LLM response.

        Looks for patterns like:
        [FILE: path] content
        [EDIT: path] old -> new
        [BASH] command
        """
        actions = []

        # File write: [FILE: path]\ncontent (possibly with ``` markers)
        file_pattern = re.compile(
            r'\[FILE:\s*(.+?)\]\s*\n(.*?)(?=\[FILE:|\[EDIT:|\[BASH\]|$)',
            re.DOTALL
        )
        for match in file_pattern.finditer(response):
            path = match.group(1).strip()
            content = self._clean_content(match.group(2))
            if content:
                actions.append({"type": "write", "path": path, "content": content})

        # Edit: [EDIT: path]\nold -> new
        edit_pattern = re.compile(
            r'\[EDIT:\s*(.+?)\]\s*\n(.*?)\s*->\s*(.*?)(?=\[FILE:|\[EDIT:|\[BASH\]|$)',
            re.DOTALL
        )
        for match in edit_pattern.finditer(response):
            path = match.group(1).strip()
            old = self._clean_content(match.group(2))
            new = self._clean_content(match.group(3))
            if old and new:
                actions.append({"type": "edit", "path": path, "old": old, "new": new})

        # Bash: [BASH] command
        bash_pattern = re.compile(r'\[BASH\]\s*(.+?)(?=\[FILE:|\[EDIT:|\[BASH\]|$)', re.DOTALL)
        for match in bash_pattern.finditer(response):
            cmd = match.group(1).strip()
            # Remove markdown code blocks from bash commands too
            cmd = self._clean_content(cmd)
            if cmd:
                actions.append({"type": "bash", "command": cmd})

        return actions

    def execute_action(self, action: dict) -> dict:
        """Execute a parsed action."""
        try:
            if action["type"] == "write":
                self.files.write_file(action["path"], action["content"])
                return {"ok": True, "action": "write", "path": action["path"]}

            elif action["type"] == "edit":
                self.files.edit_file(action["path"], action["old"], action["new"])
                return {"ok": True, "action": "edit", "path": action["path"]}

            elif action["type"] == "bash":
                result = self.files.run_bash(action["command"])
                return {"ok": True, "action": "bash", "output": result}

        except Exception as e:
            return {"ok": False, "error": str(e), "action": action["type"]}

        return {"ok": False, "error": f"Unknown action type: {action.get('type')}"}
