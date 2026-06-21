"""Guardrail callbacks shared across Lab Manager sub-agents (SPEC.md §4)."""

from google.adk.tools import BaseTool, ToolContext


async def require_confirmation(
    tool: BaseTool, args: dict, tool_context: ToolContext
) -> dict | None:
    """Blocks execute_archive_plan unless the caller explicitly passed confirm=True.

    Returning a dict here short-circuits the tool call — execute_archive_plan's
    body never runs, so no archive action happens without explicit confirmation.
    """
    if tool.name == "execute_archive_plan" and not args.get("confirm"):
        return {
            "status": "blocked",
            "reason": "Archive execution requires confirm=True from a human-in-the-loop approval.",
        }
    return None
