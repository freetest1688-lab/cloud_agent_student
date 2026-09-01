"""Helpers for loading and normalizing the MCP servers config.

The JSON file at ``agent/config/mcp_servers.json`` may declare relative ``cwd``
paths (for example ``"agent"``). Those paths must be resolved to absolute paths
before being handed to ``MultiServerMCPClient``; otherwise the subprocess
launcher resolves them against whatever directory the parent process happens to
be running from (e.g. the FastAPI app's ``app/`` folder), which produces a
misleading ``FileNotFoundError: [Errno 2] No such file or directory: 'agent'``.
"""

from __future__ import annotations

import json
import os
from typing import Any

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "mcp_servers.json")
AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(AGENT_DIR)


def _resolve_cwd(value: str) -> str:
    if os.path.isabs(value):
        return value
    return os.path.normpath(os.path.join(REPO_ROOT, value))


def load_mcp_servers_config(path: str | None = None) -> dict[str, Any]:
    """Load mcp_servers.json and rewrite any relative ``cwd`` to absolute."""
    config_path = path or CONFIG_PATH
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    servers = config.get("mcpServers", {})
    for server in servers.values():
        cwd = server.get("cwd")
        if isinstance(cwd, str) and cwd:
            server["cwd"] = _resolve_cwd(cwd)
    return config
