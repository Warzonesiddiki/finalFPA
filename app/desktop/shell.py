"""Desktop window shell launching pywebview on local FastAPI loopback per ADR-001, ADR-009, 09 §3.6, §7.4, and 15 §4, §6, §12.

Features:
- Windows single-instance mutex (per-project or global) to prevent double-launching (09 §7.4, FR-PRJ-006, ERR-ENG-008)
- Clean process shutdown handling (signal listeners, uvicorn server graceful shutdown)
- Port binding fallback (retry and free port scanning with loopback validation)
- Browser launch fallback if WebView2 is missing or fails to initialize (15 §4.1, §6.1, §6.3, ERR-ENG-001)
"""

import ctypes
import os
import signal
import socket
import sys
import threading
import time
import webbrowser
from typing import Optional, Tuple
import uvicorn

from app import __version__, __app_name__
from app.api.main import app, get_session_token

# Windows API constants
ERROR_ALREADY_EXISTS = 183
MUTEX_ALL_ACCESS = 0x1F0001
SW_RESTORE = 9

# Global reference to server instance for clean shutdown
_server_instance: Optional[uvicorn.Server] = None
_server_thread: Optional[threading.Thread] = None
_mutex_handle: Optional[int] = None


class SingleInstanceMutex:
    """Manages a named Windows Mutex to prevent multiple concurrent instances per 09 §7.4."""

    def __init__(self, name: str = "FPAndAMonthEndCopilot_GlobalMutex"):
        self.name = name
        self.handle: Optional[int] = None
        self.already_running: bool = False

    def acquire(self) -> bool:
        """Attempt to create and acquire the named mutex.
        
        Returns True if acquired (first instance), False if already running.
        """
        if sys.platform != "win32":
            # For non-Windows environments (tests or dev containers), emulate or pass
            return True

        try:
            # CreateMutexW(lpMutexAttributes, bInitialOwner, lpName)
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.CreateMutexW(None, True, self.name)
            last_error = kernel32.GetLastError()

            if last_error == ERROR_ALREADY_EXISTS:
                self.already_running = True
                if handle:
                    kernel32.CloseHandle(handle)
                self.handle = None
                return False

            self.handle = handle
            self.already_running = False
            return True
        except Exception:
            # If ctypes fails, don't crash the launch
            return True

    def release(self) -> None:
        """Release and close the mutex handle on clean shutdown."""
        if self.handle and sys.platform == "win32":
            try:
                kernel32 = ctypes.windll.kernel32
                kernel32.ReleaseMutex(self.handle)
                kernel32.CloseHandle(self.handle)
            except Exception:
                pass
            finally:
                self.handle = None


def find_free_port(start_port: int = 0, max_attempts: int = 5) -> int:
    """Find a free loopback port on 127.0.0.1 per ADR-009 with retry fallback."""
    if start_port > 0:
        for offset in range(max_attempts):
            candidate = start_port + offset
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("127.0.0.1", candidate))
                    return candidate
            except OSError:
                continue

    # Ephemeral port binding fallback
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_server(port: int) -> uvicorn.Server:
    """Start uvicorn server instance."""
    global _server_instance
    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=port,
        log_level="error",
        access_log=False,
    )
    server = uvicorn.Server(config)
    _server_instance = server
    server.run()
    return server


def shutdown_process() -> None:
    """Cleanly terminate uvicorn server, release mutex, and shut down process."""
    global _server_instance, _mutex_handle
    if _server_instance:
        _server_instance.should_exit = True

    if _mutex_handle:
        try:
            _mutex_handle.release()
        except Exception:
            pass


def _setup_signal_handlers() -> None:
    """Register signal handlers for clean termination on SIGINT and SIGTERM."""
    def _sig_handler(signum, frame):
        shutdown_process()
        sys.exit(0)

    try:
        signal.signal(signal.SIGINT, _sig_handler)
        signal.signal(signal.SIGTERM, _sig_handler)
    except (ValueError, AttributeError):
        # In non-main thread or unsupported OS signal environments
        pass


