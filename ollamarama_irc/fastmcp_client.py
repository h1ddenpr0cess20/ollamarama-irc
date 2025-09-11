from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List

import logging
import shlex

from fastmcp import Client
import mcp.types


logger = logging.getLogger(__name__)


class FastMCPClient:
    """Minimal client wrapper to interact with MCP servers.

    Args:
        servers: Mapping of server names to connection specs. Each spec may
            be a URL string, a command+args mapping, or a shell-like string.
    """
    def __init__(self, servers: Dict[str, Any]) -> None:
        self._servers: Dict[str, Any] = {}
        logger.debug("FastMCPClient init with servers: %s", list(servers.keys()))
        for name, spec in servers.items():
            if spec is None:
                continue
            if isinstance(spec, (list, tuple)):
                parts = list(spec)
                if not parts:
                    continue
                cfg: Dict[str, Any] = {"command": str(parts[0])}
                if len(parts) > 1:
                    cfg["args"] = [str(a) for a in parts[1:]]
                self._servers[name] = cfg
                logger.debug("Normalized server '%s' from list: %s", name, cfg)
                continue
            if isinstance(spec, str):
                target = spec.strip()
                if not target:
                    continue
                if "://" in target:
                    self._servers[name] = target
                    logger.debug("Using server '%s' URL: %s", name, target)
                else:
                    parts = shlex.split(target)
                    cfg: Dict[str, Any] = {"command": parts[0]}
                    if len(parts) > 1:
                        cfg["args"] = parts[1:]
                    self._servers[name] = cfg
                    logger.debug("Normalized server '%s' from string to command+args: %s", name, cfg)
                continue
            if isinstance(spec, dict):
                cfg = dict(spec)
                cmd = cfg.get("command")
                if isinstance(cmd, str) and ("args" not in cfg or isinstance(cfg.get("args"), str)) and " " in cmd:
                    parts = shlex.split(cmd)
                    cfg["command"] = parts[0]
                    if len(parts) > 1:
                        cfg["args"] = parts[1:]
                if isinstance(cfg.get("args"), str):
                    cfg["args"] = shlex.split(cfg["args"])  # type: ignore[index]
                if "url" in cfg and "target" not in cfg:
                    cfg["target"] = cfg["url"]
                self._servers[name] = cfg
                logger.debug("Server '%s' config: %s", name, cfg)
                continue
        self._tool_servers: Dict[str, str] = {}

        for name, spec in list(self._servers.items()):
            if isinstance(spec, str) and "://" in spec:
                continue
            if isinstance(spec, dict):
                cmd = spec.get("command")
                args = spec.get("args", [])
                if isinstance(cmd, str):
                    argv = [cmd] + ([str(a) for a in args] if isinstance(args, (list, tuple)) else [])
                    cmdline = " ".join(shlex.quote(p) for p in argv)
                    wrapped = {"command": "bash", "args": ["-lc", f"{cmdline} 2>/dev/null"]}
                    self._servers[name] = wrapped
                    logger.debug("Wrapped server '%s' command for silent output", name)

    async def _list_tools_async(self) -> List[Dict[str, Any]]:
        """Asynchronously list tools from all configured MCP servers.

        Returns:
            A list of tool schema dictionaries suitable for tool-calling APIs.
        """
        schema: List[Dict[str, Any]] = []
        for name, cfg in self._servers.items():
            logger.debug("Listing tools from MCP server '%s'", name)
            spec = cfg
            client = Client({name: spec})
            try:
                async with client:
                    tools = await client.list_tools()
                logger.debug("Server '%s' returned %d tool(s)", name, len(tools))
            except Exception as e:
                logger.error("Failed to list tools from MCP server '%s': %s", name, e)
                continue
            for tool in tools:
                self._tool_servers[tool.name] = name
                schema.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description or "",
                            "parameters": tool.inputSchema
                            or {"type": "object", "properties": {}, "additionalProperties": False},
                        },
                    }
                )
        return schema

    def _run(self, coro):
        """Run an async coroutine from sync code, even if a loop is running.

        If called inside an existing event loop, runs the coroutine in a
        dedicated background thread with its own loop.

        Args:
            coro: The coroutine object to execute.

        Returns:
            The coroutine's result.

        Raises:
            Any exception raised by the coroutine.
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        result: Dict[str, Any] = {}

        def runner() -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result["value"] = loop.run_until_complete(coro)
            except Exception as e:
                result["exc"] = e
            finally:
                loop.close()

        import threading

        t = threading.Thread(target=runner)
        t.start()
        t.join()
        if "exc" in result:
            raise result["exc"]  # type: ignore[misc]
        return result.get("value")

    def list_tools(self) -> List[Dict[str, Any]]:
        """Synchronously list tools from all MCP servers.

        Returns:
            A list of tool schema dictionaries.
        """
        return self._run(self._list_tools_async())

    async def _call_tool_async(self, client: Client, name: str, arguments: Dict[str, Any]) -> Any:
        """Asynchronously call a named tool via an MCP client.

        Args:
            client: Connected ``fastmcp.Client`` instance.
            name: Tool name to execute.
            arguments: Tool input arguments mapping.

        Returns:
            A JSON-serializable object aggregating tool output.
        """
        logger.debug("Calling MCP tool '%s' on client", name)
        async with client:
            result = await client.call_tool(name, arguments)
        if result.data is not None:
            return result.data
        if result.structured_content is not None:
            return result.structured_content
        texts: List[str] = []
        for block in result.content:
            if isinstance(block, mcp.types.TextContent):
                texts.append(block.text)
        aggregated = "\n".join(texts)
        return {"result": aggregated}

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Synchronously execute a tool by name and return JSON text.

        Args:
            name: Tool name to execute.
            arguments: Tool input arguments mapping.

        Returns:
            A JSON string representing the tool result or an error object.
        """
        server_name = self._tool_servers.get(name)
        if server_name is None:
            logger.warning("Attempted to call unknown MCP tool '%s'", name)
            return json.dumps({"error": f"Unknown tool: {name}"}, ensure_ascii=False)
        cfg = self._servers.get(server_name)
        client = Client({server_name: cfg})
        try:
            data = self._run(self._call_tool_async(client, name, arguments))
        except Exception as e:
            logger.exception("Error executing MCP tool '%s' on server '%s'", name, server_name)
            return json.dumps({"error": f"Tool execution error for {name}: {e}"}, ensure_ascii=False)
        try:
            return json.dumps(data, ensure_ascii=False)
        except Exception:
            return json.dumps({"result": str(data)}, ensure_ascii=False)


__all__ = ["FastMCPClient"]
