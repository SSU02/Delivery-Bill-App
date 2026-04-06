"""
WhatsApp sending via a local Node.js whatsapp-web.js HTTP server.

Architecture:
  DeliveryBillApp (Python)
      → HTTP POST localhost:3000/send
      → whatsapp_server.js  (Node.js, headless Puppeteer)
      → WhatsApp Web

Benefits over pyautogui approach:
  - Completely background: user can use laptop normally while sending
  - Directly sends via WhatsApp Web DOM API (no keyboard tricks)
  - Session persists: scan QR code only once ever
  - Reliable: no window-focus race conditions
"""

from __future__ import annotations

import os
import random
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# ── Constants ─────────────────────────────────────────────────────────────────

SERVER_URL  = "http://127.0.0.1:3000"
def _log_file() -> str:
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), "whatsapp_log.txt")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "whatsapp_log.txt")

LOG_FILE = _log_file()
_LOG_MAX    = 500

_server_proc: Optional[subprocess.Popen] = None

# ── Logging ───────────────────────────────────────────────────────────────────

def _log(line: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        entry = f"[{ts}] {line}\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
        # Keep log compact
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) > _LOG_MAX:
            with open(LOG_FILE, "w", encoding="utf-8") as f:
                f.writelines(lines[-_LOG_MAX:])
    except Exception:
        pass

# ── Phone normalisation ───────────────────────────────────────────────────────

def format_indian_phone(phone: str) -> str:
    """Normalise any Indian number to +91XXXXXXXXXX."""
    if not phone:
        return ""
    digits = "".join(ch for ch in str(phone) if ch.isdigit())
    if len(digits) >= 10:
        return f"+91{digits[-10:]}"
    return ""

# ── Node / npm helpers ────────────────────────────────────────────────────────

def _find_node() -> str:
    path = shutil.which("node")
    if path:
        return path
    for p in [
        r"C:\Program Files\nodejs\node.exe",
        r"C:\Program Files (x86)\nodejs\node.exe",
    ]:
        if os.path.exists(p):
            return p
    return ""


def _find_npm() -> str:
    path = shutil.which("npm")
    if path:
        return path
    for p in [
        r"C:\Program Files\nodejs\npm.cmd",
        r"C:\Program Files (x86)\nodejs\npm.cmd",
    ]:
        if os.path.exists(p):
            return p
    return ""


