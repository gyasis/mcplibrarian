"""Platform factory for MCP Dockerize.

Provides ``get_platform`` to obtain an ``AbstractPlatform`` instance by ID,
and ``VALID_PLATFORMS`` listing all supported platform identifiers.
"""

from mcp_dockerize.platforms.base import AbstractPlatform
from mcp_dockerize.platforms.claude_code import ClaudeCodePlatform
from mcp_dockerize.platforms.codex import CodexPlatform
from mcp_dockerize.platforms.cursor import CursorPlatform
from mcp_dockerize.platforms.goose import GoosePlatform
from mcp_dockerize.platforms.opencode import OpenCodePlatform
from mcp_dockerize.platforms.vscode import VSCodePlatform

__all__ = [
    "AbstractPlatform",
    "ClaudeCodePlatform",
    "CodexPlatform",
    "CursorPlatform",
    "GoosePlatform",
    "OpenCodePlatform",
    "VSCodePlatform",
    "VALID_PLATFORMS",
    "get_platform",
]

# Ordered mapping of platform IDs to their concrete classes.
_PLATFORM_REGISTRY: dict[str, type[AbstractPlatform]] = {
    "claude_code": ClaudeCodePlatform,
    "cursor": CursorPlatform,
    "vscode": VSCodePlatform,
    "goose": GoosePlatform,
    "codex": CodexPlatform,
    "opencode": OpenCodePlatform,
}

VALID_PLATFORMS: list[str] = list(_PLATFORM_REGISTRY)


def get_platform(platform_id: str) -> AbstractPlatform:
    """Return an ``AbstractPlatform`` instance for the given *platform_id*.

    Valid IDs: claude_code, cursor, vscode, goose, codex, opencode

    Parameters
    ----------
    platform_id:
        One of the strings listed in ``VALID_PLATFORMS``.

    Returns
    -------
    AbstractPlatform
        A freshly constructed instance of the matching platform class.

    Raises
    ------
    ValueError
        If *platform_id* is not recognised.  The message includes the
        full list of valid IDs so callers can surface it to users.

    Examples
    --------
    >>> platform = get_platform("claude_code")
    >>> platform.platform_id
    'claude_code'

    >>> get_platform("unknown")
    Traceback (most recent call last):
        ...
    ValueError: Unknown platform 'unknown'. Valid platforms: claude_code, cursor, vscode, goose, codex, opencode
    """
    try:
        cls = _PLATFORM_REGISTRY[platform_id]
    except KeyError:
        valid = ", ".join(VALID_PLATFORMS)
        raise ValueError(
            f"Unknown platform {platform_id!r}. Valid platforms: {valid}"
        ) from None
    return cls()