def is_webview2_available() -> bool:
    """Check if Microsoft Edge WebView2 runtime is installed on the Windows system."""
    if sys.platform != "win32":
        return True

    try:
        import winreg
        # Check standard 64-bit and 32-bit registry locations for WebView2
        subkeys = [
            r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-F552-44E6-B60F-9E74E7668077}",
            r"SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-F552-44E6-B60F-9E74E7668077}",
        ]
        for subkey in subkeys:
            for root in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                try:
                    with winreg.OpenKey(root, subkey) as key:
                        val, _ = winreg.QueryValueEx(key, "pv")
                        if val and str(val).strip() != "" and str(val).strip() != "0.0.0.0":
                            return True
                except OSError:
                    continue
        return False
    except Exception:
        # Default to True so pywebview can attempt its own check/initialization
        return True


def launch_browser_fallback(target_url: str) -> None:
    """Documented fallback per ADR-001, ADR-009, and 15 §4.1 / §6.3 (ERR-ENG-001).
    
    Opens the default system browser at the local loopback URL.
    """
    webbrowser.open(target_url)


def launch_app(
    project_id: str = "default",
    prefer_browser: bool = False,
    start_port: int = 0,
) -> bool:
    """Launch the application shell with single-instance protection, clean shutdown, and fallback.
    
    Returns True if launched, False if blocked by an existing instance (ERR-ENG-008).
    """
    global _mutex_handle, _server_thread

    # 1. Enforce single-instance mutex per 09 §7.4 and 15 §6.3
    mutex_name = f"FPAndAMonthEndCopilot_Project_{project_id}"
    mutex = SingleInstanceMutex(name=mutex_name)
    if not mutex.acquire():
        # Instance already running: per 09 §7.4, don't crash, report friendly error / bring to front
        _show_instance_already_running_message()
        return False

    _mutex_handle = mutex

    # 2. Setup clean shutdown handlers
    _setup_signal_handlers()

    # 3. Port binding with fallback
    port = find_free_port(start_port=start_port)
    token = get_session_token()

    # 4. Start FastAPI backend in dedicated background thread
    server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
    _server_thread = server_thread
    server_thread.start()

    # Give server a brief moment to bind socket
    time.sleep(0.3)

    target_url = f"http://127.0.0.1:{port}/#token={token}"

    # 5. Check WebView2 presence or browser preference
    use_browser = prefer_browser or (sys.platform == "win32" and not is_webview2_available())

    if use_browser:
        launch_browser_fallback(target_url)
        # Keep process alive until signal/keyboard interrupt if in browser mode
        try:
            while server_thread.is_alive():
                time.sleep(1.0)
        except KeyboardInterrupt:
            shutdown_process()
        return True

    # 6. Launch pywebview window with fallback to browser if pywebview fails
    try:
        import webview

        window = webview.create_window(
            title=f"{__app_name__} v{__version__}",
            url=target_url,
            width=1400,
            height=900,
            min_size=(1366, 768),
            confirm_close=True,
        )

        def _on_closed():
            shutdown_process()

        window.events.closed += _on_closed
        webview.start(debug=False)
    except Exception as e:
        # Fallback to default browser if WebView2 or pywebview fails (ERR-ENG-001)
        launch_browser_fallback(target_url)
        try:
            while server_thread.is_alive():
                time.sleep(1.0)
        except KeyboardInterrupt:
            shutdown_process()
    finally:
        shutdown_process()

    return True


def _show_instance_already_running_message() -> None:
    """Inform user that project is already running per 09 §7.4 and ERR-ENG-008."""
    msg = (
        "This project is already open in another window.\n\n"
        "Please switch to the open window."
    )
    if sys.platform == "win32":
        try:
            # MB_OK | MB_ICONINFORMATION = 0x00000040
            ctypes.windll.user32.MessageBoxW(0, msg, f"{__app_name__}", 0x00000040)
            return
        except Exception:
            pass
    print(f"[{__app_name__}] {msg}", file=sys.stderr)


if __name__ == "__main__":
    launch_app()