def _app_dir() -> str:
    """Return the folder that contains whatsapp_server.js.
    When frozen by PyInstaller the JS files live next to the .exe, not in _MEIPASS."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _server_script() -> str:
    return os.path.join(_app_dir(), "whatsapp_server.js")


def _node_modules_ok() -> bool:
    nm = os.path.join(_app_dir(), "node_modules")
    return os.path.isdir(os.path.join(nm, "whatsapp-web.js"))


def node_installed() -> bool:
    return bool(_find_node())


def npm_install() -> Tuple[bool, str]:
    """Run npm install in the app folder. Returns (ok, error_message)."""
    npm = _find_npm()
    if not npm:
        return False, "npm not found. Please install Node.js from https://nodejs.org"
    app_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        result = subprocess.run(
            [npm, "install"],
            cwd=app_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            _log("NPM_INSTALL_OK")
            return True, ""
        err = (result.stderr or result.stdout or "npm install failed").strip()
        _log(f"NPM_INSTALL_FAILED: {err[:200]}")
        return False, err
    except Exception as e:
        return False, str(e)

# ── Server lifecycle ──────────────────────────────────────────────────────────

def _requests():
    try:
        import requests as r
        return r
    except ImportError:
        return None


def is_server_running() -> bool:
    r = _requests()
    if not r:
        return False
    try:
        resp = r.get(f"{SERVER_URL}/status", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


def get_server_status() -> dict:
    """Returns dict with keys: state (str), qr (str | None)."""
    r = _requests()
    if not r:
        return {"state": "offline", "qr": None}
    try:
        resp = r.get(f"{SERVER_URL}/status", timeout=3)
        return resp.json()
    except Exception:
        return {"state": "offline", "qr": None}


def reconnect_whatsapp() -> bool:
    """Ask the running server to reinitialise WhatsApp (generates new QR)."""
    r = _requests()
    if not r:
        return False
    try:
        r.post(f"{SERVER_URL}/reconnect", timeout=3)
        _log("RECONNECT_SENT")
        return True
    except Exception:
        return False


def _kill_existing_server() -> None:
    """Kill any Node process already listening on port 3000."""
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/IM", "node.exe"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        else:
            subprocess.run(["pkill", "-f", "whatsapp_server.js"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
    except Exception:
        pass


def start_server() -> Tuple[bool, str]:
    """Start the Node.js server. Returns (ok, friendly_error)."""
    global _server_proc

    # Always kill any existing stuck Node process and start fresh
    if is_server_running():
        _log("SERVER: killing existing server for clean restart")
        stop_server()
        _kill_existing_server()
        time.sleep(1)

    node = _find_node()
    if not node:
        return False, (
            "Node.js is not installed.\n\n"
            "Please install it from  https://nodejs.org  (LTS version)\n"
            "then restart this app."
        )

    script = _server_script()
    if not os.path.exists(script):
        return False, f"whatsapp_server.js not found at:\n{script}"

    if not _node_modules_ok():
        return False, (
            "WhatsApp packages are not installed yet.\n\n"
            "Please open a terminal in the app folder and run:\n\n"
            "    npm install\n\n"
            "then try again."
        )

    try:
        kwargs: dict = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        node_log = open(
            os.path.join(os.path.dirname(script), "whatsapp_node.log"), "a", encoding="utf-8"
        )
        _server_proc = subprocess.Popen(
            [node, script],
            cwd=os.path.dirname(script),
            stdout=node_log,
            stderr=node_log,
            **kwargs,
        )
        _log(f"SERVER_STARTED pid={_server_proc.pid}")

        # Wait up to 20 s for the HTTP endpoint to come up
        for _ in range(20):
            time.sleep(1)
            if is_server_running():
                _log("SERVER_HTTP_READY")
                return True, ""

        _log("SERVER_TIMEOUT")
        return False, (
            "Server started but did not respond in 20 seconds.\n"
            "Please check that Node.js and the packages are installed correctly."
        )
    except Exception as e:
        _log(f"SERVER_START_ERROR: {e}")
        return False, f"Could not start WhatsApp server:\n{e}"


def stop_server() -> None:
    global _server_proc
    r = _requests()
    if r:
        try:
            r.post(f"{SERVER_URL}/stop", timeout=2)
        except Exception:
            pass
    if _server_proc:
        try:
            _server_proc.terminate()
        except Exception:
            pass
        _server_proc = None
    _log("SERVER_STOPPED")


def logout_whatsapp() -> Tuple[bool, str]:
    r = _requests()
    if not r:
        return False, "requests library not installed"
    try:
        resp = r.post(f"{SERVER_URL}/logout", timeout=10)
        data = resp.json()
        if data.get("ok"):
            _log("LOGGED_OUT")
            return True, ""
        return False, data.get("error", "Logout failed")
    except Exception as e:
        return False, str(e)

# ── Message sending ───────────────────────────────────────────────────────────

def send_single_message(phone: str, message: str) -> Tuple[bool, str]:
    """
    Send a single WhatsApp message via the local Node server.
    Completely background – no window focus, no keyboard automation.
    """
    phone_norm = format_indian_phone(phone)
    if not phone_norm:
        msg = "Invalid phone number. Please enter a 10-digit Indian mobile number."
        _log(f"FAILED phone={phone!r} reason=invalid_phone")
        return False, msg

    if not (message or "").strip():
        _log(f"FAILED phone={phone_norm} reason=empty_message")
        return False, "Message is empty."

    r = _requests()
    if not r:
        return False, (
            "The 'requests' library is not installed.\n"
            "Please run:  pip install requests"
        )

    if not is_server_running():
        return False, (
            "WhatsApp server is not running.\n"
            "Please click 'Connect WhatsApp' first."
        )

    status = get_server_status()
    state  = status.get("state", "unknown")
    if state != "ready":
        if state == "qr":
            return False, "Please scan the QR code to connect WhatsApp first."
        return False, (
            f"WhatsApp is not connected (state: {state}).\n"
            "Please reconnect via the 'Connect WhatsApp' button."
        )

    try:
        resp = r.post(
            f"{SERVER_URL}/send",
            json={"phone": phone_norm, "message": (message or "").strip()},
            timeout=30,
        )
        data = resp.json()
        if data.get("ok"):
            _log(f"SENT phone={phone_norm}")
            return True, ""
        err = data.get("error", "Send failed")
        _log(f"FAILED phone={phone_norm} error={err}")
        return False, err
    except Exception as e:
        _log(f"ERROR phone={phone_norm} err={e}")
        return False, f"Send error: {e}"


@dataclass
class BulkResult:
    sent: int
    failed: int
    results: List[Dict]


def send_bulk_messages(bills_list: List[Dict], delay: int = 5) -> BulkResult:
    sent, failed = 0, 0
    results: List[Dict] = []

    for idx, bill in enumerate(bills_list, 1):
        phone   = format_indian_phone(bill.get("phone", ""))
        name    = bill.get("customer_name", "") or ""
        message = bill.get("message", "")

        ok, err = send_single_message(phone, message)
        results.append({"index": idx, "customer_name": name, "phone": phone, "ok": ok, "error": err})
        if ok:
            sent += 1
        else:
            failed += 1

        if idx < len(bills_list):
            wait_s = max(1, delay + random.randint(-2, 2))
            _log(f"WAIT seconds={wait_s}")
            time.sleep(wait_s)

    _log(f"SUMMARY sent={sent} failed={failed} total={len(bills_list)}")
    return BulkResult(sent=sent, failed=failed, results=results)
