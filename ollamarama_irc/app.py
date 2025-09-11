from __future__ import annotations

import asyncio
import json
import logging
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

from .config import AppConfig, load_config, validate_config
from .history import HistoryStore
from .irc_client import IRCClient
from .ollama_client import OllamaClient
from .handlers import CommandRouter
from .handlers.cmd_ai import make_ai_handler, make_x_handler
from .handlers.cmd_help import make_help_handler
from .handlers.cmd_model import make_model_handler
from .handlers.cmd_prompt import make_persona_handler, make_custom_handler
from .handlers.cmd_reset import make_reset_handler, make_stock_handler
from .handlers.cmd_clear import make_clear_handler
from .handlers.cmd_verbose import make_verbose_handler
from .tools import execute_tool, load_schema
from .fastmcp_client import FastMCPClient
from .text_utils import strip_thinking_markers


log = logging.getLogger(__name__)


class AppContext:
    """Application context bundling config, IRC, model, and tools.

    Args:
        cfg: Loaded application configuration.

    Attributes:
        cfg: Raw configuration object.
        executor: Thread pool for blocking IO.
        log: Package logger.
        nickname: Bot nickname.
        models: Mapping of model keys to ids.
        model: Active model id/name.
        personality: Active system persona.
        options: Default model options.
        timeout: Default request timeout.
        history: Per-channel/user conversation store.
        ollama: HTTP client for the Ollama server.
        irc: IRC client wrapper.
        router: Command router instance.
        tools_schema: Combined MCP + builtin tool schemas.
        tools_enabled: Whether any tools are available.
    """
    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ollama")
        self.log = logging.getLogger("ollamarama_irc")
        self.nickname = cfg.irc.nickname
        self.models = cfg.ollama.models
        self.model = cfg.ollama.default_model or next(iter(self.models.values()), "")
        self.default_personality = cfg.ollama.personality
        self.personality = cfg.ollama.personality
        self.options = cfg.ollama.options
        self.timeout = cfg.ollama.timeout

        self.history = HistoryStore(
            prompt_prefix=cfg.ollama.prompt[0] if cfg.ollama.prompt else "You are ",
            prompt_suffix=cfg.ollama.prompt[1] if len(cfg.ollama.prompt) > 1 else ".",
            personality=self.default_personality,
            prompt_suffix_extra=(cfg.ollama.prompt[2] if len(cfg.ollama.prompt) > 2 else ""),
            max_items=cfg.ollama.history_size,
        )

        base_url = cfg.ollama.api_url.rsplit("/", 1)[0] if "/" in cfg.ollama.api_url else cfg.ollama.api_url
        self.ollama = OllamaClient(base_url=base_url, timeout=cfg.ollama.timeout)
        self.irc = IRCClient(
            server=cfg.irc.server,
            port=6667,
            nickname=cfg.irc.nickname,
            password=cfg.irc.password,
            channels=cfg.irc.channels,
            on_ready=self._on_ready,
            on_message=self._on_message,
        )
        # Early visibility for connection attempts
        try:
            ch_list = ", ".join(cfg.irc.channels) if cfg.irc.channels else "(none)"
            self.log.info(
                "Connecting to %s:%d as %s]",
                cfg.irc.server,
                6667,
                cfg.irc.nickname,
                ch_list,
            )
        except Exception:
            pass

        self.router = CommandRouter(nickname=cfg.irc.nickname)
        self._register_handlers()
        # Verbose handling
        try:
            self.verbose: bool = bool(cfg.ollama.verbose)
            self.history.set_verbose(self.verbose)
        except Exception:
            self.verbose = False

        # Tools & MCP
        self.tools_enabled: bool = True
        self.mcp_client: FastMCPClient | None = None
        self._mcp_tool_names: set[str] = set()
        try:
            builtin_schema = load_schema()
        except Exception:
            self.log.exception("Failed to load builtin tools schema")
            builtin_schema = []
        mcp_schema: List[Dict[str, Any]] = []
        if cfg.ollama.mcp_servers:
            self.log.info("MCP servers configured: %s", list(cfg.ollama.mcp_servers.keys()))
            try:
                # Single consolidated client; one listing pass only
                self.mcp_client = FastMCPClient(cfg.ollama.mcp_servers)
                tools = self.mcp_client.list_tools()
                mcp_schema.extend(tools)
                for tool in tools:
                    fn = (tool.get("function") or {}).get("name")
                    if isinstance(fn, str):
                        self._mcp_tool_names.add(fn)
            except Exception:
                self.log.exception("Failed to initialize/list tools from MCP servers")
                self.mcp_client = None
        combined: List[Dict[str, Any]] = list(mcp_schema)
        for tool in builtin_schema:
            fn = (tool.get("function") or {}).get("name")
            if isinstance(fn, str) and fn not in self._mcp_tool_names:
                combined.append(tool)
        self.tools_schema = combined
        if not self.tools_schema:
            self.tools_enabled = False
            self.log.info("Tool calling disabled: no tools available")

        # Optional health check
        try:
            if not self.ollama.health():
                self.log.warning("Ollama server appears unreachable (health check failed)")
        except Exception:
            self.log.warning("Ollama health check errored; continuing anyway")

    # Handlers registration
    def _register_handlers(self) -> None:
        """Register command handlers and admin-gated handlers."""
        self.router.register(".ai", make_ai_handler(self))
        self.router.register(".x", make_x_handler(self))
        self.router.register(".persona", make_persona_handler(self))
        self.router.register(".custom", make_custom_handler(self))
        self.router.register(".reset", make_reset_handler(self))
        self.router.register(".stock", make_stock_handler(self))
        self.router.register(".help", make_help_handler(self))

        def gate_admin(fn):
            """Decorator factory to allow only admin senders to invoke a handler.

            Args:
                fn: The async handler to wrap.

            Returns:
                A wrapper handler that silently ignores non-admin senders.
            """
            async def _wrapped(channel: str, sender: str, tokens: List[str]):
                """Gate a command to admin users only.

                Args:
                    channel: IRC channel.
                    sender: Nickname issuing the command.
                    tokens: Tokenized input.
                """
                if sender in self.cfg.irc.admins:
                    await fn(channel, sender, tokens)
            return _wrapped

        self.router.register(".model", gate_admin(make_model_handler(self)))
        self.router.register(".clear", gate_admin(make_clear_handler(self)))
        self.router.register(".verbose", gate_admin(make_verbose_handler(self)))

    # IRC callbacks
    def _on_ready(self) -> None:
        """Called once the bot has connected and joined channels."""
        # Schedule welcome messages per channel
        loop = asyncio.get_running_loop()
        for ch in self.cfg.irc.channels:
            loop.create_task(self._send_welcome(ch))

    def _on_message(self, channel: str, sender: str, text: str) -> None:
        """Inbound message handler; delegates to the command router.

        Args:
            channel: IRC channel name.
            sender: Nickname of the author.
            text: Raw message text.
        """
        if sender == self.nickname:
            return
        try:
            # Debug-level log for all inbound lines
            self.log.debug("Inbound %s %s: %s", channel, sender, text)
        except Exception:
            pass
        loop = asyncio.get_running_loop()
        loop.create_task(self.router.dispatch(channel, sender, text))

    # Response helpers
    def chop(self, message: str, width: int = 420) -> List[str]:
        """Wrap a message into lines under a maximum width.

        Args:
            message: Text to wrap.
            width: Maximum line width in characters.

        Returns:
            List of wrapped lines preserving whitespace as much as possible.
        """
        lines = message.splitlines()
        newlines: List[str] = []
        for line in lines:
            if len(line) > width:
                wrapped = textwrap.wrap(
                    line,
                    width=width,
                    drop_whitespace=False,
                    replace_whitespace=False,
                    fix_sentence_endings=True,
                    break_long_words=False,
                )
                newlines.extend(wrapped)
            else:
                newlines.append(line)
        return newlines

    def _strip_thinking_text(self, text: str) -> str:
        """Log and remove any model "thinking" markers from text.

        Args:
            text: Raw model output possibly containing hidden thoughts.

        Returns:
            Text with thinking segments removed.
        """
        # Log thinking if present, then strip via helper
        try:
            if "<think>" in text and "</think>" in text:
                thinking = text.split("</think>", 1)[0].replace("<think>", "").strip()
                self.log.info("Model thinking: %s", thinking)
            if "<|begin_of_thought|>" in text and "<|end_of_thought|>" in text:
                seg = text.split("<|end_of_thought|>", 1)[0]
                seg = seg.replace("<|begin_of_thought|>", "").replace("<|end_of_thought|>", "").strip()
                self.log.info("Model thinking: %s", seg)
        except Exception:
            pass
        return strip_thinking_markers(text)

    async def respond(self, channel: str, user: str, sender2: Optional[str] = None) -> None:
        """Generate and send a model response for a user's history.

        Args:
            channel: IRC channel to send messages to.
            user: Primary user whose conversation to continue.
            sender2: Optional name to address when relaying via ``.x``.
        """
        try:
            messages = self.history.get(channel, user)
            if getattr(self, "tools_enabled", False):
                # Use tool loop in thread
                content = await self.to_thread(self.respond_with_tools, messages)
            else:
                data = await self.to_thread(self.ollama.chat, model=self.model, messages=messages, options=self.options, timeout=self.timeout)
                content = data.get("message", {}).get("content", "")

            content = self._strip_thinking_text((content or "").strip())
            lines = self.chop(content)
            joined = " ".join(lines)

            # Keep in history
            self.history.add(channel, user, "assistant", joined)

            if sender2:
                self.log.info("Sending response to %s in %s: '%s'", sender2, channel, joined)
                self.irc.send_message(channel, f"{sender2}:")
            else:
                self.log.info("Sending response to %s in %s: '%s'", user, channel, joined)
                self.irc.send_message(channel, f"{user}:")
            await asyncio.sleep(1)

            for line in lines:
                self.irc.send_message(channel, line)
                await asyncio.sleep(2)
        except Exception as e:
            self.log.exception("Error producing response: %s", e)
            self.irc.send_message(channel, "Something went wrong, try again.")

    async def _send_welcome(self, channel: str) -> None:
        """Send a one-time welcome message to a channel.

        Args:
            channel: Channel to greet.
        """
        greet = "introduce yourself"
        system = f"{self.history.prompt_prefix}{self.default_personality}{self.history._full_suffix()}"
        try:
            # One-off prompt for welcome
            data = await self.to_thread(
                self.ollama.chat,
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": greet},
                ],
                options=self.options,
                timeout=self.timeout,
            )
            content = data.get("message", {}).get("content", "")
            content = self._strip_thinking_text(content)
            lines = self.chop(content + "  Type .help to learn how to use me.")
            self.log.info("Sending welcome response to %s: '%s'", channel, " ".join(lines))
            for line in lines:
                self.irc.send_message(channel, line)
                await asyncio.sleep(2)
        except Exception as e:
            self.log.exception("Error sending welcome message: %s", e)

    async def to_thread(self, fn, *args, **kwargs) -> Any:
        """Run a blocking function in the thread pool.

        Args:
            fn: Callable to execute in the executor.
            *args: Positional arguments for the callable.
            **kwargs: Keyword arguments for the callable.

        Returns:
            The callable's return value.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, lambda: fn(*args, **kwargs))

    def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """Execute either an MCP or builtin tool based on the name.

        Args:
            name: Tool function name.
            arguments: Tool input arguments.

        Returns:
            A JSON string result produced by the tool.
        """
        try:
            _args_str = json.dumps(arguments or {}, ensure_ascii=False, default=str)
        except Exception:
            _args_str = str(arguments)
        if len(_args_str) > 800:
            _args_str = _args_str[:800] + "…"
        if self.mcp_client is not None and name in self._mcp_tool_names:
            self.log.info("Tool (MCP): %s args=%s", name, _args_str)
            return self.mcp_client.call_tool(name, arguments)
        self.log.info("Tool (builtin): %s args=%s", name, _args_str)
        return execute_tool(name, arguments)

    def respond_with_tools(self, messages: List[Dict[str, Any]], *, tool_choice: str | None = "auto") -> str:
        """Run a tool-calling loop until the model stops requesting tools.

        Args:
            messages: Mutable conversation history to update in-place.
            tool_choice: Tool selection strategy, e.g. ``"auto"`` or ``None``.

        Returns:
            Final assistant content string (may be empty on failure).
        """
        try:
            result = self.ollama.chat_with_tools(
                model=self.model,
                messages=messages,
                options=self.options,
                tools=self.tools_schema,
                tool_choice=tool_choice,
                timeout=self.timeout,
            )
        except Exception:
            self.log.exception("Initial chat_with_tools failed")
            return ""
        max_iterations = 8
        iterations = 0
        while iterations < max_iterations:
            msg = result.get("message", {})
            tool_calls = msg.get("tool_calls") or []
            if not tool_calls:
                break
            try:
                self.log.info("Model requested %d tool call(s)", len(tool_calls))
            except Exception:
                pass
            messages.append(msg)
            for call in tool_calls:
                func = (call.get("function") or {})
                name = func.get("name") or ""
                raw_args = func.get("arguments")
                try:
                    if isinstance(raw_args, str):
                        args = json.loads(raw_args) if raw_args.strip() else {}
                    elif isinstance(raw_args, dict):
                        args = raw_args
                    else:
                        args = {}
                except Exception:
                    self.log.exception("Failed to parse tool arguments for '%s'", name)
                    args = {}
                tool_result = self._execute_tool(name, args)
                tool_msg: Dict[str, Any] = {"role": "tool", "content": str(tool_result)}
                if call.get("id"):
                    tool_msg["tool_call_id"] = call["id"]
                messages.append(tool_msg)
            try:
                result = self.ollama.chat_with_tools(
                    model=self.model,
                    messages=messages,
                    options=self.options,
                    tools=self.tools_schema,
                    tool_choice=tool_choice,
                    timeout=self.timeout,
                )
            except Exception:
                self.log.exception("Follow-up chat_with_tools failed")
                return ""
            iterations += 1
        final = result.get("message", {})
        content = (final.get("content", "") or "").strip()
        messages.append({"role": "assistant", "content": content})
        # Remove tool scaffolding from messages for future compression
        messages[:] = [
            m
            for m in messages
            if not (isinstance(m, dict) and (m.get("role") == "tool" or m.get("tool_calls")))
        ]
        if len(messages) > self.history.max_items:
            if messages and isinstance(messages[0], dict) and messages[0].get("role") == "system":
                messages.pop(1)
            else:
                messages.pop(0)
        return content


def run_app(config_path: Path, *, overrides: Optional[Dict[str, Any]] = None) -> None:
    """Load configuration and run the IRC application.

    Args:
        config_path: Path to the JSON configuration file.
        overrides: Optional config overrides to merge before starting.

    Raises:
        SystemExit: With code 2 when configuration validation fails.
    """
    cfg = load_config(config_path, overrides=overrides)
    ok, errs = validate_config(cfg) if 'validate_config' in globals() else (True, [])
    if not ok:
        for e in errs:
            log = logging.getLogger("ollamarama_irc")
            log.error(e)
        raise SystemExit(2)
    ctx = AppContext(cfg)

    async def runner():
        """Run the IRC loop and handle graceful shutdown signals."""
        # Graceful shutdown handling
        import signal
        stop = asyncio.Event()
        try:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                try:
                    loop.add_signal_handler(sig, stop.set)
                except Exception:
                    pass
        except Exception:
            pass

        task = asyncio.create_task(ctx.irc.run_async())
        stop_task = asyncio.create_task(stop.wait())
        try:
            done, pending = await asyncio.wait({task, stop_task}, return_when=asyncio.FIRST_COMPLETED)
            # Drain exceptions to avoid 'Task exception was never retrieved'
            for t in done:
                try:
                    await t
                except Exception as e:
                    logging.getLogger("ollamarama_irc").exception("Background task failed: %s", e)
            for t in pending:
                t.cancel()
        except KeyboardInterrupt:
            pass
        finally:
            try:
                ctx.irc.shutdown()
            except Exception:
                pass
            try:
                if hasattr(ctx, "executor"):
                    ctx.executor.shutdown(wait=False, cancel_futures=True)  # type: ignore[attr-defined]
            except Exception:
                pass

    asyncio.run(runner())
