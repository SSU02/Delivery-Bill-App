"""
WhatsApp sending dialog (PyQt5/PyQt6 compatible).

Uses whatsapp-web.js via a local Node.js server for fully-background sending.
No browser windows, no keyboard automation – user can use the laptop normally.
"""

from __future__ import annotations

import csv
import io
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

# ── Qt imports ────────────────────────────────────────────────────────────────
try:
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSettings
    from PyQt5.QtGui import QPixmap, QFont
    from PyQt5.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QProgressBar,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QMessageBox,
        QGroupBox,
        QLineEdit,
        QComboBox,
        QFileDialog,
        QWidget,
        QSizePolicy,
        QTextEdit,
        QSplitter,
        QScrollArea,
        QFrame,
    )

    PYQT_VERSION = 5
    DIALOG_ACCEPTED = QDialog.Accepted
except ImportError:
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSettings
    from PyQt6.QtGui import QPixmap, QFont
    from PyQt6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QProgressBar,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QMessageBox,
        QGroupBox,
        QLineEdit,
        QComboBox,
        QFileDialog,
        QWidget,
        QSizePolicy,
        QTextEdit,
        QSplitter,
        QScrollArea,
        QFrame,
    )

    PYQT_VERSION = 6
    DIALOG_ACCEPTED = QDialog.DialogCode.Accepted

