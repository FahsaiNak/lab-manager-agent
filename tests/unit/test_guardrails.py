"""Unit tests for the archive-execution guardrail (SPEC.md §4, eval case 5)."""

import pytest

from app.guardrails import require_confirmation


class _FakeTool:
    def __init__(self, name):
        self.name = name


@pytest.mark.asyncio
async def test_blocks_execute_archive_without_confirm():
    result = await require_confirmation(
        _FakeTool("execute_archive_plan"), {}, tool_context=None
    )
    assert result["status"] == "blocked"


@pytest.mark.asyncio
async def test_allows_execute_archive_with_confirm():
    result = await require_confirmation(
        _FakeTool("execute_archive_plan"), {"confirm": True}, tool_context=None
    )
    assert result is None


@pytest.mark.asyncio
async def test_other_tools_pass_through_unblocked():
    result = await require_confirmation(
        _FakeTool("scan_filesystem"), {}, tool_context=None
    )
    assert result is None
