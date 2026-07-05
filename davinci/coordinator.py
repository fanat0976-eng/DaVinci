"""Coordinator — thin router that dispatches tasks to agents."""

from pathlib import Path
from typing import Any

from .llm.client import LLMClient
from .agents.architect import ArchitectAgent
from .agents.coder import CoderAgent
from .agents.tester import TesterAgent
from .agents.reviewer import ReviewerAgent
from .memory.decisions import DecisionsMemory
from .memory.context import ContextManager
from .rag.retriever import Retriever
from .config import Config


class Coordinator:
    """Routes tasks to the appropriate agent with RAG and independent review."""

    def __init__(self, config: Config):
        self.config = config
        self.llm = LLMClient(
            base_url=config.llm.base_url,
            model=config.llm.model,
            timeout=config.llm.timeout,
        )

        # Shared memory
        self.decisions = DecisionsMemory(config.davinci_dir)
        self.context = ContextManager(config.project_dir, self.decisions)

        # RAG
        self.retriever = Retriever(config.project_dir, config.llm.base_url)

        # Agents
        self.architect = ArchitectAgent(self.llm, config.project_dir)
        self.coder = CoderAgent(self.llm, config.project_dir)
        self.tester = TesterAgent(self.llm, config.project_dir)
        self.reviewer = ReviewerAgent(self.llm, config.project_dir)

    def route(self, task: str) -> str:
        """Route task using LLM classification.

        Asks the model to classify the task into one of:
        - coder: write/modify code
        - architect: design/architecture planning
        - tester: write tests, verify
        - reviewer: review code, find bugs
        """
        classification_prompt = f"""Classify this task into EXACTLY ONE category. Reply with ONLY the category name, nothing else.

Task: {task}

Categories:
- coder: Writing, modifying, or implementing code. Adding features, fixing bugs in code, creating new files.
- architect: Designing system architecture, planning implementation, creating technical specs, refactoring large systems.
- tester: Writing tests, verifying code works, running test suites, checking test coverage.
- reviewer: Code review, finding bugs/security issues, suggesting improvements, auditing code quality.

Category:"""

        try:
            response = self.llm.chat(
                [{"role": "user", "content": classification_prompt}],
                temperature=0.1,
                max_tokens=20,
            )
            agent = response.strip().lower().split()[0]  # Take first word
            if agent in ("coder", "architect", "tester", "reviewer"):
                return agent
        except Exception:
            pass

        # Fallback to keyword routing
        return self._keyword_route(task)

    def _keyword_route(self, task: str) -> str:
        """Fallback keyword-based routing."""
        task_lower = task.lower()
        if any(w in task_lower for w in ["архитектура", "спроектируй", "план", "design", "architect"]):
            return "architect"
        if any(w in task_lower for w in ["тест", "проверь", "test", "verify"]):
            return "tester"
        if any(w in task_lower for w in ["ревью", "баг", "ошибк", "review", "bug", "fix"]):
            return "reviewer"
        return "coder"

    def index(self) -> int:
        """Index the project for RAG. Returns number of chunks."""
        return self.retriever.index_project()

    def run(self, task: str, force_agent: str | None = None) -> dict[str, Any]:
        """Execute a task with full agent pipeline.

        Pipeline:
        1. Gather context (RAG + decisions)
        2. Architect designs (if complex task)
        3. Coder implements
        4. Tester verifies
        5. Reviewer checks (if issues found)
        """
        agent_name = force_agent or self.route(task)

        # Gather context from multiple sources
        base_context = self.context.gather(task)

        # Add RAG context if indexed
        if self.retriever.is_indexed():
            rag_context = self.retriever.get_context(task, top_k=3)
            base_context += f"\n\n{rag_context}"

        # Record decision
        self.decisions.add(
            title=f"Task: {task[:50]}...",
            content=f"- Assigned to: **{agent_name}**\n- Task: {task}",
            agent="coordinator",
        )

        results = {"pipeline": [], "task": task, "agent": agent_name}

        # Execute based on agent type
        try:
            if agent_name == "architect":
                # Architect designs, then coder implements
                arch_result = self.architect.run(
                    f"Design a solution for: {task}\n\nExisting context:\n{base_context}"
                )
                results["pipeline"].append({"agent": "architect", "result": arch_result})
                base_context += f"\n\n## Architecture Plan\n{arch_result['response']}"

                coder_result = self.coder.run(
                    f"Implement: {task}\n\nPlan:\n{base_context}"
                )
                results["pipeline"].append({"agent": "coder", "result": coder_result})

            elif agent_name == "coder":
                # Check if complex (needs architect first)
                if self._is_complex(task):
                    arch_result = self.architect.run(
                        f"Design a solution for: {task}\n\nExisting context:\n{base_context}"
                    )
                    results["pipeline"].append({"agent": "architect", "result": arch_result})
                    base_context += f"\n\n## Architecture Plan\n{arch_result['response']}"

                coder_result = self.coder.run(
                    f"Implement: {task}\n\nPlan:\n{base_context}"
                )
                results["pipeline"].append({"agent": "coder", "result": coder_result})

            elif agent_name == "tester":
                tester_result = self.tester.run(f"{task}\n\n{base_context}")
                results["pipeline"].append({"agent": "tester", "result": tester_result})

            elif agent_name == "reviewer":
                reviewer_result = self.reviewer.run(f"{task}\n\n{base_context}")
                results["pipeline"].append({"agent": "reviewer", "result": reviewer_result})

            # Independent review (for coder/architect output)
            if agent_name in ("coder", "architect") and results["pipeline"]:
                code_context = "\n\n".join(
                    f"### {p['agent']} output:\n{p['result']['response'][:2000]}"
                    for p in results["pipeline"]
                )
                tester_result = self.tester.run(
                    f"Review and test this implementation:\n\n{code_context}\n\nOriginal task: {task}"
                )
                results["pipeline"].append({"agent": "tester", "result": tester_result})

                # If tester found issues, reviewer fixes (not the original coder!)
                if "FAIL" in tester_result["response"] or "REJECTED" in tester_result["response"]:
                    reviewer_result = self.reviewer.run(
                        f"The tester found issues. Fix them:\n\n"
                        f"Tester feedback:\n{tester_result['response']}\n\n"
                        f"Original code:\n{code_context}"
                    )
                    results["pipeline"].append({"agent": "reviewer", "result": reviewer_result})

        except Exception as e:
            results["error"] = str(e)

        # Combine all responses
        full_response = "\n\n---\n\n".join(
            f"### {p['agent'].upper()}\n{p['result']['response']}"
            for p in results["pipeline"]
        )
        results["response"] = full_response

        # Collect all actions
        all_actions = []
        for p in results["pipeline"]:
            all_actions.extend(p["result"].get("actions", []))
        results["actions"] = all_actions

        return results

    def run_stream(self, task: str):
        """Stream the response token by token."""
        agent_name = self.route(task)
        agent = getattr(self, agent_name)

        # Gather context
        context = self.context.gather(task)
        if self.retriever.is_indexed():
            rag_context = self.retriever.get_context(task, top_k=3)
            context += f"\n\n{rag_context}"

        messages = agent.build_messages(task, context)
        for token in self.llm.chat_stream(messages):
            yield token

    def _is_complex(self, task: str) -> bool:
        """Determine if a task needs architectural planning via LLM."""
        prompt = f"""Is this task complex enough to need architecture planning first?
Answer ONLY "yes" or "no".

A task is complex if it:
- Involves multiple files or modules
- Requires designing a new system or major feature
- Needs careful planning before implementation
- Involves refactoring existing architecture

Simple tasks (answer "no"):
- Adding a single function
- Small bug fixes
- Writing tests for existing code
- Minor edits to one file

Task: {task}

Answer:"""

        try:
            response = self.llm.chat(
                [{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=5,
            )
            return response.strip().lower().startswith("yes")
        except Exception:
            return False
