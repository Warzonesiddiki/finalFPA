"""Unit tests for Desktop Shell Hardening per 09 §3.6, §7.4 and 15 §4, §6, §12.

Covers:
- Windows Single-Instance Mutex (acquire, duplicate detection, release)
- Port binding fallback and loopback IP compliance
- Clean process shutdown logic
- WebView2 detection and browser launch fallback (ERR-ENG-001)
"""

import socket
import sys
from unittest.mock import MagicMock, patch

from app.desktop.shell import (
    SingleInstanceMutex,
    find_free_port,
    is_webview2_available,
    launch_app,
    launch_browser_fallback,
    shutdown_process,
)


def test_single_instance_mutex_acquire_and_release():
    """Verify single-instance mutex can be acquired and cleanly released."""
    mutex_name = "FPAndAMonthEndCopilot_Test_Mutex_1"
    m1 = SingleInstanceMutex(name=mutex_name)
    acquired = m1.acquire()
    assert acquired is True
    assert m1.already_running is False

    # Second instance with same name should fail to acquire on Windows
    if sys.platform == "win32":
        m2 = SingleInstanceMutex(name=mutex_name)
        acquired_2 = m2.acquire()
        assert acquired_2 is False
        assert m2.already_running is True
        m2.release()

    m1.release()

    # After release, acquisition should succeed again
    if sys.platform == "win32":
        m3 = SingleInstanceMutex(name=mutex_name)
        assert m3.acquire() is True
        m3.release()


def test_find_free_port_fallback():
    """Verify free port finder returns a valid bindable 127.0.0.1 port."""
    port = find_free_port()
    assert isinstance(port, int)
    assert 1024 <= port <= 65535

    # Verify that the returned port was actually free to bind
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", port))


def test_find_free_port_with_conflict():
    """Verify port finder falls back if specified start_port is occupied."""
    # Occupy a temporary port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    occupied_port = sock.getsockname()[1]

    try:
        fallback_port = find_free_port(start_port=occupied_port, max_attempts=2)
        assert fallback_port != occupied_port
        assert isinstance(fallback_port, int)
    finally:
        sock.close()


def test_is_webview2_available():
    """Verify is_webview2_available executes without error."""
    avail = is_webview2_available()
    assert isinstance(avail, bool)


def test_launch_browser_fallback():
    """Verify launch_browser_fallback delegates to webbrowser.open."""
    with patch("webbrowser.open") as mock_open:
        test_url = "http://127.0.0.1:8000/#token=abc123"
        launch_browser_fallback(test_url)
        mock_open.assert_called_once_with(test_url)


def test_shutdown_process_cleanly():
    """Verify shutdown_process signals uvicorn server and releases mutex."""
    mock_server = MagicMock()
    mock_server.should_exit = False

    mock_mutex = MagicMock()

    with (
        patch("app.desktop.shell._server_instance", mock_server),
        patch("app.desktop.shell._mutex_handle", mock_mutex),
    ):
        shutdown_process()
        assert mock_server.should_exit is True
        mock_mutex.release.assert_called_once()


def test_launch_app_blocked_by_mutex():
    """Verify launch_app returns False if mutex is held by existing instance (ERR-ENG-008)."""
    with (
        patch.object(SingleInstanceMutex, "acquire", return_value=False),
        patch("app.desktop.shell._show_instance_already_running_message") as mock_msg,
    ):
        result = launch_app(project_id="test_blocked")
        assert result is False
        mock_msg.assert_called_once()


def test_launch_app_browser_fallback_mode():
    """Verify launch_app falls back to browser when prefer_browser is True."""
    with (
        patch.object(SingleInstanceMutex, "acquire", return_value=True),
        patch.object(SingleInstanceMutex, "release"),
        patch("threading.Thread"),
        patch("time.sleep"),
        patch("app.desktop.shell.launch_browser_fallback") as mock_browser,
    ):
        # Server thread is mocked as not alive immediately to exit loop
        mock_thread = MagicMock()
        mock_thread.is_alive.return_value = False
        with patch("threading.Thread", return_value=mock_thread):
            result = launch_app(project_id="test_browser", prefer_browser=True)
            assert result is True
            mock_browser.assert_called_once()
