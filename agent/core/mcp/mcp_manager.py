
import json
import logging
from pathlib import Path
from typing import Any

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger(__name__)


class MCPManager:
    """Manager for MCP server connections and tool discovery.
    
    Handles:
    - Loading MCP server configuration
    - Establishing connections to multiple MCP servers
    - Discovering and aggregating tools from all servers
    - Resource cleanup
    
    Example:
        manager = MCPManager("config/mcp_servers.json")
        await manager.connect()
        tools = await manager.get_tools()
        # use tools with an agent
        await manager.close()
    """
    
    def __init__(self, config_path: str | Path) -> None:
        """Initialize the MCP manager with a configuration file.
        
        Args:
            config_path: Path to the MCP server configuration JSON file.
        """
        self.config_path = Path(config_path)
        self._client: MultiServerMCPClient | None = None
        self._tools: list[BaseTool] | None = None
        self._servers_config: dict[str, Any] | None = None
    
    def _load_config(self) -> dict[str, Any]:
        """Load MCP server configuration from a JSON file.

        Returns:
            Dictionary containing the mcpServers configuration.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
            json.JSONDecodeError: If the configuration file is not valid JSON.
        """
        # ================== TODO 13 - Load MCP config ==================
        # GOAL : Read and validate the MCP server JSON config.
        # WHY  : Fail loudly on a missing config - a silent {} here looks like 'no tools exist'.
        # STEPS:
        #   1. Raise FileNotFoundError if self.config_path does not exist.
        #   2. Open it with encoding='utf-8' and json.load it.
        #   3. Store config.get('mcpServers', {}) on self._servers_config and return it.
        # HINT : The top-level key is 'mcpServers' (same shape as Claude Desktop's config).
        # CHECK: Point config_path at a bogus file - you should get FileNotFoundError, not {}.
        # SIZE : ~7 lines
        raise NotImplementedError("TODO 13: load mcpServers from JSON")
        # ======================================================

    async def connect(self) -> None:
        """Connect to all configured MCP servers.

        Loads the configuration, establishes connections,
        and automatically discovers available tools.
        """
        # ================== TODO 14 - Connect + discover tools ==================
        # GOAL : Connect to every configured MCP server and cache its tools.
        # WHY  : Tool discovery is dynamic: the agent learns what exists at runtime, not at import.
        # STEPS:
        #   1. Guard re-entry: if self._client is not None, log a warning and return.
        #   2. servers_config = self._load_config(); if empty, warn and return.
        #   3. self._client = MultiServerMCPClient(servers_config).
        #   4. self._tools = await self._client.get_tools(); log how many were found.
        # HINT : Idempotency matters - connect() may be called from more than one agent.
        # CHECK: Call connect() twice; the second must warn, not open a second client.
        # SIZE : ~9 lines
        raise NotImplementedError("TODO 14: connect and populate self._tools")
        # ======================================================

    async def close(self) -> None:
        """Close all MCP connections and clean up resources.

        Note: MultiServerMCPClient v0.1.0+ manages its own lifecycle;
        an explicit close call is not required.
        """
        if self._client is not None:
            self._client = None
            self._tools = None
            logger.info("MCP connections cleaned up")

    async def get_tools(self) -> list[BaseTool]:
        """Return all tools from the connected MCP servers.

        Returns:
            List of LangChain BaseTool objects.

        Raises:
            RuntimeError: If ``connect()`` has not been called yet.
        """
        if self._tools is None:
            raise RuntimeError(
                "MCPManager is not connected. Call connect() before get_tools()."
            )
        return self._tools

    def get_tool_names(self) -> list[str]:
        """Return the names of all available tools.

        Returns:
            List of tool name strings.

        Raises:
            RuntimeError: If ``connect()`` has not been called yet.
        """
        if self._tools is None:
            raise RuntimeError("MCPManager is not connected. Call connect() first.")
        return [tool.name for tool in self._tools]

    def get_server_names(self) -> list[str]:
        """Return the names of configured MCP servers.

        Returns:
            List of server name strings from the configuration.
        """
        if self._servers_config is None:
            self._load_config()
        return list(self._servers_config.keys()) if self._servers_config else []
