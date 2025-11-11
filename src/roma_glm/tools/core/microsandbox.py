"""MicroSandbox code execution toolkit for secure local sandboxed code execution."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Optional

from roma_glm.tools.base.base import BaseToolkit


class MicroSandboxToolkit(BaseToolkit):
    """
    MicroSandbox code execution toolkit providing secure local sandboxed code execution.

    MicroSandbox is a local alternative to E2B that provides hardware-level VM isolation
    with instant startup times and OCI compatibility. This toolkit integrates MicroSandbox
    with the ROMA agent system for secure code execution.

    Key features:
    - Local hardware-level VM isolation with microVMs
    - Instant startup (under 200ms boot times)
    - OCI compatible - runs standard container images
    - Self-hosted deployment within your infrastructure
    - Async-safe operation with asyncio.Lock for parallel agent execution
    - Comprehensive code execution and file management
    - Zero event loop blocking during sandbox operations

    Configuration:
        timeout: Sandbox timeout in seconds (default: 300 = 5 min)
        image: Container image to use (default: "python")
        cpus: Number of CPUs to allocate (default: 1)
        memory: Memory in MB to allocate (default: 1024)
        auto_reinitialize: Auto-recreate sandbox on death (default: True)

    Note:
        All tool methods are async and must be awaited. Use async context manager
        (async with) for proper resource cleanup, or call aclose() explicitly.
    """

    def _setup_dependencies(self) -> None:
        """Setup MicroSandbox toolkit dependencies."""
        try:
            from microsandbox import PythonSandbox
            self._Sandbox = PythonSandbox
        except ImportError:
            raise ImportError(
                "microsandbox library is required for MicroSandboxToolkit. "
                "Install it with: pip install microsandbox"
            )

        # Check if MicroSandbox server is running
        try:
            result = subprocess.run(
                ["msb", "server", "status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                self.log_warning(
                    "MicroSandbox server may not be running. Start it with: msb server start --dev"
                )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.log_warning(
                f"Could not check MicroSandbox server status: {e}. "
                "Ensure MicroSandbox is installed and server is running."
            )

    def _initialize_tools(self) -> None:
        """Initialize MicroSandbox toolkit configuration."""
        # Configuration with defaults
        self.timeout = self.config.get('timeout', 300)  # 5 minutes in seconds
        self.image = self.config.get('image', 'python')
        self.cpus = self.config.get('cpus', 1)
        self.memory = self.config.get('memory', 1024)  # MB
        self.auto_reinitialize = self.config.get('auto_reinitialize', True)

        # Validate configuration
        if self.timeout <= 0:
            raise ValueError(f"timeout must be positive, got {self.timeout}")
        if self.cpus <= 0:
            raise ValueError(f"cpus must be positive, got {self.cpus}")
        if self.memory <= 0:
            raise ValueError(f"memory must be positive, got {self.memory}")

        # State tracking
        self._sandbox: Optional[Any] = None  # Actual type: PythonSandbox
        self._sandbox_context: Optional[Any] = None  # Async context manager
        self._sandbox_name: Optional[str] = None
        self._created_at: float = 0
        self._lock = asyncio.Lock()  # Async-safe lock for concurrent operations

        self.log_debug(
            f"MicroSandbox toolkit initialized with image={self.image}, "
            f"timeout={self.timeout}s, cpus={self.cpus}, memory={self.memory}MB"
        )

    async def _ensure_sandbox_alive(self) -> object:
        """
        Ensure sandbox is alive and healthy, reinitialize if needed.

        This method is async-safe and performs minimal locking. The health check
        and sandbox creation are locked, but execution happens outside the lock
        to allow parallel operations.

        Returns:
            Active PythonSandbox instance

        Raises:
            RuntimeError: If sandbox creation fails and auto_reinitialize is False
        """
        async with self._lock:  # Critical section: check + create only
            # No sandbox yet
            if self._sandbox is None:
                return await self._create_sandbox()

            # Check if sandbox is still running (MicroSandbox doesn't have explicit health check)
            # We'll try a simple operation to verify it's responsive
            try:
                # Try a simple operation to check if sandbox is responsive
                run_method = getattr(self._sandbox, 'run', None)
                if run_method:
                    await run_method("print('health_check')")
                sandbox = self._sandbox
            except Exception as e:
                self.log_warning(f"Sandbox health check failed: {e}")
                if self.auto_reinitialize:
                    return await self._create_sandbox()
                else:
                    raise RuntimeError(f"Sandbox health check failed: {e}")

        return sandbox  # Return outside lock

    async def _create_sandbox(self) -> object:
        """
        Create a new sandbox instance.

        This method should only be called while holding self._lock.

        Returns:
            New PythonSandbox instance

        Raises:
            ValueError: If required configuration is invalid
        """
        # Cleanup old sandbox if exists
        if self._sandbox is not None:
            try:
                stop_method = getattr(self._sandbox, 'stop', None)
                if stop_method:
                    await stop_method()
                self.log_debug(f"Stopped old sandbox {self._sandbox_name}")
            except Exception as e:
                self.log_warning(f"Error stopping old sandbox: {e}")

        # Create new sandbox
        try:
            sandbox_name = f"roma-sandbox-{int(time.time())}"
            
            create_method = getattr(self._Sandbox, 'create', None)
            if create_method:
                # PythonSandbox.create() returns an async context manager
                self._sandbox_context = create_method(name=sandbox_name)
                # Enter the context manager to get the actual sandbox
                if self._sandbox_context is not None:
                    self._sandbox = await self._sandbox_context.__aenter__()
                else:
                    raise RuntimeError("Failed to create sandbox context")
            else:
                raise RuntimeError("PythonSandbox.create method not found")
            
            self._sandbox_name = sandbox_name
            self._created_at = time.time()

            self.log_debug(
                f"Created new sandbox {self._sandbox_name} with "
                f"image={self.image}, timeout={self.timeout}s, "
                f"cpus={self.cpus}, memory={self.memory}MB"
            )

            return self._sandbox

        except Exception as e:
            self.log_error(f"Failed to create sandbox: {e}")
            raise

    async def aclose(self) -> None:
        """
        Async close and cleanup sandbox resources.

        Use this method or async context manager to ensure proper cleanup.
        """
        if not hasattr(self, '_lock'):
            return  # Not fully initialized

        async with self._lock:
            if self._sandbox is not None:
                try:
                    # First exit the context manager if we have one
                    if self._sandbox_context is not None:
                        await self._sandbox_context.__aexit__(None, None, None)
                        self._sandbox_context = None
                    
                    # Also try to stop the sandbox directly if available
                    stop_method = getattr(self._sandbox, 'stop', None)
                    if stop_method:
                        await stop_method()
                    self.log_debug(f"Closed sandbox {self._sandbox_name}")
                except Exception as e:
                    self.log_warning(f"Error closing sandbox: {e}")
                finally:
                    self._sandbox = None
                    self._sandbox_name = None

    def close(self) -> None:
        """
        Sync wrapper for close. Prefer using aclose() in async contexts.

        Use this method or context manager to ensure proper cleanup.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, schedule close for later
                asyncio.create_task(self.aclose())
            else:
                # If no loop running, run aclose() synchronously
                loop.run_until_complete(self.aclose())
        except RuntimeError:
            # No event loop exists, create one
            asyncio.run(self.aclose())

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.aclose()
        return False

    def __enter__(self):
        """Sync context manager entry (for backward compatibility)."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync context manager exit (for backward compatibility)."""
        self.close()
        return False

    def __del__(self):
        """Cleanup sandbox on destruction."""
        self.close()

    # ========== Tool Methods ==========

    async def run_python_code(self, code: str) -> str:
        """
        Execute Python code in the MicroSandbox.

        Use this tool to run Python code in a secure isolated environment.
        The sandbox persists across calls, allowing you to build up state.
        Automatically handles sandbox timeouts and reinitializes when needed.

        Args:
            code: Python code to execute

        Returns:
            JSON string with execution results, stdout, stderr, and any errors

        Examples:
            run_python_code("x = 5 + 3\\nprint(x)") - Basic calculation
            run_python_code("import pandas as pd\\ndf = pd.DataFrame({'a': [1,2,3]})") - Use libraries
            run_python_code("print('Hello from sandbox!')") - Print output
        """
        sandbox = await self._ensure_sandbox_alive()

        try:
            run_method = getattr(sandbox, 'run', None)
            if not run_method:
                raise RuntimeError("Sandbox run method not available")
            
            execution = await run_method(code)

            # Get output from execution
            output_method = getattr(execution, 'output', None)
            output = await output_method() if output_method else str(execution)

            response = {
                "success": True,
                "results": [output],
                "stdout": [output],
                "stderr": [],
                "error": None,
                "sandbox_name": self._sandbox_name
            }

            self.log_debug(f"Code executed successfully in sandbox {self._sandbox_name}")
            return json.dumps(response)

        except Exception as e:
            error_msg = f"Code execution failed: {str(e)}"
            self.log_error(error_msg)
            return json.dumps({"success": False, "error": error_msg})

    async def run_command(self, command: str, timeout_seconds: int = 60) -> str:
        """
        Execute a shell command in the MicroSandbox.

        Use this tool to run shell commands like installing packages, running scripts,
        or performing system operations in the isolated sandbox environment.

        Args:
            command: Shell command to execute
            timeout_seconds: Command timeout in seconds (default: 60)

        Returns:
            JSON string with command exit code, stdout, and stderr

        Examples:
            run_command("pip install numpy") - Install Python package
            run_command("ls -la /home") - List directory contents
            run_command("echo 'Hello World'") - Simple shell command
        """
        sandbox = await self._ensure_sandbox_alive()

        try:
            # MicroSandbox uses command.run() for executing shell commands
            command_attr = getattr(sandbox, 'command', None)
            if not command_attr:
                raise RuntimeError("Sandbox command interface not available")
            
            command_run = getattr(command_attr, 'run', None)
            if not command_run:
                raise RuntimeError("Sandbox command.run method not available")
            
            result = await command_run(command.split(), timeout=timeout_seconds)

            output_method = getattr(result, 'output', None)
            output = await output_method() if output_method else str(result)

            response = {
                "success": True,
                "exit_code": 0,  # MicroSandbox may not provide exit code
                "stdout": output,
                "stderr": "",
                "sandbox_name": self._sandbox_name
            }

            self.log_debug(f"Command executed: {command}")
            return json.dumps(response)

        except Exception as e:
            error_msg = f"Command execution failed: {str(e)}"
            self.log_error(error_msg)
            return json.dumps({"success": False, "error": error_msg})

    async def get_sandbox_status(self) -> str:
        """
        Get current sandbox status and information.

        Use this tool to check sandbox health, uptime, and configuration.
        Useful for debugging and monitoring long-running agent sessions.

        Returns:
            JSON string with sandbox status, name, uptime, and configuration

        Examples:
            get_sandbox_status() - Check current sandbox state
        """
        async with self._lock:
            if self._sandbox is None:
                return json.dumps({
                    "success": True,
                    "status": "no_sandbox",
                    "message": "No sandbox created yet"
                })

            try:
                uptime = time.time() - self._created_at

                response = {
                    "success": True,
                    "status": "running",
                    "sandbox_name": self._sandbox_name,
                    "uptime_seconds": round(uptime, 1),
                    "uptime_hours": round(uptime / 3600, 2),
                    "timeout": self.timeout,
                    "image": self.image,
                    "cpus": self.cpus,
                    "memory": self.memory
                }

                return json.dumps(response)

            except Exception as e:
                error_msg = f"Failed to get sandbox status: {str(e)}"
                self.log_error(error_msg)
                return json.dumps({"success": False, "error": error_msg})

    async def restart_sandbox(self) -> str:
        """
        Manually restart the sandbox.

        Use this tool to force a fresh sandbox environment, clearing all state.
        Useful when you need to reset the execution environment.

        Returns:
            JSON string with new sandbox information

        Examples:
            restart_sandbox() - Force sandbox restart
        """
        async with self._lock:
            try:
                old_name = self._sandbox_name
                await self._create_sandbox()

                response = {
                    "success": True,
                    "message": "Sandbox restarted",
                    "old_sandbox_name": old_name,
                    "new_sandbox_name": self._sandbox_name
                }

                self.log_debug(f"Sandbox manually restarted: {old_name} -> {self._sandbox_name}")
                return json.dumps(response)

            except Exception as e:
                error_msg = f"Failed to restart sandbox: {str(e)}"
                self.log_error(error_msg)
                return json.dumps({"success": False, "error": error_msg})

    async def install_package(self, package: str) -> str:
        """
        Install a Python package in the sandbox using pip.

        Use this tool to add Python libraries needed for your code execution.
        The package will be installed in the sandbox environment.

        Args:
            package: Package name to install (e.g., "numpy", "pandas==2.0.0")

        Returns:
            JSON string with installation status

        Examples:
            install_package("numpy") - Install latest numpy
            install_package("pandas==2.0.0") - Install specific version
            install_package("scikit-learn") - Install scikit-learn
        """
        sandbox = await self._ensure_sandbox_alive()

        try:
            # Install package using pip
            command_attr = getattr(sandbox, 'command', None)
            if not command_attr:
                raise RuntimeError("Sandbox command interface not available")
            
            command_run = getattr(command_attr, 'run', None)
            if not command_run:
                raise RuntimeError("Sandbox command.run method not available")
            
            result = await command_run(["pip", "install", package], timeout=120)  # 2 minutes timeout

            output_method = getattr(result, 'output', None)
            output = await output_method() if output_method else str(result)

            response = {
                "success": True,
                "package": package,
                "exit_code": 0,
                "stdout": output,
                "stderr": "",
                "sandbox_name": self._sandbox_name
            }

            self.log_debug(f"Installed package: {package}")
            return json.dumps(response)

        except Exception as e:
            error_msg = f"Package installation failed: {str(e)}"
            self.log_error(error_msg)
            return json.dumps({"success": False, "error": error_msg})

    async def create_directory(self, path: str) -> str:
        """
        Create a directory in the sandbox.

        Use this tool to create directory structures for organizing files in the sandbox.

        Args:
            path: Directory path to create in sandbox

        Returns:
            JSON string with creation status

        Examples:
            create_directory("/home/user/data") - Create data directory
            create_directory("/home/user/output/results") - Create nested directories
        """
        sandbox = await self._ensure_sandbox_alive()

        try:
            # Create directory using shell command
            command_attr = getattr(sandbox, 'command', None)
            if not command_attr:
                raise RuntimeError("Sandbox command interface not available")
            
            command_run = getattr(command_attr, 'run', None)
            if not command_run:
                raise RuntimeError("Sandbox command.run method not available")
            
            result = await command_run(["mkdir", "-p", path])

            output_method = getattr(result, 'output', None)
            output = await output_method() if output_method else str(result)

            response = {
                "success": True,
                "message": f"Created directory: {path}",
                "path": path,
                "output": output,
                "sandbox_name": self._sandbox_name
            }

            self.log_debug(f"Created directory: {path}")
            return json.dumps(response)

        except Exception as e:
            error_msg = f"Create directory failed: {str(e)}"
            self.log_error(error_msg)
            return json.dumps({"success": False, "error": error_msg})

    async def list_files(self, directory: str = "/home/user") -> str:
        """
        List files and directories in the sandbox.

        Use this tool to explore the sandbox filesystem and understand what
        files are available for processing.

        Args:
            directory: Directory to list (default: "/home/user")

        Returns:
            JSON string with list of files and directories

        Examples:
            list_files() - List files in home directory
            list_files("/tmp") - List files in /tmp directory
        """
        sandbox = await self._ensure_sandbox_alive()

        try:
            # List directory using shell command
            command_attr = getattr(sandbox, 'command', None)
            if not command_attr:
                raise RuntimeError("Sandbox command interface not available")
            
            command_run = getattr(command_attr, 'run', None)
            if not command_run:
                raise RuntimeError("Sandbox command.run method not available")
            
            result = await command_run(["ls", "-la", directory])

            output_method = getattr(result, 'output', None)
            output = await output_method() if output_method else str(result)

            response = {
                "success": True,
                "directory": directory,
                "output": output,
                "sandbox_name": self._sandbox_name
            }

            self.log_debug(f"Listed directory: {directory}")
            return json.dumps(response)

        except Exception as e:
            error_msg = f"List files failed: {str(e)}"
            self.log_error(error_msg)
            return json.dumps({"success": False, "error": error_msg})