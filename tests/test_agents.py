"""Tests for all agents."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from davinci.agents.architect import ArchitectAgent
from davinci.agents.coder import CoderAgent
from davinci.agents.tester import TesterAgent
from davinci.agents.reviewer import ReviewerAgent


def test_architect_system_prompt():
    """Architect has proper system prompt."""
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = ArchitectAgent(MagicMock(), Path(tmpdir))
        prompt = agent.system_prompt()
        assert "Architect" in prompt
        assert "[PLAN]" in prompt


def test_tester_system_prompt():
    """Tester has proper system prompt."""
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = TesterAgent(MagicMock(), Path(tmpdir))
        prompt = agent.system_prompt()
        assert "Tester" in prompt
        assert "[REVIEW]" in prompt


def test_reviewer_system_prompt():
    """Reviewer has proper system prompt."""
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = ReviewerAgent(MagicMock(), Path(tmpdir))
        prompt = agent.system_prompt()
        assert "Reviewer" in prompt
        assert "APPROVED" in prompt


def test_parse_plan_action():
    """Parse plan action from architect response."""
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = ArchitectAgent(MagicMock(), Path(tmpdir))
        response = """[PLAN]
## Task: Add auth

### Files to modify:
- app.py — add auth middleware

### Steps:
1. Add middleware
2. Test
"""
        # Plan is in response text, no file actions
        actions = agent.parse_actions(response)
        assert len(actions) == 0  # Plans don't create files directly


def test_parse_review_action():
    """Parse review action from tester response."""
    with tempfile.TemporaryDirectory() as tmpdir:
        agent = TesterAgent(MagicMock(), Path(tmpdir))
        response = """[REVIEW]
## Code Review

### Issues Found:
- **CRITICAL**: SQL injection in query

### Verdict: FAIL
"""
        # Review is informational
        actions = agent.parse_actions(response)
        assert len(actions) == 0  # Reviews don't create files


def test_all_agents_share_base():
    """All agents inherit from BaseAgent."""
    from davinci.agents.base import BaseAgent
    with tempfile.TemporaryDirectory() as tmpdir:
        llm = MagicMock()
        for AgentClass in [ArchitectAgent, CoderAgent, TesterAgent, ReviewerAgent]:
            agent = AgentClass(llm, Path(tmpdir))
            assert isinstance(agent, BaseAgent)