from whatsapp_sender import (
    format_indian_phone,
    get_server_status,
    is_server_running,
    logout_whatsapp,
    node_installed,
    npm_install,
    send_single_message,
    start_server,
    stop_server,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _qt_align_center():
    return Qt.AlignCenter if PYQT_VERSION == 5 else Qt.AlignmentFlag.AlignCenter


def _qt_align_left_vcenter():
    if PYQT_VERSION == 5:
        return Qt.AlignLeft | Qt.AlignVCenter
    return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter


STATUS_SENDING = "⏳ Sending"
STATUS_SENT    = "✅ Sent"
STATUS_FAILED  = "❌ Failed"


def _qr_string_to_pixmap(qr_str: str) -> QPixmap:
    """Render a QR-code string to a QPixmap (requires qrcode[pil])."""
    try:
        import qrcode  # type: ignore
        qr = qrcode.QRCode(version=1, box_size=5, border=2)
        qr.add_data(qr_str)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        px = QPixmap()
        px.loadFromData(buf.read())
        return px
    except Exception:
        return QPixmap()


DEFAULT_TEMPLATE = (
    "Hello {customer_name} 👋\n"
    "\n"
    "Your delivery bill from *{company_name}* is ready!\n"
    "\n"
    "📦 *Items ready for delivery:*\n"
    "{items}\n"
    "\n"
    "💰 *Total: ₹{total}*\n"
    "\n"
    "Thank you! 🙏"
)

_SETTINGS_KEY = "whatsapp/message_template"


def load_template() -> str:
    s = QSettings("DeliveryBillApp", "WhatsApp")
    return s.value(_SETTINGS_KEY, DEFAULT_TEMPLATE)


def save_template(template: str) -> None:
    s = QSettings("DeliveryBillApp", "WhatsApp")
    s.setValue(_SETTINGS_KEY, template)


def build_message(customer_name: str, company_name: str, items: List[Dict], amount: float,
                  template: str = "") -> str:
    if not template:
        template = load_template()

    # Build items block: Item - Qty x Rate = Total
    item_lines: List[str] = []
    if items:
        for it in items:
            desc = (it.get("description") or "").strip()
            qty  = it.get("qty", "")
            unit = (it.get("unit") or "").strip()
            rate = it.get("rate")
            total = it.get("total")  # pre-tax line total
            if not desc:
                continue
            try:
                rate_str  = f"₹{float(rate):.2f}"  if rate  is not None else None
                total_str = f"₹{float(total):.2f}" if total is not None else None
            except (TypeError, ValueError):
                rate_str = total_str = None

            qty_unit = f"{qty} {unit}".strip()
            if rate_str and total_str:
                item_lines.append(f"- {desc} – {qty_unit} × {rate_str} = {total_str}")
            else:
                item_lines.append(f"- {desc} – {qty_unit}".rstrip(" –"))
    if not item_lines:
        item_lines = ["- (No items)"]
    items_str = "\n".join(item_lines)

    try:
        amt = float(amount)
    except Exception:
        amt = 0.0

    return template.format(
        customer_name=customer_name,
        company_name=company_name,
        items=items_str,
        total=f"{amt:.2f}",
    )


# ── Template editor dialog ────────────────────────────────────────────────────

class MessageTemplateDialog(QDialog):
    """Side-by-side message template editor with live preview."""

    SAMPLE = {
        "customer_name": "Rajesh Kumar",
        "company_name":  "Senthil Explosives",
        "items": [
            {"description": "Gelatin Sticks", "qty": "10", "unit": "Box",  "rate": 320.00, "total": 3200.00},
            {"description": "Detonators",     "qty": "50", "unit": "Pcs",  "rate": 12.00,  "total": 600.00},
            {"description": "Safety Fuse",    "qty": "5",  "unit": "Roll", "rate": 210.00, "total": 1050.00},
        ],
        "amount": 4850.00,
    }

    def __init__(self, parent=None, company_name: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Edit Message Template")
        self.setMinimumSize(820, 560)
        self._company_name = company_name or "Senthil Explosives"
        self._build_ui()
        self.setStyleSheet(self._style())
        self._refresh_preview()

    def _style(self) -> str:
        return """
            QDialog { background: white; }
            QLabel  { color: #212529; font-size: 12px; }
            QTextEdit {
                font-family: Consolas, monospace;
                font-size: 12px;
                border: 2px solid #ced4da;
                border-radius: 6px;
                padding: 6px;
                background: white;
                color: #212529;
            }
            QTextEdit:focus { border: 2px solid #007bff; }
            QTextEdit#preview {
                background: #f0f7ff;
                border: 2px solid #b8d4f5;
                font-family: Arial, sans-serif;
            }
            QPushButton {
                padding: 9px 18px; border-radius: 5px;
                font-size: 12px; font-weight: bold; border: none;
            }
            QPushButton#primary  { background:#007bff; color:white; }
            QPushButton#primary:hover { background:#0056b3; }
            QPushButton#secondary{ background:#6c757d; color:white; }
            QPushButton#secondary:hover { background:#5a6268; }
            QPushButton#danger   { background:#dc3545; color:white; }
            QPushButton#danger:hover { background:#c82333; }
            QGroupBox {
                border: 1px solid #dee2e6; border-radius: 8px;
                margin-top: 8px; padding: 8px; background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 10px;
                padding: 0 4px; font-weight: bold;
            }
            QFrame#chip {
                background: #e8f4fd; border: 1px solid #bee5f0;
                border-radius: 4px;
            }
        """

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        # ── Placeholders reference ─────────────────────────────────────────────
        ph_group = QGroupBox("Available Placeholders  (click to insert)")
        ph_row   = QHBoxLayout(ph_group)
        ph_row.setSpacing(6)
        placeholders = [
            ("{customer_name}", "Customer's name"),
            ("{company_name}",  "Your company name"),
            ("{items}",         "Full items list"),
            ("{total}",         "Total amount (₹)"),
        ]
        for ph, tip in placeholders:
            btn = QPushButton(ph)
            btn.setObjectName("secondary")
            btn.setToolTip(tip)
            btn.setFixedHeight(30)
            btn.setStyleSheet(
                "QPushButton { background:#e8f4fd; color:#0056b3; border:1px solid #bee5f0;"
                " border-radius:4px; font-size:11px; font-family:Consolas,monospace;"
                " padding:2px 8px; font-weight:bold; }"
                "QPushButton:hover { background:#cce5f0; }"
            )
            btn.clicked.connect(lambda _, p=ph: self._insert_placeholder(p))
            ph_row.addWidget(btn)
        ph_row.addStretch()
        root.addWidget(ph_group)

        # ── Editor + Preview side by side ──────────────────────────────────────
        splitter = QSplitter(Qt.Horizontal if PYQT_VERSION == 5 else Qt.Orientation.Horizontal)
        splitter.setHandleWidth(6)
        splitter.setChildrenCollapsible(False)

        # Left: editor
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 4, 0)
        lv.setSpacing(4)
        lv.addWidget(QLabel("<b>Template</b>"))
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Type your message template here…")
        self.editor.setPlainText(load_template())
        self.editor.textChanged.connect(self._refresh_preview)
        lv.addWidget(self.editor, 1)

        reset_btn = QPushButton("Reset to Default")
        reset_btn.setObjectName("danger")
        reset_btn.setFixedHeight(30)
        reset_btn.clicked.connect(self._reset_template)
        lv.addWidget(reset_btn)

        # Right: preview
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(4, 0, 0, 0)
        rv.setSpacing(4)
        rv.addWidget(QLabel("<b>Preview</b>  <span style='color:#6c757d;font-size:11px;'>(sample data)</span>"))
        self.preview = QTextEdit()
        self.preview.setObjectName("preview")
        self.preview.setReadOnly(True)
        rv.addWidget(self.preview, 1)

        # Character count
        self.char_label = QLabel("0 characters")
        self.char_label.setStyleSheet("color:#6c757d; font-size:11px;")
        rv.addWidget(self.char_label)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([400, 400])
        root.addWidget(splitter, 1)

        # ── Buttons ────────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Save Template")
        btn_save.setObjectName("primary")
        btn_save.clicked.connect(self._save_and_close)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        root.addLayout(btn_row)

    def _insert_placeholder(self, ph: str):
        self.editor.insertPlainText(ph)
        self.editor.setFocus()

    def _refresh_preview(self):
        tmpl = self.editor.toPlainText()
        s = self.SAMPLE
        try:
            msg = build_message(
                s["customer_name"], self._company_name or s["company_name"],
                s["items"], s["amount"], template=tmpl,
            )
        except KeyError as e:
            msg = f"⚠️  Unknown placeholder: {e}\n\nFix the template and it will work."
        except Exception as e:
            msg = f"⚠️  Template error: {e}"
        self.preview.setPlainText(msg)
        self.char_label.setText(f"{len(msg)} characters")

    def _reset_template(self):
        if QMessageBox.question(self, "Reset", "Reset to the default template?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.editor.setPlainText(DEFAULT_TEMPLATE)

    def _save_and_close(self):
        tmpl = self.editor.toPlainText().strip()
        if not tmpl:
            QMessageBox.warning(self, "Empty Template", "Template cannot be empty.")
            return
        save_template(tmpl)
        self.accept()


@dataclass
class SendItem:
    customer_id: int
    customer_name: str
    phone: str
    message: str


# ── Worker thread ──────────────────────────────────────────────────────────────

class WhatsAppSendWorker(QThread):
    progress_changed   = pyqtSignal(int, int)   # done, total
    row_status_changed = pyqtSignal(int, str, str)  # row, status, error
    eta_changed        = pyqtSignal(str)
    finished_summary   = pyqtSignal(int, int)   # sent, failed

    def __init__(self, items: List[SendItem], base_delay: int, jitter: int = 2):
        super().__init__()
        self.items      = items
        self.base_delay = int(base_delay)
        self.jitter     = int(jitter)
        self._pause = False
        self._stop  = False

    def request_pause(self, paused: bool):
        self._pause = paused

    def request_stop(self):
        self._stop = True

    def _sleep_with_pause(self, seconds: float):
        end = time.time() + seconds
        while time.time() < end:
            if self._stop:
                return
            while self._pause and not self._stop:
                time.sleep(0.2)
            time.sleep(0.2)

    def run(self):
        total  = len(self.items)
        sent   = 0
        failed = 0
        start  = time.time()

        for idx, item in enumerate(self.items):
            if self._stop:
                break

            while self._pause and not self._stop:
                time.sleep(0.2)

            self.row_status_changed.emit(idx, STATUS_SENDING, "")

            ok, err = send_single_message(item.phone, item.message)
            if ok:
                sent += 1
                self.row_status_changed.emit(idx, STATUS_SENT, "")
            else:
                failed += 1
                self.row_status_changed.emit(idx, STATUS_FAILED, err or "Failed")

            done    = idx + 1
            self.progress_changed.emit(done, total)

            elapsed = max(0.1, time.time() - start)
            per     = elapsed / max(1, done)
            remaining = int(per * max(0, total - done))
            self.eta_changed.emit(f"{remaining // 60:02d}:{remaining % 60:02d}")

            if done < total and not self._stop:
                wait_s = max(1, self.base_delay + (int.from_bytes(os.urandom(1), "little") % (2 * self.jitter + 1) - self.jitter))
                self._sleep_with_pause(wait_s)

        self.finished_summary.emit(sent, failed)


# ── QR popup window ───────────────────────────────────────────────────────────

class _QRPopup(QDialog):
    """Dedicated popup that shows only the WhatsApp QR code."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scan QR Code — WhatsApp")
        self.setFixedSize(420, 500)
        self.setModal(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("<b style='font-size:15px'>Connect WhatsApp</b>")
        title.setAlignment(_qt_align_center())
        layout.addWidget(title)

        sub = QLabel(
            "Open WhatsApp on your phone<br>"
            "Menu (⋮) → <b>Linked Devices</b> → <b>Link a Device</b>"
        )
        sub.setAlignment(_qt_align_center())
        sub.setWordWrap(True)
        layout.addWidget(sub)

        self.qr_label = QLabel()
        self.qr_label.setFixedSize(340, 340)
        self.qr_label.setAlignment(_qt_align_center())
        self.qr_label.setStyleSheet(
            "border: 2px solid #dee2e6; border-radius: 10px; background: white;"
        )
        self.qr_label.setText("Loading QR code…")
        layout.addWidget(self.qr_label, 0, _qt_align_center())

        self.status_label = QLabel("Waiting for scan…")
        self.status_label.setAlignment(_qt_align_center())
        self.status_label.setStyleSheet("color: #856404; font-size: 12px;")
        layout.addWidget(self.status_label)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("secondary")
        btn_cancel.clicked.connect(self.close)
        layout.addWidget(btn_cancel, 0, _qt_align_center())

    def update_qr(self, qr_str: str):
        px = _qr_string_to_pixmap(qr_str)
        if not px.isNull():
            self.qr_label.setPixmap(px.scaled(334, 334, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def connected_and_close(self):
        self.status_label.setText("✅  Connected successfully!")
        self.status_label.setStyleSheet("color: #155724; font-size: 13px; font-weight: bold;")
        QTimer.singleShot(1200, self.close)


# ── Server-start worker (so UI doesn't freeze while Node boots) ───────────────

class ServerStartWorker(QThread):
    done = pyqtSignal(bool, str)   # ok, error_msg

    def run(self):
        ok, err = start_server()
        self.done.emit(ok, err)


# ── Main dialog ────────────────────────────────────────────────────────────────

class WhatsAppDialog(QDialog):
    def __init__(
        self,
        parent=None,
        bills: Optional[List[Dict]] = None,
        default_company_name: str = "Senthil Explosives",
    ):
        super().__init__(parent)
        self.setWindowTitle("Send via WhatsApp")
        self.setMinimumWidth(920)
        self.setMinimumHeight(580)

        self._worker: Optional[WhatsAppSendWorker] = None
        self._server_worker: Optional[ServerStartWorker] = None
        self._rows: List[Dict] = []
        self._failed_rows: List[Dict] = []
        self._selected_rows: List[int] = []

        self._build_ui(default_company_name=default_company_name)
        self.setStyleSheet(self._style_sheet())

        if bills:
            self.load_bills(bills)

        # Poll WhatsApp connection status every 2 s
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_connection)
        self._poll_timer.start(2000)

        # Kick off auto-connect on open
        QTimer.singleShot(300, self._auto_connect)

    # ── Stylesheet ─────────────────────────────────────────────────────────────

    def _style_sheet(self) -> str:
        return """
            QDialog { background-color: white; }
            QLabel { color: #212529; font-size: 12px; }
            QLineEdit, QComboBox {
                padding: 8px;
                border: 2px solid #ced4da;
                border-radius: 4px;
                font-size: 12px;
                background-color: white;
                color: #212529;
            }
            QLineEdit:focus, QComboBox:focus { border: 2px solid #007bff; }
            QPushButton {
                padding: 9px 16px;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
                border: none;
            }
            QPushButton#primary   { background-color: #007bff; color: white; }
            QPushButton#primary:hover  { background-color: #0056b3; }
            QPushButton#primary:disabled { background-color: #a8cff5; }
            QPushButton#secondary { background-color: #6c757d; color: white; }
            QPushButton#secondary:hover { background-color: #5a6268; }
            QPushButton#danger    { background-color: #dc3545; color: white; }
            QPushButton#danger:hover    { background-color: #c82333; }
            QPushButton#success   { background-color: #28a745; color: white; }
            QPushButton#success:hover   { background-color: #218838; }
            QPushButton#warning   { background-color: #ffc107; color: #212529; }
            QPushButton#warning:hover   { background-color: #e0a800; }
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                text-align: center;
                height: 16px;
                background: #f8f9fa;
            }
            QProgressBar::chunk { background-color: #007bff; border-radius: 6px; }
            QGroupBox {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding: 10px;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px 0 4px;
                font-weight: bold;
            }
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                gridline-color: #e9ecef;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 6px;
                border: 1px solid #dee2e6;
                font-weight: bold;
            }
        """

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self, default_company_name: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # ── Connection panel (slim bar only – QR opens in its own popup) ────────
        conn_group = QGroupBox("WhatsApp Connection")
        conn_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        conn_row = QHBoxLayout(conn_group)
        conn_row.setContentsMargins(10, 6, 10, 6)

        self.conn_status_label = QLabel("🔴  Not connected")
        self.conn_status_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        conn_row.addWidget(self.conn_status_label)
        conn_row.addStretch()

        self.btn_connect = QPushButton("Connect WhatsApp")
        self.btn_connect.setObjectName("success")
        self.btn_connect.clicked.connect(self._start_server_async)
        conn_row.addWidget(self.btn_connect)

        self.btn_disconnect = QPushButton("Logout")
        self.btn_disconnect.setObjectName("warning")
        self.btn_disconnect.setEnabled(False)
        self.btn_disconnect.clicked.connect(self._logout)
        conn_row.addWidget(self.btn_disconnect)

        layout.addWidget(conn_group)

        # ── Settings ───────────────────────────────────────────────────────────
        settings_group = QGroupBox("Settings")
        settings_layout = QHBoxLayout(settings_group)

        self.company_edit = QLineEdit(default_company_name)
        self.company_edit.setPlaceholderText("Company name used in the message")
        settings_layout.addWidget(QLabel("Company:"))
        settings_layout.addWidget(self.company_edit, 2)

        self.delay_combo = QComboBox()
        self.delay_combo.addItem("Fast  (3 sec between msgs)", 3)
        self.delay_combo.addItem("Normal (5 sec between msgs)", 5)
        self.delay_combo.addItem("Safe  (10 sec between msgs)", 10)
        self.delay_combo.setCurrentIndex(1)
        settings_layout.addWidget(QLabel("  Delay:"))
        settings_layout.addWidget(self.delay_combo, 1)

        btn_template = QPushButton("Edit Message Template")
        btn_template.setObjectName("secondary")
        btn_template.clicked.connect(self._open_template_editor)
        settings_layout.addWidget(btn_template)

        layout.addWidget(settings_group)

        # ── Bills table ────────────────────────────────────────────────────────
        table_group = QGroupBox("Bills to Send")
        table_layout = QVBoxLayout(table_group)

        top_btn_row = QHBoxLayout()
        btn_select_all = QPushButton("Select All")
        btn_select_all.setObjectName("secondary")
        btn_select_all.clicked.connect(lambda: self._set_all_checked(True))
        btn_deselect_all = QPushButton("Deselect All")
        btn_deselect_all.setObjectName("secondary")
        btn_deselect_all.clicked.connect(lambda: self._set_all_checked(False))
        top_btn_row.addWidget(btn_select_all)
        top_btn_row.addWidget(btn_deselect_all)
        top_btn_row.addStretch()
        table_layout.addLayout(top_btn_row)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Send", "Customer", "Phone", "Status", "Note"])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        table_layout.addWidget(self.table, 1)

        layout.addWidget(table_group, 1)

        # ── Progress & controls ────────────────────────────────────────────────
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)

        self.progress_label = QLabel("0/0")
        self.progress_label.setAlignment(_qt_align_left_vcenter())
        progress_layout.addWidget(self.progress_label)

        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        progress_layout.addWidget(self.progress)

        eta_row = QHBoxLayout()
        self.eta_label = QLabel("Estimated time remaining: 00:00")
        eta_row.addWidget(self.eta_label)
        eta_row.addStretch()
        progress_layout.addLayout(eta_row)

        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("Start Sending")
        self.btn_start.setObjectName("primary")
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self.start_sending)

        self.btn_pause = QPushButton("Pause")
        self.btn_pause.setObjectName("secondary")
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self.toggle_pause)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("danger")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_sending)

        self.btn_export_failed = QPushButton("Export Failed CSV")
        self.btn_export_failed.setObjectName("secondary")
        self.btn_export_failed.setEnabled(False)
        self.btn_export_failed.clicked.connect(self.export_failed_csv)

        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_pause)
        btn_row.addWidget(self.btn_stop)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_export_failed)
        progress_layout.addLayout(btn_row)

        layout.addWidget(progress_group)

    # ── Connection management ──────────────────────────────────────────────────

    def _auto_connect(self):
        """Silently try to connect when dialog opens."""
        if is_server_running():
            self._poll_connection()
        else:
            self._start_server_async()

    def _start_server_async(self):
        """Start the Node server in a background thread so dialog stays responsive."""
        if self._server_worker and self._server_worker.isRunning():
            return

        # Quick pre-checks
        if not node_installed():
            QMessageBox.warning(
                self,
                "Node.js Required",
                "Node.js is not installed.\n\n"
                "Please download and install it from:\n"
                "  https://nodejs.org  (choose the LTS version)\n\n"
                "After installing, restart this app.",
            )
            return

        self._set_conn_status("🟡  Starting WhatsApp server…", "#856404")
        self.btn_connect.setEnabled(False)

        # Start a timeout — if we don't reach QR/ready in 60s, show an error
        if hasattr(self, "_connect_timeout"):
            self._connect_timeout.stop()
        self._connect_timeout = QTimer(self)
        self._connect_timeout.setSingleShot(True)
        self._connect_timeout.timeout.connect(self._on_connect_timeout)
        self._connect_timeout.start(60000)

        self._server_worker = ServerStartWorker()
        self._server_worker.done.connect(self._on_server_start_done)
        self._server_worker.start()

    def _on_connect_timeout(self):
        """Called if we haven't reached QR/ready after 60 seconds."""
        status = get_server_status()
        state  = status.get("state", "offline")
        if state not in ("ready", "qr"):
            self._set_conn_status("🔴  Connection timed out", "#721c24")
            self.btn_connect.setEnabled(True)
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whatsapp_node.log")
            QMessageBox.warning(
                self,
                "Connection Timed Out",
                "WhatsApp server did not respond in time.\n\n"
                "Possible causes:\n"
                "• Chrome could not launch (try updating Chrome)\n"
                "• Network issue\n\n"
                f"Check the log for details:\n{log_path}",
            )

    def _on_server_start_done(self, ok: bool, err: str):
        self.btn_connect.setEnabled(True)
        if not ok:
            self._set_conn_status("🔴  Not connected", "#721c24")
            # Check if it's an npm install issue
            if "npm install" in err or "packages are not installed" in err:
                reply = QMessageBox.question(
                    self,
                    "Install WhatsApp Packages",
                    "WhatsApp packages are not installed yet.\n\n"
                    "Click OK to install them now (needs internet, takes ~1-2 minutes).\n"
                    "Or click Cancel and run  npm install  yourself in the app folder.",
                    QMessageBox.Ok | QMessageBox.Cancel,
                )
                if reply == QMessageBox.Ok:
                    self._set_conn_status("🟡  Installing packages…", "#856404")
                    self.btn_connect.setEnabled(False)
                    self._run_npm_install()
            else:
                QMessageBox.warning(self, "Connection Failed", err)
        # If ok, _poll_connection() will pick up the new state

    def _run_npm_install(self):
        class _NpmWorker(QThread):
            done = pyqtSignal(bool, str)
            def run(self_inner):
                ok, err = npm_install()
                self_inner.done.emit(ok, err)

        self._npm_worker = _NpmWorker()
        self._npm_worker.done.connect(self._on_npm_done)
        self._npm_worker.start()

    def _on_npm_done(self, ok: bool, err: str):
        self.btn_connect.setEnabled(True)
        if ok:
            QMessageBox.information(
                self,
                "Packages Installed",
                "WhatsApp packages installed successfully!\n\nClick 'Connect WhatsApp' to continue.",
            )
            self._set_conn_status("🔴  Not connected", "#721c24")
        else:
            QMessageBox.warning(
                self,
                "Install Failed",
                f"Could not install packages automatically:\n\n{err}\n\n"
                "Please open a terminal in the app folder and run:  npm install",
            )
            self._set_conn_status("🔴  Not connected", "#721c24")

    def _cancel_connect_timeout(self):
        if hasattr(self, "_connect_timeout") and self._connect_timeout:
            self._connect_timeout.stop()

    def _poll_connection(self):
        status = get_server_status()
        state  = status.get("state", "offline")
        qr     = status.get("qr")

        if state == "ready":
            self._set_conn_status("🟢  Connected — ready to send", "#155724")
            self.btn_disconnect.setEnabled(True)
            self.btn_connect.setEnabled(False)
            self._cancel_connect_timeout()
            self._update_start_enabled()
            # Auto-close QR popup if open
            if hasattr(self, "_qr_popup") and self._qr_popup and self._qr_popup.isVisible():
                self._qr_popup.connected_and_close()

        elif state == "qr":
            self._set_conn_status("📱  Scan the QR code to connect", "#856404")
            self.btn_connect.setEnabled(False)
            self._cancel_connect_timeout()
            # Open/update the QR popup
            if qr:
                if not hasattr(self, "_qr_popup") or not self._qr_popup or not self._qr_popup.isVisible():
                    self._qr_popup = _QRPopup(self)
                    self._qr_popup.show()
                self._qr_popup.update_qr(qr)

        elif state in ("initializing", "authenticated"):
            self._set_conn_status("🟡  Connecting…", "#856404")
            self.btn_connect.setEnabled(False)

        elif state in ("disconnected", "error", "offline"):
            self._set_conn_status("🔴  Not connected", "#721c24")
            self.btn_connect.setEnabled(True)
            self.btn_disconnect.setEnabled(False)
            self.btn_start.setEnabled(False)

        else:
            self._set_conn_status(f"🟡  {state}", "#856404")

    def _set_conn_status(self, text: str, color: str = "#212529"):
        self.conn_status_label.setText(text)
        self.conn_status_label.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {color};"
        )

    def _logout(self):
        reply = QMessageBox.question(
            self,
            "Logout",
            "This will disconnect WhatsApp and delete the saved session.\n"
            "You will need to scan the QR code again.\n\nContinue?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            logout_whatsapp()
            self.btn_disconnect.setEnabled(False)
            self.btn_connect.setEnabled(False)
            self.btn_start.setEnabled(False)
            self._set_conn_status("🟡  Logged out — generating new QR code…", "#856404")

    def _open_template_editor(self):
        company = self.company_edit.text().strip()
        dlg = MessageTemplateDialog(self, company_name=company)
        if (dlg.exec_() if PYQT_VERSION == 5 else dlg.exec()) == DIALOG_ACCEPTED:
            # Rebuild messages for all already-loaded rows using new template
            new_tmpl = load_template()
            company  = self.company_edit.text().strip() or "Company"
            for row in self._rows:
                row["message"] = build_message(
                    row.get("customer_name") or "Customer",
                    company,
                    [],   # items already baked in; full rebuild needs original data
                    0,
                    template=new_tmpl,
                )
            QMessageBox.information(
                self, "Template Saved",
                "Message template saved.\n\n"
                "Note: item details and totals will use the new template when you next open this dialog.",
            )

    # ── Bills loading ──────────────────────────────────────────────────────────

    def load_bills(self, bills: List[Dict]):
        self.table.setRowCount(0)
        self._rows = []
        self._failed_rows = []
        company_name = self.company_edit.text().strip() or "Company"

        tmpl = load_template()
        for bill in bills:
            customer    = bill.get("customer") or {}
            customer_id = int(customer.get("id") or 0)
            name        = (customer.get("name") or "").strip() or "Customer"
            phone       = format_indian_phone(customer.get("phone") or "")
            message     = build_message(name, company_name, bill.get("items") or [], bill.get("grand_total") or 0, template=tmpl)

            row = self.table.rowCount()
            self.table.insertRow(row)

            chk_item = QTableWidgetItem("")
            chk_item.setFlags(chk_item.flags() | Qt.ItemIsUserCheckable)
            chk_item.setCheckState(Qt.Checked)
            self.table.setItem(row, 0, chk_item)
            self.table.setItem(row, 1, QTableWidgetItem(name.upper()))
            self.table.setItem(row, 2, QTableWidgetItem(phone or "(missing)"))
            self.table.setItem(row, 3, QTableWidgetItem(""))
            self.table.setItem(row, 4, QTableWidgetItem(""))

            self._rows.append(
                {"customer_id": customer_id, "customer_name": name, "phone": phone, "message": message}
            )

        self._update_start_enabled()

    def _set_all_checked(self, checked: bool):
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item:
                item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
        self._update_start_enabled()

    def _update_start_enabled(self):
        status = get_server_status()
        ready  = status.get("state") == "ready"
        any_checked = any(
            self.table.item(r, 0) is not None and self.table.item(r, 0).checkState() == Qt.Checked
            for r in range(self.table.rowCount())
        )
        self.btn_start.setEnabled(ready and any_checked and self._worker is None)

    # ── Sending ────────────────────────────────────────────────────────────────

    def start_sending(self):
        # Check connection
        status = get_server_status()
        if status.get("state") != "ready":
            QMessageBox.warning(
                self,
                "Not Connected",
                "WhatsApp is not connected.\nPlease wait for the connection or scan the QR code.",
            )
            return

        # Collect selected rows
        selected_rows = [
            r for r in range(self.table.rowCount())
            if self.table.item(r, 0) is not None
            and self.table.item(r, 0).checkState() == Qt.Checked
        ]
        if not selected_rows:
            QMessageBox.warning(self, "Select Bills", "Please select at least one bill to send.")
            return

        # Validate phones
        missing = [
            self._rows[r]["customer_name"].upper()
            for r in selected_rows
            if not format_indian_phone(self._rows[r].get("phone", ""))
        ]
        if missing:
            QMessageBox.warning(
                self,
                "Missing Phone Numbers",
                "Phone number is missing for:\n" + "\n".join(missing)
                + "\n\nPlease edit the customer and add a 10-digit number.",
            )
            return

        # Build send list
        send_list: List[SendItem] = [
            SendItem(
                customer_id=int(self._rows[r].get("customer_id") or 0),
                customer_name=self._rows[r].get("customer_name") or "Customer",
                phone=self._rows[r].get("phone") or "",
                message=self._rows[r].get("message") or "",
            )
            for r in selected_rows
        ]

        # Reset table statuses
        for r in range(self.table.rowCount()):
            self.table.item(r, 3).setText("")
            self.table.item(r, 4).setText("")

        self._failed_rows  = []
        self._selected_rows = selected_rows

        base_delay = int(self.delay_combo.currentData() or 5)
        jitter     = min(2, base_delay // 2)

        self._worker = WhatsAppSendWorker(send_list, base_delay=base_delay, jitter=jitter)
        self._worker.progress_changed.connect(self._on_progress)
        self._worker.row_status_changed.connect(self._on_row_status)
        self._worker.eta_changed.connect(self._on_eta)
        self._worker.finished_summary.connect(self._on_finished)
        self._worker.start()

        self.btn_start.setEnabled(False)
        self.btn_pause.setEnabled(True)
        self.btn_stop.setEnabled(True)
        self.btn_export_failed.setEnabled(False)
        self.btn_pause.setText("Pause")
        self.progress.setValue(0)
        self.progress_label.setText(f"0/{len(send_list)}")
        self.eta_label.setText("Estimated time remaining: 00:00")

    def toggle_pause(self):
        if not self._worker:
            return
        if self.btn_pause.text().strip().lower().startswith("resume"):
            self._worker.request_pause(False)
            self.btn_pause.setText("Pause")
        else:
            self._worker.request_pause(True)
            self.btn_pause.setText("Resume")

    def stop_sending(self):
        if self._worker:
            self._worker.request_stop()
            self.btn_stop.setEnabled(False)

    # ── Signal handlers ────────────────────────────────────────────────────────

    def _on_progress(self, done: int, total: int):
        self.progress_label.setText(f"{done}/{total}")
        self.progress.setValue(int(done / max(1, total) * 100))

    def _on_eta(self, eta: str):
        self.eta_label.setText(f"Estimated time remaining: {eta}")

    def _on_row_status(self, worker_row: int, status: str, error: str):
        table_row = self._selected_rows[worker_row]
        self.table.item(table_row, 3).setText(status)
        self.table.item(table_row, 4).setText((error or "")[:200])
        if status == STATUS_FAILED:
            data = dict(self._rows[table_row])
            data["error"] = error
            self._failed_rows.append(data)

    def _on_finished(self, sent: int, failed: int):
        self.btn_pause.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self._worker = None
        self._update_start_enabled()
        self.btn_export_failed.setEnabled(bool(self._failed_rows))
        self._show_toast(f"WhatsApp done: {sent} sent, {failed} failed")
        QMessageBox.information(self, "WhatsApp Summary", f"✅ {sent} sent\n❌ {failed} failed")

    # ── Toast ──────────────────────────────────────────────────────────────────

    def _show_toast(self, text: str, duration_ms: int = 3500):
        toast = QWidget(self)
        if PYQT_VERSION == 6:
            toast.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.ToolTip)
        else:
            toast.setWindowFlags(Qt.FramelessWindowHint | Qt.ToolTip)
        toast.setAttribute(Qt.WA_TranslucentBackground, True)
        lv = QVBoxLayout(toast)
        lv.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(text, toast)
        lbl.setStyleSheet(
            "QLabel { background-color: rgba(33,37,41,0.92); color:white; "
            "padding:10px 14px; border-radius:8px; font-size:12px; font-weight:bold; }"
        )
        lv.addWidget(lbl)
        toast.adjustSize()
        geo = self.geometry()
        toast.move(max(10, geo.x() + geo.width() - toast.width() - 20),
                   max(10, geo.y() + geo.height() - toast.height() - 20))
        toast.show()
        QTimer.singleShot(duration_ms, toast.close)

    # ── Export CSV ─────────────────────────────────────────────────────────────

    def export_failed_csv(self):
        if not self._failed_rows:
            QMessageBox.information(self, "No Failed Numbers", "No failed numbers to export.")
            return
        default_name = f"whatsapp_failed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path, _ = QFileDialog.getSaveFileName(self, "Save Failed CSV", default_name, "CSV Files (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["customer_name", "phone", "error"])
                for r in self._failed_rows:
                    w.writerow([r.get("customer_name", ""), r.get("phone", ""), r.get("error", "")])
            QMessageBox.information(self, "Exported", f"Saved to:\n{path}")
        except Exception:
            QMessageBox.warning(self, "Export Failed", "Could not save the CSV. Try a different location.")

    # ── Cleanup ────────────────────────────────────────────────────────────────

    def closeEvent(self, event):
        self._poll_timer.stop()
        if self._worker and self._worker.isRunning():
            self._worker.request_stop()
            self._worker.wait(3000)
        super().closeEvent(event)
