"""
Modern Professional UI for Delivery Bill Generator
Built with PyQt6 for a professional Tally/ZohoBooks-like experience
"""
import sys
# Try PyQt5 first (more stable on macOS), fallback to PyQt6
try:
    from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox, QDateEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea,
    QFrame, QGroupBox, QMessageBox, QDialog, QTextEdit, QSpinBox,
    QDoubleSpinBox, QFileDialog, QSplitter, QListWidget, QListWidgetItem,
    QListView, QInputDialog, QAbstractItemView, QStackedWidget, QStyledItemDelegate,
    QGraphicsDropShadowEffect, QSizePolicy
    )
    from PyQt5.QtCore import Qt, QDate, QSize, pyqtSignal, QEvent, QSettings
    from PyQt5.QtGui import QFont, QIcon, QColor, QPalette, QPixmap, QPainter, QPen, QPainterPath, QWheelEvent
    PYQT_VERSION = 5
    DIALOG_ACCEPTED = QDialog.Accepted
except ImportError:
    # Fallback to PyQt6
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox, QDateEdit,
        QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea,
        QFrame, QGroupBox, QMessageBox, QDialog, QTextEdit, QSpinBox,
        QDoubleSpinBox, QFileDialog, QSplitter, QListWidget, QListWidgetItem,
    QListView, QInputDialog, QAbstractItemView, QStackedWidget, QStyledItemDelegate,
    QGraphicsDropShadowEffect, QSizePolicy
    )
    from PyQt6.QtCore import Qt, QDate, QSize, pyqtSignal, QEvent, QSettings
    from PyQt6.QtGui import QFont, QIcon, QColor, QPalette, QPixmap, QPainter, QPen, QPainterPath, QWheelEvent
    PYQT_VERSION = 6
    DIALOG_ACCEPTED = QDialog.DialogCode.Accepted
from datetime import datetime
from database import Database
from pdf_generator import PDFGenerator
from whatsapp_dialog import WhatsAppDialog
from number_to_words import number_to_words
from dialogs_modern import (
    AddAreaDialog, AddVehicleDialog, AddCustomerDialog,
    AddGoodDialog, AddBlasterDialog, NewGoodDialog, SelectCustomerDialog,
    AddUnitDialog
)
from modern_calendar import DateEditWithModernCalendar
import re
import math
import tempfile
import os


class NoWheelComboBox(QComboBox):
    """QComboBox that only responds to wheel events when explicitly clicked/focused"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._wheel_enabled = False  # Only enable wheel when explicitly clicked
    
    def mousePressEvent(self, event):
        """Enable wheel events when combo box is clicked"""
        self._wheel_enabled = True
        super().mousePressEvent(event)
    
    def focusOutEvent(self, event):
        """Disable wheel events when focus is lost"""
        self._wheel_enabled = False
        super().focusOutEvent(event)
    
    def wheelEvent(self, event: QWheelEvent):
        # Only process wheel events if the combo box was explicitly clicked/focused
        if self._wheel_enabled and self.hasFocus():
            super().wheelEvent(event)
        else:
            # Ignore wheel events when not explicitly focused
            event.ignore()


class ModernButton(QPushButton):
    """Modern styled button"""
    def __init__(self, text, primary=False, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        if primary:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
                QPushButton:pressed {
                    background-color: #004085;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #f8f9fa;
                    color: #212529;
                    border: 1px solid #dee2e6;
                    padding: 8px 16px;
                    border-radius: 5px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                }
                QPushButton:pressed {
                    background-color: #dee2e6;
                }
            """)


class CardWidget(QFrame):
    """Card-style widget container"""
    def __init__(self, title="", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
            QLabel {
                background-color: transparent;
                color: #212529;
            }
        """)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)  # Reduced from 15 to 10
        self.layout.setSpacing(8)  # Reduced from 10 to 8
        
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: #212529;
                    padding-bottom: 10px;
                    border-bottom: 2px solid #007bff;
                }
            """)
            self.layout.addWidget(title_label)


class SidebarWidget(QWidget):
    """Modern sidebar navigation"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                color: white;
            }
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                padding: 15px 20px;
                text-align: left;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:pressed {
                background-color: #1a252f;
            }
        """)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Logo/Title
        title = QLabel("Senthil Explosives\nDelivery Bill Generator")
        title.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 20px;
                background-color: #1a252f;
            }
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(title)
        
        # Navigation buttons
        self.nav_buttons = []
        nav_items = [
            ("📋 New Bill", "new_bill"),
            ("📦 Batch Processing", "batch"),
            ("👥 Customers", "customers"),
            ("📦 Goods", "goods"),
            ("🚚 Vehicles", "vehicles"),
            ("⚙️ Settings", "settings")
        ]
        
        for text, action in nav_items:
            btn = QPushButton(text)
            btn.setProperty("action", action)
            self.nav_buttons.append(btn)
            self.layout.addWidget(btn)
        
        self.layout.addStretch()


class CustomerItemWidget(QWidget):
    """Widget for customer list item"""
    clicked = pyqtSignal(int)
    
    def __init__(self, customer_id, customer_name, checkmark_icon_path, is_selected=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.customer_id = customer_id
        self.checkmark_icon_path = checkmark_icon_path
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 8px;
            }
            QWidget:hover {
                background-color: #f8f9fa;
                border: 1px solid #007bff;
            }
            QCheckBox {
                font-size: 11px;
                color: #212529;
                background-color: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:hover {
                border-color: #007bff;
            }
            QCheckBox::indicator:checked {
                background-color: #007bff;
                border-color: #007bff;
                image: url(""" + self.checkmark_icon_path.replace('\\', '/') + """);
            }
            QLabel {
                font-size: 11px;
                color: #212529;
                background-color: transparent;
            }
            QPushButton {
                background-color: transparent;
                border: none;
                color: #212529;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)  # Reduced margins for more compact appearance
        layout.setSpacing(5)  # Reduced spacing to join checkbox and name together
        
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(is_selected)
        layout.addWidget(self.checkbox)
        
        self.name_label = QLabel(customer_name.upper() if customer_name else customer_name)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 12px;")  # Reduced font size
        layout.addWidget(self.name_label, 1)
        
        self.expand_btn = QPushButton("▶")
        self.expand_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 12px;
                padding: 5px;
                min-width: 20px;
            }
        """)
        layout.addWidget(self.expand_btn)
        
        # Make entire widget clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def mousePressEvent(self, event):
        """Emit clicked signal when the row (name/area) is clicked, but not when clicking the checkbox."""
        if event.button() == Qt.MouseButton.LeftButton:
            # If click is on the checkbox, let default behavior happen
            if not self.checkbox.geometry().contains(event.pos()):
                # Simulate clicking the expand button (toggle details)
                self.expand_btn.click()
                return
        super().mousePressEvent(event)
    
    def set_expanded(self, expanded):
        self.expand_btn.setText("▼" if expanded else "▶")


class BatchProcessingWindow(QMainWindow):
    """Main window for batch processing with modern UI"""
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.pdf_gen = PDFGenerator()
        
        # Initialize QSettings for remembering last save location
        self.settings = QSettings("DeliveryBillApp", "DeliveryBillGenerator")
        
        # Create checkmark icon for checkboxes
        self.checkmark_icon_path = self._create_checkmark_icon()
        
        # Set window icon (logo)
        self._set_window_icon()
        
        # State
        self.current_category = None
        self.current_area_id = None
        self.current_area_name = None
        self.selected_customers = {}
        self.expanded_customer_id = None
        self.default_cgst_rate = 9.0
        self.default_sgst_rate = 9.0
        
        self.load_tax_rates()
        self.init_ui()
    
    def load_tax_rates(self):
        """Load default tax rates"""
        self.default_cgst_rate = float(self.db.get_setting('cgst_rate', '9.0'))
        self.default_sgst_rate = float(self.db.get_setting('sgst_rate', '9.0'))
    
    def _create_checkmark_icon(self):
        """Create a white checkmark icon for checkboxes"""
        # Create a pixmap for the checkmark
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.GlobalColor.transparent if PYQT_VERSION == 6 else Qt.transparent)
        
        # Draw checkmark
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing if PYQT_VERSION == 6 else QPainter.Antialiasing)
        
        # Set pen for checkmark
        pen = QPen(QColor(255, 255, 255))  # White color
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap if PYQT_VERSION == 6 else Qt.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin if PYQT_VERSION == 6 else Qt.RoundJoin)
        painter.setPen(pen)
        
        # Draw checkmark path
        path = QPainterPath()
        path.moveTo(4, 10)
        path.lineTo(8, 14)
        path.lineTo(16, 6)
        painter.drawPath(path)
        
        painter.end()
        
        # Save to temporary file
        temp_dir = tempfile.gettempdir()
        icon_path = os.path.join(temp_dir, 'checkbox_check.png')
        pixmap.save(icon_path)
        
        return icon_path
    
    def _set_window_icon(self):
        """Set the window icon from logo.png"""
        # Handle PyInstaller bundled mode
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            script_dir = sys._MEIPASS
        else:
            # Running as script
            script_dir = os.path.dirname(os.path.abspath(__file__))
        
        logo_path = os.path.join(script_dir, "logo.png")
        if os.path.exists(logo_path):
            icon = QIcon(logo_path)
            self.setWindowIcon(icon)
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Senthil Explosives Delivery Bill Generator")
        self.setGeometry(100, 100, 1600, 900)
        
        # Force light theme and set application style
        app = QApplication.instance()
        app.setStyle('Fusion')  # Use Fusion style for better control
        
        # Set light palette to override system dark theme
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(245, 246, 250))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(33, 37, 41))
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(248, 249, 250))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(33, 37, 41))
        palette.setColor(QPalette.ColorRole.Text, QColor(33, 37, 41))
        palette.setColor(QPalette.ColorRole.Button, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(33, 37, 41))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Link, QColor(0, 123, 255))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 123, 255))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        app.setPalette(palette)
        
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }
            QWidget {
                background-color: #f5f6fa;
                color: #212529;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
                color: #212529;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #212529;
            }
            QLineEdit, QComboBox, QDateEdit, QTextEdit, QSpinBox, QDoubleSpinBox {
                padding: 8px;
                border: 2px solid #ced4da;
                border-radius: 4px;
                font-size: 12px;
                background-color: white;
                color: #212529;
                selection-background-color: #007bff;
                selection-color: white;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTextEdit:focus {
                border: 2px solid #007bff;
                background-color: white;
            }
            QComboBox::drop-down {
                border: none;
                background-color: transparent;
            }
            QComboBox::drop-down:hover {
                background-color: transparent;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #212529;
                selection-background-color: #007bff;
                selection-color: white;
                border: 1px solid #ced4da;
            }
            QLabel {
                color: #212529;
                font-size: 12px;
                background-color: transparent;
            }
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                background-color: white;
                gridline-color: #dee2e6;
                color: #212529;
            }
            QTableWidget::item {
                padding: 5px;
                color: #212529;
                background-color: white;
            }
            QTableWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            QHeaderView::section {
                background-color: #007bff;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QScrollArea {
                background-color: white;
                border: 1px solid #dee2e6;
            }
            QCheckBox {
                color: #212529;
                background-color: transparent;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:hover {
                border-color: #007bff;
            }
            QCheckBox::indicator:checked {
                background-color: #007bff;
                border-color: #007bff;
                image: url(""" + self.checkmark_icon_path.replace('\\', '/') + """);
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Top section: Clean, Professional Configuration
        top_card = CardWidget("Configuration")
        top_card.layout.setSpacing(15)  # Reduced spacing
        top_card.layout.setContentsMargins(15, 15, 15, 15)  # Reduced margins
        top_card.setMinimumHeight(220)  # Taller for better visibility
        
        # Main configuration area with splitter for left config and right goods management
        config_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Configuration fields - SIMPLIFIED AND CLEAR
        left_config_widget = QWidget()
        left_config_layout = QVBoxLayout(left_config_widget)
        left_config_layout.setContentsMargins(10, 5, 10, 12)  # Top margin 5px, bottom margin 12px
        left_config_layout.setSpacing(10)  # Reduced spacing between rows
        
        # Row 1: Category, Area, Vehicle, and Date - All on same line
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(15)
        row1_layout.setContentsMargins(0, 0, 0, 0)
        
        # Define dropdown style for all dropdowns
        self.dropdown_field_style = """
            QComboBox {
                padding: 10px 12px;
                border: 1.5px solid #d0d7de;
                border-radius: 8px;
                background-color: #ffffff;
                font-size: 14px;
                color: #212529;
                text-align: center;
            }
            QComboBox:focus {
                border: 1.5px solid #0d6efd;
                background-color: #ffffff;
            }
            QComboBox::drop-down {
                width: 0px;
                border: none;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                width: 0px;
                height: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: transparent;
                border: none;
            }
        """
        
        # Category - Dropdown field
        category_label = QLabel("Category:")
        category_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #212529; min-width: 80px; padding: 2px 0px;")
        category_label.setMinimumHeight(45)
        category_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        self.category_combo = NoWheelComboBox()
        self.category_combo.setMinimumWidth(180)
        self.category_combo.setMaximumWidth(180)
        self.category_combo.setMinimumHeight(45)
        self.category_combo.setEditable(False)
        self.category_combo.addItem("-- Select Category --", None)
        self.category_combo.addItem("Detonator", "Detonator")
        self.category_combo.addItem("Explosives", "Explosives")
        self.category_combo.setStyleSheet(self.dropdown_field_style)
        # Simple dropdown without custom popup (only 2 options)
        self.category_combo.setMaxVisibleItems(10)
        self.category_combo.currentIndexChanged.connect(self.on_category_changed)
        
        row1_layout.addWidget(category_label)
        row1_layout.addWidget(self.category_combo)
        
        # Area - Larger and clearer
        area_label = QLabel("Area:")
        area_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #212529; min-width: 50px; padding: 2px 0px;")
        area_label.setMinimumHeight(45)
        area_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.area_combo = NoWheelComboBox()
        self.area_combo.setMinimumWidth(180)
        self.area_combo.setMaximumWidth(180)
        self.area_combo.setMinimumHeight(45)
        self.area_combo.setEditable(False)
        self.area_combo.setStyleSheet(self.dropdown_field_style)
        # Disable default popup, use custom one
        self.area_combo.setMaxVisibleItems(0)
        self.area_combo.view().setVisible(False)
        # Create custom popup with fixed buttons
        self._create_custom_dropdown_popup(self.area_combo, self.add_area, self.manage_areas)
        # Override showPopup to use custom popup
        self.area_combo.showPopup = lambda: self._check_category_and_show_popup(self.area_combo, "Area")
        # Add keyboard support to combo box
        self._add_combo_keyboard_support(self.area_combo)
        self.area_combo.currentTextChanged.connect(self.on_area_changed)
        row1_layout.addWidget(area_label)
        row1_layout.addWidget(self.area_combo)
        
        # Vehicle - on same line
        vehicle_label = QLabel("Vehicle:")
        vehicle_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #212529; min-width: 60px; padding: 2px 0px;")
        vehicle_label.setMinimumHeight(45)
        vehicle_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.vehicle_combo = NoWheelComboBox()
        self.vehicle_combo.setMinimumWidth(180)  # Same width as other fields
        self.vehicle_combo.setMaximumWidth(180)  # Constrain to prevent expansion
        self.vehicle_combo.setMinimumHeight(45)
        self.vehicle_combo.setEditable(False)
        self.vehicle_combo.setStyleSheet(self.dropdown_field_style)
        # Disable default popup, use custom one  
        self.vehicle_combo.setMaxVisibleItems(0)
        self.vehicle_combo.view().setVisible(False)
        # Create custom popup with fixed buttons
        self._create_custom_dropdown_popup(self.vehicle_combo, self.add_vehicle, self.manage_vehicles)
        # Override showPopup to use custom popup
        self.vehicle_combo.showPopup = lambda: self._check_category_and_show_popup(self.vehicle_combo, "Vehicle")
        # Add keyboard support to combo box
        self._add_combo_keyboard_support(self.vehicle_combo)
        row1_layout.addWidget(vehicle_label)
        row1_layout.addWidget(self.vehicle_combo)
        
        # Date - on same line
        date_label = QLabel("Date:")
        date_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #212529; min-width: 50px; padding: 2px 0px;")
        date_label.setMinimumHeight(45)
        date_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setMinimumWidth(150)
        self.date_edit.setMinimumHeight(45)
        self.date_edit.setStyleSheet("""
            QDateEdit {
                padding: 10px;
                padding-right: 50px;
                border: 2px solid #ced4da;
                border-radius: 5px;
                background-color: white;
                font-size: 14px;
                color: #212529;
            }
            QDateEdit:focus {
                border: 2px solid #007bff;
                background-color: white;
            }
            QDateEdit::drop-down {
                border-left: 2px solid #ced4da;
                width: 45px;
                background-color: #f8f9fa;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
            }
            QDateEdit::drop-down:hover {
                background-color: #e9ecef;
                border-left: 2px solid #007bff;
            }
            QDateEdit::drop-down:pressed {
                background-color: #dee2e6;
            }
            QDateEdit::up-button, QDateEdit::down-button {
                width: 0px;
                height: 0px;
                border: none;
                background: transparent;
            }
        """)
        
        if PYQT_VERSION == 6:
            self.date_edit.setDisplayFormat("dd-MM-yyyy")
        else:
            self.date_edit.setDisplayFormat("dd/MM/yyyy")
        
        # Attach modern calendar popup
        DateEditWithModernCalendar.attach_to_date_edit(self.date_edit)
        
        # Create a wrapper to overlay the calendar icon
        date_wrapper = QWidget()
        date_wrapper.setMinimumWidth(150)
        date_wrapper.setMinimumHeight(45)
        date_wrapper_layout = QHBoxLayout(date_wrapper)
        date_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        date_wrapper_layout.setSpacing(0)
        date_wrapper_layout.addWidget(self.date_edit)
        
        # Calendar icon label positioned absolutely over the dropdown area
        if PYQT_VERSION == 5:
            from PyQt5.QtGui import QPixmap
        else:
            from PyQt6.QtGui import QPixmap
        
        import os
        # Get the directory where this script is located
        # Handle PyInstaller bundled mode
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            script_dir = sys._MEIPASS
        else:
            # Running as script
            script_dir = os.path.dirname(os.path.abspath(__file__))
        calendar_icon_path = os.path.join(script_dir, "calendar_4371058.png")
        
        # Load the calendar icon image
        calendar_pixmap = QPixmap(calendar_icon_path)
        emoji_size = 18  # Small size like emoji
        
        if not calendar_pixmap.isNull():
            # Get device pixel ratio for high-DPI displays (Retina, etc.)
            app = QApplication.instance()
            if app:
                try:
                    device_pixel_ratio = app.devicePixelRatio()
                except:
                    device_pixel_ratio = 2.0  # Default to 2x for Retina displays
            else:
                device_pixel_ratio = 2.0  # Default to 2x for better quality
            
            # Scale to higher resolution for crisp rendering
            target_size = int(emoji_size * max(device_pixel_ratio, 2.0))
            calendar_pixmap = calendar_pixmap.scaled(
                target_size, target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Set device pixel ratio
            if hasattr(calendar_pixmap, 'setDevicePixelRatio'):
                calendar_pixmap.setDevicePixelRatio(max(device_pixel_ratio, 2.0))
        
        calendar_icon_label = QLabel(date_wrapper)
        calendar_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        calendar_icon_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: none;
                padding: 0px;
            }
        """)
        calendar_icon_label.setScaledContents(False)
        
        if not calendar_pixmap.isNull():
            calendar_icon_label.setPixmap(calendar_pixmap)
        else:
            # Fallback: use a simple text if image fails to load
            calendar_icon_label.setText("📅")
            calendar_icon_label.setStyleSheet("""
                QLabel {
                    background-color: transparent;
                    border: none;
                    padding: 0px;
                    font-size: 14px;
                }
            """)
        calendar_icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        calendar_icon_label.raise_()
        
        def update_icon_position():
            if date_wrapper.width() > 0 and not calendar_pixmap.isNull():
                # Get actual pixmap size
                pixmap_width = calendar_pixmap.width()
                pixmap_height = calendar_pixmap.height()
                
                # Center the icon in the dropdown area (right 45px)
                icon_x = date_wrapper.width() - 45 + (45 - pixmap_width) // 2
                icon_y = (date_wrapper.height() - pixmap_height) // 2
                calendar_icon_label.setGeometry(icon_x, icon_y, pixmap_width, pixmap_height)
        
        # Store original methods
        original_show = date_wrapper.showEvent
        original_resize = date_wrapper.resizeEvent
        
        def show_with_icon(event):
            if original_show:
                original_show(event)
            update_icon_position()
        
        def resize_with_icon(event):
            if original_resize:
                original_resize(event)
            update_icon_position()
        
        date_wrapper.showEvent = show_with_icon
        date_wrapper.resizeEvent = resize_with_icon
        
        row1_layout.addWidget(date_label)
        row1_layout.addWidget(date_wrapper)
        
        row1_layout.addStretch()
        left_config_layout.addLayout(row1_layout)
        left_config_layout.addSpacing(15)  # Add spacing between rows
        
        # Row 2: Copy Type and E-Way Bill Number
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(10)
        row2_layout.setContentsMargins(0, 0, 0, 0)
        
        # Copy Type checkboxes on row 2
        checkbox_label = QLabel("Copy Type:")
        checkbox_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #212529; min-width: 80px; padding: 2px 0px;")
        checkbox_label.setMinimumHeight(45)
        checkbox_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        checkbox_style = """
            QCheckBox {
                font-size: 14px;
                padding: 5px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 22px;
                height: 22px;
                border: 2px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:hover {
                border-color: #007bff;
            }
            QCheckBox::indicator:checked {
                background-color: #007bff;
                border-color: #007bff;
                image: url(""" + self.checkmark_icon_path.replace('\\', '/') + """);
            }
        """
        
        self.original_checkbox = QCheckBox("Original")
        self.duplicate_checkbox = QCheckBox("Duplicate")
        self.triplicate_checkbox = QCheckBox("Triplicate")
        self.original_checkbox.setStyleSheet(checkbox_style)
        self.duplicate_checkbox.setStyleSheet(checkbox_style)
        self.triplicate_checkbox.setStyleSheet(checkbox_style)
        self.original_checkbox.setMinimumHeight(45)
        self.duplicate_checkbox.setMinimumHeight(45)
        self.triplicate_checkbox.setMinimumHeight(45)
        # Default to Original checked
        self.original_checkbox.setChecked(True)
        
        row2_layout.addWidget(checkbox_label)
        row2_layout.addWidget(self.original_checkbox)
        row2_layout.addSpacing(5)
        row2_layout.addWidget(self.duplicate_checkbox)
        row2_layout.addSpacing(5)
        row2_layout.addWidget(self.triplicate_checkbox)
        row2_layout.addSpacing(30)  # Space before E-Way Bill field
        
        # E-Way Bill Number on same row
        eway_label = QLabel("E-Way Bill No:")
        eway_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #212529; min-width: 100px; padding: 2px 0px;")
        eway_label.setMinimumHeight(45)
        eway_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        self.eway_bill_edit = QLineEdit()
        self.eway_bill_edit.setPlaceholderText("Enter E-Way Bill Number")
        self.eway_bill_edit.setMinimumWidth(250)  # Increased width
        self.eway_bill_edit.setMaximumWidth(250)  # Constrain to prevent expansion
        self.eway_bill_edit.setMinimumHeight(45)
        self.eway_bill_edit.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ced4da;
                border-radius: 5px;
                background-color: white;
                font-size: 14px;
                color: #212529;
            }
            QLineEdit:focus {
                border: 2px solid #007bff;
                background-color: white;
            }
        """)
        
        row2_layout.addWidget(eway_label)
        row2_layout.addWidget(self.eway_bill_edit)
        row2_layout.addStretch()
        left_config_layout.addLayout(row2_layout)
        left_config_layout.addSpacing(5)  # Add spacing below copy type row
        
        config_splitter.addWidget(left_config_widget)
        config_splitter.setStretchFactor(0, 3)
        
        # Right side: Manage Goods button
        right_goods_widget = QWidget()
        right_goods_layout = QVBoxLayout(right_goods_widget)
        right_goods_layout.setContentsMargins(15, 10, 15, 10)
        right_goods_layout.setSpacing(15)
        
        # Add stretch before button to center it vertically
        right_goods_layout.addStretch()
        
        btn_manage_goods = ModernButton("Manage Goods", primary=True)
        btn_manage_goods.setMinimumHeight(45)
        btn_manage_goods.setMinimumWidth(150)
        btn_manage_goods.clicked.connect(self.manage_goods)
        right_goods_layout.addWidget(btn_manage_goods, 0, Qt.AlignmentFlag.AlignCenter if PYQT_VERSION == 6 else Qt.AlignCenter)
        
        # Add stretch after button to center it vertically
        right_goods_layout.addStretch()
        config_splitter.addWidget(right_goods_widget)
        config_splitter.setStretchFactor(1, 1)
        config_splitter.setSizes([600, 200])  # Set initial sizes
        
        top_card.layout.addWidget(config_splitter)
        
        # Main content: Splitter for customer list and details (moved up)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Customer list (moved up)
        customer_list_card = CardWidget("Customer List")
        customer_list_layout = QVBoxLayout()
        
        # Customer list buttons
        customer_btn_layout = QHBoxLayout()
        customer_btn_add = ModernButton("+ Add Customer", primary=True)
        customer_btn_edit = ModernButton("Edit", primary=False)
        customer_btn_manage = ModernButton("Manage", primary=False)
        blaster_btn_manage = ModernButton("Manage Blasters", primary=False)
        customer_btn_add.clicked.connect(self.add_customer)
        customer_btn_edit.clicked.connect(self.edit_selected_customer)
        customer_btn_manage.clicked.connect(self.manage_customers)
        blaster_btn_manage.clicked.connect(self.manage_blasters)
        customer_btn_layout.addWidget(customer_btn_add)
        customer_btn_layout.addWidget(customer_btn_edit)
        customer_btn_layout.addWidget(customer_btn_manage)
        customer_btn_layout.addWidget(blaster_btn_manage)
        customer_btn_layout.addStretch()
        customer_list_layout.addLayout(customer_btn_layout)
        
        # Scrollable customer list
        self.customer_scroll = QScrollArea()
        self.customer_scroll.setWidgetResizable(True)
        self.customer_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                background-color: white;
            }
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #ced4da;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #adb5bd;
            }
        """)
        self.customer_list_widget = QWidget()
        self.customer_list_layout = QVBoxLayout(self.customer_list_widget)
        self.customer_list_layout.setContentsMargins(15, 15, 15, 15)  # Increased margins for broader spacing
        self.customer_list_layout.setSpacing(12)  # Increased spacing between items
        self.customer_list_layout.addStretch()
        self.customer_scroll.setWidget(self.customer_list_widget)
        customer_list_layout.addWidget(self.customer_scroll)
        
        customer_list_card.layout.addLayout(customer_list_layout)
        splitter.addWidget(customer_list_card)
        
        # Right: Customer details
        self.details_card = CardWidget("Customer Details")
        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        self.details_scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                background-color: white;
            }
            QScrollBar:vertical {
                background-color: #f8f9fa;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #ced4da;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #adb5bd;
            }
        """)
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout(self.details_widget)
        self.details_layout.setContentsMargins(15, 15, 15, 15)
        self.details_scroll.setWidget(self.details_widget)
        self.details_card.layout.addWidget(self.details_scroll)
        
        # Initial message
        initial_label = QLabel("Click the arrow (▶) next to a customer to view/edit details")
        initial_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        initial_label.setStyleSheet("font-size: 14px; color: #6c757d; padding: 50px;")
        self.details_layout.addWidget(initial_label)
        
        splitter.addWidget(self.details_card)
        # Customer list: 35% of width, Details: 65% of width
        # Using ratio 7:13 which approximates 35:65
        splitter.setStretchFactor(0, 7)  # Customer list - ~35%
        splitter.setStretchFactor(1, 13)  # Customer details - ~65%
        splitter.setSizes([350, 650])  # Set initial sizes: 35% list, 65% details
        
        # Layout order: Top config (all settings), then customer list/details (main area)
        main_layout.addWidget(top_card)
        main_layout.addWidget(splitter, 1)  # Customer list/details - main area with more space
        
        # Bottom: Action buttons
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        btn_generate = ModernButton("Generate PDFs for Selected Customers", primary=True)
        self.btn_whatsapp = ModernButton("Send via WhatsApp", primary=False)
        self.btn_whatsapp.setEnabled(False)
        btn_clear = ModernButton("Clear Form", primary=False)
        btn_generate.clicked.connect(self.generate_pdfs)
        self.btn_whatsapp.clicked.connect(self.open_whatsapp_dialog)
        btn_clear.clicked.connect(self.clear_form)
        action_layout.addWidget(btn_generate)
        action_layout.addWidget(self.btn_whatsapp)
        action_layout.addWidget(btn_clear)
        main_layout.addLayout(action_layout)
        
        # Load initial data (with placeholder selections)
        self.category_combo.setCurrentIndex(0)  # Set to placeholder "-- Select Category --"
        self.refresh_areas()
        self.area_combo.setCurrentIndex(0)  # Set to placeholder "-- Select Area --"
        self.refresh_vehicles()
        self.vehicle_combo.setCurrentIndex(0)  # Set to placeholder "-- Select Vehicle --"
        self.refresh_customer_list()
    
    def _create_custom_dropdown_popup(self, combo: QComboBox, add_callback, manage_callback):
        """Create a custom popup with scrollable list and fixed action buttons."""
        if PYQT_VERSION == 5:
            from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
        else:
            from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
        
        popup = QWidget()
        if PYQT_VERSION == 6:
            popup.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        else:
            popup.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        
        layout = QVBoxLayout(popup)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Scrollable list view
        list_view = QListView()
        list_view.setMinimumHeight(120)
        list_view.setMaximumHeight(250)
        list_view.setMinimumWidth(combo.width())
        list_view.setFocus()
        list_view.clicked.connect(lambda index: self._handle_popup_selection(combo, popup, index))
        
        # Add keyboard support
        if PYQT_VERSION == 5:
            from PyQt5.QtCore import QEvent
        else:
            from PyQt6.QtCore import QEvent
        
        def list_key_press(event):
            if PYQT_VERSION == 6:
                if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                    current_index = list_view.currentIndex()
                    if current_index.isValid():
                        self._handle_popup_selection(combo, popup, current_index)
                elif event.key() == Qt.Key.Key_Escape:
                    popup.close()
                else:
                    QListView.keyPressEvent(list_view, event)
            else:
                if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                    current_index = list_view.currentIndex()
                    if current_index.isValid():
                        self._handle_popup_selection(combo, popup, current_index)
                elif event.key() == Qt.Key_Escape:
                    popup.close()
                else:
                    QListView.keyPressEvent(list_view, event)
        
        list_view.keyPressEvent = list_key_press
        layout.addWidget(list_view)
        
        # Fixed button row at bottom
        button_row = QWidget()
        button_row.setStyleSheet("background-color: transparent;")
        button_layout = QHBoxLayout(button_row)
        button_layout.setContentsMargins(5, 5, 5, 5)
        button_layout.setSpacing(5)
        
        add_btn = ModernButton("+ Add", primary=True)
        add_btn.clicked.connect(lambda: self._handle_popup_action(popup, add_callback))
        manage_btn = ModernButton("Manage", primary=False)
        manage_btn.clicked.connect(lambda: self._handle_popup_action(popup, manage_callback))
        
        button_layout.addWidget(add_btn)
        button_layout.addWidget(manage_btn)
        layout.addWidget(button_row)
        
        popup.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #d0d7de;
                border-radius: 8px;
            }
            QListView {
                background-color: white;
                border: none;
                padding: 4px;
                outline: 0;
            }
            QListView::item {
                padding: 8px 10px;
                border-radius: 5px;
                color: #212529;
            }
            QListView::item:hover {
                background-color: #f5f6f8;
            }
            QListView::item:selected {
                background-color: #eaf2ff;
                color: #0d6efd;
            }
            QScrollBar:vertical {
                background-color: #e9ecef;
                width: 12px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #adb5bd;
                min-height: 30px;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6c757d;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                border: none;
                background: transparent;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                width: 0px;
                height: 0px;
            }
        """)
        
        combo._custom_popup = popup
        combo._custom_list_view = list_view
        return popup
    
    def _handle_popup_selection(self, combo, popup, index):
        """Handle selection from custom popup."""
        # Set the exact index - no offset needed
        combo.setCurrentIndex(index.row())
        popup.close()
    
    def _handle_popup_action(self, popup, callback):
        """Handle action button click from popup."""
        popup.close()
        if callback:
            callback()
    
    def _add_combo_keyboard_support(self, combo):
        """Add keyboard support to combo box."""
        if PYQT_VERSION == 5:
            from PyQt5.QtCore import QEvent
        else:
            from PyQt6.QtCore import QEvent
        
        original_key_press = combo.keyPressEvent
        
        def combo_key_press(event):
            # Check if this is area or vehicle combo
            is_area_or_vehicle = combo == self.area_combo or combo == self.vehicle_combo
            
            if PYQT_VERSION == 6:
                if event.key() == Qt.Key.Key_Down or event.key() == Qt.Key.Key_Up:
                    # Check category for area/vehicle
                    if is_area_or_vehicle and not self.current_category:
                        QMessageBox.warning(self, "Category Required", "Please select a Category first.")
                        return
                    # Open popup if not already open
                    if not hasattr(combo, '_custom_popup') or not combo._custom_popup.isVisible():
                        self._show_custom_popup(combo)
                    else:
                        # Pass event to list view
                        if hasattr(combo, '_custom_list_view'):
                            QListView.keyPressEvent(combo._custom_list_view, event)
                else:
                    original_key_press(event)
            else:
                if event.key() == Qt.Key_Down or event.key() == Qt.Key_Up:
                    # Check category for area/vehicle
                    if is_area_or_vehicle and not self.current_category:
                        QMessageBox.warning(self, "Category Required", "Please select a Category first.")
                        return
                    # Open popup if not already open
                    if not hasattr(combo, '_custom_popup') or not combo._custom_popup.isVisible():
                        self._show_custom_popup(combo)
                    else:
                        # Pass event to list view
                        if hasattr(combo, '_custom_list_view'):
                            QListView.keyPressEvent(combo._custom_list_view, event)
                else:
                    original_key_press(event)
        
        combo.keyPressEvent = combo_key_press
    
    def _check_category_and_show_popup(self, combo, field_name):
        """Check if category is selected before showing popup."""
        if not self.current_category:
            QMessageBox.warning(
                self,
                "Category Required",
                f"Please select a Category first before choosing {field_name}."
            )
            return
        self._show_custom_popup(combo)
    
    def _show_custom_popup(self, combo):
        """Show the custom popup for a combo box."""
        if not hasattr(combo, '_custom_popup'):
            return
        
        popup = combo._custom_popup
        list_view = combo._custom_list_view
        
        # Create a model with all combo box items
        if PYQT_VERSION == 5:
            from PyQt5.QtGui import QStandardItemModel, QStandardItem
        else:
            from PyQt6.QtGui import QStandardItemModel, QStandardItem
        
        model = QStandardItemModel()
        # Add all items from combo box
        for i in range(combo.count()):
            item = QStandardItem(combo.itemText(i))
            item.setData(combo.itemData(i, Qt.ItemDataRole.UserRole), Qt.ItemDataRole.UserRole)
            model.appendRow(item)
        
        list_view.setModel(model)
        
        # Set current selection in list view to match combo box
        current_index = combo.currentIndex()
        if current_index >= 0:
            list_view.setCurrentIndex(model.index(current_index, 0))
        
        # Position popup below combo box
        global_pos = combo.mapToGlobal(combo.rect().bottomLeft())
        popup.move(global_pos)
        popup.show()
        popup.raise_()
        popup.activateWindow()
        list_view.setFocus()
    
    def _apply_professional_dropdown(self, combo: QComboBox):
        """Style dropdowns to float cleanly with a subtle shadow on a transparent backdrop."""
        view = QListView()
        view.setSpacing(3)
        try:
            view.setFrameShape(QFrame.Shape.NoFrame)
        except AttributeError:
            view.setFrameShape(QFrame.NoFrame)
        view.setUniformItemSizes(True)
        try:
            view.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        except AttributeError:
            view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        
        # Set consistent dimensions for both area and vehicle dropdowns
        view.setMinimumWidth(combo.minimumWidth())
        view.setMinimumHeight(150)
        view.setMaximumHeight(280)
        
        if PYQT_VERSION == 6:
            view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            view.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        else:
            view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            view.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        try:
            view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        except AttributeError:
            view.setAttribute(Qt.WA_TranslucentBackground, True)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(8)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 35))
        view.setGraphicsEffect(shadow)
        
        view.setStyleSheet("""
            QListView {
                background-color: #ffffff;
                border: 1px solid #d0d7de;
                border-radius: 8px;
                padding: 4px;
                outline: 0;
            }
            QListView::item {
                padding: 8px 10px;
                border-radius: 5px;
                color: #212529;
            }
            QListView::item:hover {
                background-color: #f5f6f8;
            }
            QListView::item:selected {
                background-color: #eaf2ff;
                color: #0d6efd;
            }
            QScrollBar:vertical {
                background-color: #e9ecef;
                width: 12px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background-color: #adb5bd;
                min-height: 30px;
                border-radius: 2px;
                margin: 0px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #6c757d;
            }
            QScrollBar::add-line:vertical {
                height: 0px;
                border: none;
                background: transparent;
            }
            QScrollBar::sub-line:vertical {
                height: 0px;
                border: none;
                background: transparent;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                width: 0px;
                height: 0px;
                background: transparent;
            }
        """)
        combo.setView(view)
        
        # Store the view reference and combo for later styling of action items
        combo._custom_view = view
        combo._needs_action_styling = True
        
        # Apply custom delegate for action buttons
        if PYQT_VERSION == 5:
            from PyQt5.QtWidgets import QStyledItemDelegate, QStyle
            from PyQt5.QtGui import QPainter, QBrush, QPen
            from PyQt5.QtCore import QRect
        else:
            from PyQt6.QtWidgets import QStyledItemDelegate, QStyle
            from PyQt6.QtGui import QPainter, QBrush, QPen
            from PyQt6.QtCore import QRect
        
        class ActionItemDelegate(QStyledItemDelegate):
            def paint(self, painter, option, index):
                data = index.data(Qt.ItemDataRole.UserRole)
                
                # Check if this is an action item
                if isinstance(data, str) and (data.startswith("__cmd_")):
                    painter.save()
                    
                    # Determine button color
                    if "+ Add" in index.data(Qt.ItemDataRole.DisplayRole):
                        bg_color = QColor(40, 167, 69)  # Green
                        hover_color = QColor(33, 136, 56)
                    else:  # Manage
                        bg_color = QColor(0, 123, 255)  # Blue
                        hover_color = QColor(0, 86, 179)
                    
                    # Use hover color if hovered
                    if PYQT_VERSION == 6:
                        is_hovered = option.state & QStyle.StateFlag.State_MouseOver
                    else:
                        is_hovered = option.state & QStyle.State_MouseOver
                    
                    if is_hovered:
                        bg_color = hover_color
                    
                    # Draw button background
                    rect = option.rect.adjusted(4, 2, -4, -2)
                    if PYQT_VERSION == 6:
                        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                        painter.setPen(QPen(Qt.PenStyle.NoPen))
                    else:
                        painter.setRenderHint(QPainter.Antialiasing)
                        painter.setPen(QPen(Qt.NoPen))
                    painter.setBrush(QBrush(bg_color))
                    painter.drawRoundedRect(rect, 5, 5)
                    
                    # Draw text
                    painter.setPen(QPen(QColor(255, 255, 255)))
                    if PYQT_VERSION == 6:
                        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, index.data(Qt.ItemDataRole.DisplayRole))
                    else:
                        painter.drawText(rect, Qt.AlignCenter, index.data(Qt.ItemDataRole.DisplayRole))
                    
                    painter.restore()
                else:
                    # Normal item
                    super().paint(painter, option, index)
        
        view.setItemDelegate(ActionItemDelegate())
    
    def _open_simple_manager(self, title, fetch_items_fn, add_fn, edit_fn, delete_fn, display_key):
        """Generic manager dialog for simple list-based entities."""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout(dialog)
        list_widget = QListWidget()
        layout.addWidget(list_widget)
        
        def refresh():
            list_widget.clear()
            for item in fetch_items_fn():
                display = item.get(display_key, "") or "(No name)"
                # Display customer names in uppercase
                if display_key == "name" and title == "Manage Customers":
                    display = display.upper() if display else "(No name)"
                list_item = QListWidgetItem(display)
                if PYQT_VERSION == 6:
                    list_item.setData(Qt.ItemDataRole.UserRole, item)
                else:
                    list_item.setData(Qt.UserRole, item)
                list_widget.addItem(list_item)
        refresh()
        
        btn_row = QHBoxLayout()
        btn_add = ModernButton("Add", primary=True)
        btn_edit = ModernButton("Edit", primary=False)
        btn_delete = ModernButton("Delete", primary=False)
        btn_close = ModernButton("Close", primary=False)
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_delete)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)
        
        def current_item():
            item = list_widget.currentItem()
            if not item:
                QMessageBox.warning(dialog, "Select Item", "Please select an entry first.")
                return None
            return item.data(Qt.ItemDataRole.UserRole)
        
        def add_action():
            changed = add_fn()
            if changed:
                refresh()
        def edit_action():
            data = current_item()
            if not data:
                return
            changed = edit_fn(data)
            if changed:
                refresh()
        def delete_action():
            data = current_item()
            if not data:
                return
            changed = delete_fn(data)
            if changed:
                refresh()
        
        btn_add.clicked.connect(add_action)
        btn_edit.clicked.connect(edit_action)
        btn_delete.clicked.connect(delete_action)
        btn_close.clicked.connect(dialog.close)
        
        dialog.exec_() if PYQT_VERSION == 5 else dialog.exec()
    
    def on_area_activated(self, index):
        """Handle special commands from area dropdown"""
        data = self.area_combo.itemData(index, Qt.ItemDataRole.UserRole)
        if isinstance(data, str) and data.startswith("__cmd_area_"):
            if data == "__cmd_area_add":
                self.add_area()
            elif data == "__cmd_area_manage":
                self.manage_areas()
            # restore previous valid selection
            if hasattr(self, "_last_area_index") and self._last_area_index is not None:
                self.area_combo.setCurrentIndex(self._last_area_index)
            else:
                self.area_combo.setCurrentIndex(0)
            return
        self._last_area_index = index
    
    def on_category_changed(self):
        """Handle category selection"""
        # During initialization the signal may fire before widgets exist
        if not hasattr(self, "area_combo"):
            return
        
        # Get category from combo box
        category_data = self.category_combo.currentData()
        if category_data:
            self.current_category = category_data
        else:
            self.current_category = None
        
        self.current_area_id = None
        self.area_combo.setCurrentIndex(0)
        self.selected_customers = {}
        self.refresh_areas()
        self.refresh_customer_list()
    
    def refresh_areas(self):
        """Refresh area combobox"""
        self.area_combo.clear()
        self.area_combo.addItem("-- Select Area --", None)  # Add placeholder
        areas = self.db.get_locations()
        for area in areas:
            self.area_combo.addItem(area['name'], area['id'])
        # Don't auto-select, leave it at -1 (no selection)
    
    def on_area_changed(self):
        """Handle area selection"""
        data = self.area_combo.currentData()
        if isinstance(data, str) and data.startswith("__cmd_area_"):
            return
        if self.area_combo.currentIndex() > 0 and data is not None:
            self.current_area_id = data
            self.current_area_name = self.area_combo.currentText()
        else:
            self.current_area_id = None
            self.current_area_name = None
        
        self.selected_customers = {}
        self.refresh_customer_list()
    
    def refresh_vehicles(self):
        """Refresh vehicle combobox"""
        self.vehicle_combo.clear()
        self.vehicle_combo.addItem("-- Select Vehicle --", None)  # Add placeholder
        vehicles = self.db.get_vehicles()
        for vehicle in vehicles:
            self.vehicle_combo.addItem(vehicle['vehicle_number'])
        # Leave empty (no selection) by default
    
    def refresh_customer_list(self):
        """Refresh customer list display"""
        # Clear existing widgets
        while self.customer_list_layout.count() > 1:  # Keep stretch
            item = self.customer_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.current_area_id:
            label = QLabel("Please select an area first")
            label.setStyleSheet("font-size: 13px; color: #6c757d; padding: 20px;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.customer_list_layout.insertWidget(0, label)
            return
        
        # Get customers for this area
        customers = self.db.get_customers(location_id=self.current_area_id)
        
        if not customers:
            label = QLabel("No customers found for this area.\nClick 'Add Customer' to add one.")
            label.setStyleSheet("font-size: 13px; color: #6c757d; padding: 20px;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.customer_list_layout.insertWidget(0, label)
            return
        
        # Create customer items
        for customer in customers:
            customer_id = customer['id']
            is_selected = customer_id in self.selected_customers
            item_widget = CustomerItemWidget(customer_id, customer['name'], self.checkmark_icon_path, is_selected)
            item_widget.checkbox.toggled.connect(
                lambda checked, cid=customer_id: self.on_customer_check(cid, checked)
            )
            item_widget.expand_btn.clicked.connect(
                lambda checked, cid=customer_id: self.toggle_customer_details(cid)
            )
            self.customer_list_layout.insertWidget(
                self.customer_list_layout.count() - 1, item_widget
            )
    
    def on_customer_check(self, customer_id, checked):
        """Handle customer checkbox toggle"""
        if checked:
            customer = self.db.get_customer(customer_id)
            if customer:
                # Initialize with empty invoice numbers - user must enter them in customer details
                selected_count = len(self.selected_customers)
                # Auto-increment based on previous customers' invoice numbers
                base_invoice = ""
                base_eway = ""
                if self.selected_customers:
                    # Get the last customer's invoice number to increment from
                    last_customer_data = list(self.selected_customers.values())[-1]
                    base_invoice = last_customer_data.get('invoice_no', '')
                    base_eway = last_customer_data.get('e_way_doc_no', '')
                
                # Auto-increment logic
                invoice_no = self.auto_increment_number(base_invoice, 1) if base_invoice else ""
                eway_doc_no = self.auto_increment_number(base_eway, 1) if base_eway else ""
                
                # Initialize blaster data from customer
                blaster_id = customer.get('blaster_id')
                blaster_data = {}
                if blaster_id:
                    blaster = self.db.get_blaster(blaster_id)
                    if blaster:
                        blaster_data = {
                            'blaster_name': blaster.get('name', ''),
                            'blaster_document_no': blaster.get('document_no', ''),
                            'blaster_address': blaster.get('address', '')
                        }
                
                self.selected_customers[customer_id] = {
                    'customer': customer,
                    'invoice_no': invoice_no,
                    'e_way_doc_no': eway_doc_no,
                    'items': [],
                    'place_of_supply': customer.get('address', '') or self.current_area_name or '',
                    'gstin_unique_id': '',  # Start empty, user can fill it
                    'blaster_id': blaster_id,
                    'blaster_data': blaster_data,
                    'freight_charges': 0.0
                }
                
                # When a customer is selected, automatically show their details
                # so invoice fields and items section become visible.
                self.expanded_customer_id = customer_id
                self.show_customer_details(customer_id)
        else:
            if customer_id in self.selected_customers:
                del self.selected_customers[customer_id]
            if self.expanded_customer_id == customer_id:
                self.clear_customer_details()
                self.expanded_customer_id = None
        
        # Enable WhatsApp button only when something is selected
        if hasattr(self, "btn_whatsapp"):
            self.btn_whatsapp.setEnabled(bool(self.selected_customers))

    def open_whatsapp_dialog(self):
        """Open WhatsApp sending dialog for selected customers."""
        if not self.selected_customers:
            QMessageBox.warning(self, "Select Customers", "Please select at least one customer first.")
            return
        
        # Build bills list from the same invoice_data used for PDF generation
        if not self.current_category:
            QMessageBox.warning(self, "Category Required", "Please select a Category first.")
            return
        if not self.current_area_id:
            QMessageBox.warning(self, "Warning", "Please select an area")
            return
        
        # Validate invoice numbers are entered for all selected customers (same as PDF flow)
        missing_invoices = []
        for customer_id, customer_data in self.selected_customers.items():
            invoice_no = customer_data.get('invoice_no', '').strip()
            if not invoice_no:
                customer_name = customer_data['customer'].get('name', 'Unknown')
                missing_invoices.append(customer_name.upper() if customer_name else 'Unknown')
        if missing_invoices:
            QMessageBox.warning(self, "Warning",
                "Invoice number is required for:\n" + "\n".join(missing_invoices))
            return
        
        # Date of supply + vehicle (use current UI values if available)
        try:
            date_of_supply = self.date_edit.date().toString("dd-MM-yyyy")
        except Exception:
            date_of_supply = ""
        vehicle_number = self.vehicle_combo.currentText() if hasattr(self, "vehicle_combo") else ""
        e_way_bill_no = self.eway_bill_edit.text().strip() if hasattr(self, "eway_bill_edit") else ""
        
        bills = []
        for customer_id, customer_data in self.selected_customers.items():
            customer = customer_data.get('customer') or {}
            items = customer_data.get('items', []) or []
            total_items = sum(item.get('total_amount', 0) for item in items) if items else 0
            freight = customer_data.get('freight_charges', 0) or 0
            grand_total = total_items + freight
            rounded_total = self._round_total(grand_total)
            
            blaster_data = customer_data.get('blaster_data', {}) or {}
            blaster_name = blaster_data.get('blaster_name') or customer.get('blaster_name', '')
            blaster_doc = blaster_data.get('blaster_document_no') or customer.get('blaster_document_no', '')
            blaster_address = blaster_data.get('blaster_address') or customer.get('blaster_address', '')
            
            bills.append({
                'invoice_number': customer_data.get('invoice_no', ''),
                'date_of_supply': date_of_supply,
                'category': self.current_category or '',
                'location_name': self.current_area_name or '',
                'vehicle_number': vehicle_number or '',
                'customer': customer,
                'mode_of_transport': 'Road',
                'is_original': self.original_checkbox.isChecked() if hasattr(self, "original_checkbox") else False,
                'is_duplicate': self.duplicate_checkbox.isChecked() if hasattr(self, "duplicate_checkbox") else False,
                'is_triplicate': self.triplicate_checkbox.isChecked() if hasattr(self, "triplicate_checkbox") else False,
                'e_way_bill_no': e_way_bill_no,
                'e_way_document_no': customer_data.get('e_way_doc_no', ''),
                'place_of_supply': customer_data.get('place_of_supply', '') or customer.get('address', ''),
                'state_code': '33',
                'gstin_unique_id': customer_data.get('gstin_unique_id', ''),
                'items': items,
                'freight_charges': float(freight) if freight else 0.0,
                'grand_total': float(rounded_total),
                'total_in_words': '',
                'blaster_name': blaster_name or '',
                'document_no': blaster_doc or '',
                'blaster_address': blaster_address or ''
            })
        
        dialog = WhatsAppDialog(self, bills=bills, default_company_name="Senthil Explosives")
        dialog.exec_() if PYQT_VERSION == 5 else dialog.exec()
    
    def auto_increment_number(self, base_number, offset):
        """Auto-increment a number string"""
        if not base_number:
            return ""
        
        try:
            match = re.search(r'(\d+)', base_number)
            if match:
                base_num = int(match.group(1))
                new_num = base_num + offset
                return re.sub(r'\d+', str(new_num), base_number, count=1)
            else:
                return f"{base_number}_{offset + 1}"
        except:
            return f"{base_number}_{offset + 1}"
    
    def toggle_customer_details(self, customer_id):
        """Toggle customer details display"""
        if self.expanded_customer_id == customer_id:
            self.clear_customer_details()
            self.expanded_customer_id = None
        else:
            self.expanded_customer_id = customer_id
            self.show_customer_details(customer_id)
    
    def show_customer_details(self, customer_id):
        """Show customer details"""
        # Clear details
        while self.details_layout.count():
            item = self.details_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        customer = self.db.get_customer(customer_id)
        if not customer:
            return
        
        is_selected = customer_id in self.selected_customers
        customer_data = self.selected_customers.get(customer_id)
        
        # Customer name header - fixed to prevent overlapping
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 10)
        
        name_label = QLabel(customer['name'].upper() if customer.get('name') else '')
        name_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #212529;")
        name_label.setWordWrap(True)  # Allow text wrapping
        name_label.setMaximumWidth(350)  # Limit width to prevent overflow
        name_label.setMinimumHeight(30)  # Ensure enough height for wrapping
        header_layout.addWidget(name_label, 1)  # Allow it to expand
        
        if is_selected:
            edit_btn = ModernButton("Edit", primary=True)
            edit_btn.clicked.connect(lambda: self.edit_customer_from_details(customer_id))
            header_layout.addWidget(edit_btn)
        else:
            header_layout.addStretch()
        
        self.details_layout.addWidget(header_frame)
        
        # Receiver details
        receiver_group = QGroupBox("Receiver Details")
        receiver_layout = QVBoxLayout()
        
        details = [
            ("Phone", customer.get('phone', '')),
            ("Address", customer.get('address', '')),
            ("SF.NO", customer.get('sf_no', '')),
            ("RC.NO", customer.get('rc_no', '')),
            ("State", customer.get('state', '')),
            ("GSTIN", customer.get('gstin', ''))
        ]
        
        for label, value in details:
            if value:
                row_layout = QHBoxLayout()
                label_widget = QLabel(f"<b>{label}:</b>")
                label_widget.setMinimumWidth(100)
                row_layout.addWidget(label_widget)
                # Display in uppercase
                value_label = QLabel(str(value).upper())
                value_label.setWordWrap(True)  # Allow wrapping for long addresses
                value_label.setMaximumWidth(400)
                row_layout.addWidget(value_label, 1)
                row_layout.addStretch()
                receiver_layout.addLayout(row_layout)
        
        receiver_group.setLayout(receiver_layout)
        self.details_layout.addWidget(receiver_group)
        
        # Invoice details (only if selected)
        if is_selected and customer_data:
            invoice_group = QGroupBox("Invoice Details")
            # Use a form layout so all labels/fields align nicely
            if PYQT_VERSION == 5:
                from PyQt5.QtWidgets import QFormLayout
            else:
                from PyQt6.QtWidgets import QFormLayout
            invoice_layout = QFormLayout()
            invoice_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            invoice_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            invoice_layout.setHorizontalSpacing(20)
            invoice_layout.setVerticalSpacing(8)
            
            # Common style for key labels (left aligned with subtle border)
            key_label_style = (
                "font-size: 12px;"
                "font-weight: bold;"
                "color: #212529;"
                "border: 1px solid #dee2e6;"
                "border-radius: 4px;"
                "padding: 4px 8px;"
                "min-width: 140px;"
                "background-color: #f8f9fa;"
            )
            
            # Invoice No (Mandatory)
            invoice_label = QLabel("Invoice No: *")
            invoice_label.setStyleSheet(key_label_style)
            invoice_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            invoice_edit = QLineEdit(customer_data.get('invoice_no', ''))
            invoice_edit.setPlaceholderText("Enter invoice number (required)")
            invoice_edit.setMaximumWidth(400)
            # Convert to uppercase as user types and update
            def update_invoice(text):
                upper_text = text.upper()
                if text != upper_text:
                    invoice_edit.setText(upper_text)
                else:
                    self.update_customer_invoice_no(customer_id, upper_text)
            invoice_edit.textChanged.connect(update_invoice)
            invoice_layout.addRow(invoice_label, invoice_edit)
            
            # E-Way Doc No
            eway_label = QLabel("E-Way Document No:")
            eway_label.setStyleSheet(key_label_style)
            eway_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            eway_edit = QLineEdit(customer_data.get('e_way_doc_no', ''))
            eway_edit.setPlaceholderText("Enter E-Way document number")
            eway_edit.setMaximumWidth(400)
            # Convert to uppercase as user types and update
            def update_eway(text):
                upper_text = text.upper()
                if text != upper_text:
                    eway_edit.setText(upper_text)
                else:
                    self.update_customer_eway_doc(customer_id, upper_text)
            eway_edit.textChanged.connect(update_eway)
            invoice_layout.addRow(eway_label, eway_edit)
            
            # Place of Supply (Editable)
            place_label = QLabel("Place of Supply:")
            place_label.setStyleSheet(key_label_style)
            place_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            place_edit = QLineEdit(customer_data.get('place_of_supply', customer.get('address', '') or self.current_area_name or ''))
            place_edit.setPlaceholderText("Enter place of supply")
            place_edit.setMaximumWidth(400)
            # Convert to uppercase as user types and update
            def update_place(text):
                upper_text = text.upper()
                if text != upper_text:
                    place_edit.setText(upper_text)
                else:
                    self.update_customer_place_of_supply(customer_id, upper_text)
            place_edit.textChanged.connect(update_place)
            invoice_layout.addRow(place_label, place_edit)
            
            # GSTIN/Unique ID (Editable) - starts empty
            gstin_label = QLabel("GSTIN/Unique ID:")
            gstin_label.setStyleSheet(key_label_style)
            gstin_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            gstin_edit = QLineEdit(customer_data.get('gstin_unique_id', ''))
            gstin_edit.setPlaceholderText("Enter GSTIN/Unique ID (optional)")
            gstin_edit.setMaximumWidth(400)
            # Convert to uppercase as user types and update
            def update_gstin(text):
                upper_text = text.upper()
                if text != upper_text:
                    gstin_edit.setText(upper_text)
                else:
                    self.update_customer_gstin_unique_id(customer_id, upper_text)
            gstin_edit.textChanged.connect(update_gstin)
            invoice_layout.addRow(gstin_label, gstin_edit)
            
            invoice_group.setLayout(invoice_layout)
            self.details_layout.addWidget(invoice_group)
            
            # Blaster Details (Selectable with management) - always show if customer is selected
            blaster_group = QGroupBox("Blaster Details")
            # Use a form layout for aligned labels/fields
            if PYQT_VERSION == 5:
                from PyQt5.QtWidgets import QFormLayout
            else:
                from PyQt6.QtWidgets import QFormLayout
            blaster_layout = QFormLayout()
            blaster_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            blaster_layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            blaster_layout.setHorizontalSpacing(20)
            blaster_layout.setVerticalSpacing(8)
            
            # Reuse the same key label style as invoice section
            blaster_key_label_style = (
                "font-size: 12px;"
                "font-weight: bold;"
                "color: #212529;"
                "border: 1px solid #dee2e6;"
                "border-radius: 4px;"
                "padding: 4px 8px;"
                "min-width: 140px;"
                "background-color: #f8f9fa;"
            )
            
            # Blaster selection row
            blaster_select_label = QLabel("Blaster:")
            blaster_select_label.setStyleSheet(blaster_key_label_style)
            blaster_select_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            # Blaster combo box - match Area/Vehicle width
            blaster_combo = NoWheelComboBox()
            blaster_combo.setMinimumWidth(180)
            blaster_combo.setMaximumWidth(180)
            blaster_combo.setMinimumHeight(45)
            blaster_combo.setEditable(False)
            blaster_combo.setStyleSheet(self.dropdown_field_style)
            blasters = self.db.get_blasters()
            blaster_combo.addItem("-- No Blaster --", None)
            
            # Get current blaster_id from customer_data or customer
            current_blaster_id = customer_data.get('blaster_id') or customer.get('blaster_id')
            
            # Add all blasters to combo
            for blaster in blasters:
                blaster_combo.addItem(blaster['name'], blaster['id'])
            
            # Set current selection after all items are added
            if current_blaster_id:
                index = blaster_combo.findData(current_blaster_id)
                if index >= 0:
                    blaster_combo.setCurrentIndex(index)
            
            # Disable default popup, use custom one
            blaster_combo.setMaxVisibleItems(0)
            blaster_combo.view().setVisible(False)
            
            # Create wrapper functions for callbacks
            def add_blaster_callback():
                self.add_blaster_from_details(customer_id, blaster_combo)
            
            def manage_blasters_callback():
                self.manage_blasters_from_details(customer_id, blaster_combo)
            
            # Create custom popup with fixed buttons
            self._create_custom_dropdown_popup(blaster_combo, add_blaster_callback, manage_blasters_callback)
            # Override showPopup to use custom popup
            blaster_combo.showPopup = lambda: self._show_custom_popup(blaster_combo)
            
            blaster_layout.addRow(blaster_select_label, blaster_combo)
            
            # Function to update blaster fields when selection changes
            def on_blaster_selected():
                blaster_id = blaster_combo.currentData()
                if blaster_id:
                    blaster = self.db.get_blaster(blaster_id)
                    if blaster:
                        blaster_doc_edit.setText(blaster.get('document_no', '') or '')
                        blaster_addr_edit.setText(blaster.get('address', '') or '')
                        # Update customer_data
                        if 'blaster_data' not in customer_data:
                            customer_data['blaster_data'] = {}
                        customer_data['blaster_id'] = blaster_id
                        customer_data['blaster_data']['blaster_name'] = blaster.get('name', '')
                        customer_data['blaster_data']['blaster_document_no'] = blaster.get('document_no', '')
                        customer_data['blaster_data']['blaster_address'] = blaster.get('address', '')
                else:
                    blaster_doc_edit.clear()
                    blaster_addr_edit.clear()
                    if 'blaster_data' in customer_data:
                        customer_data['blaster_data'] = {}
                    customer_data['blaster_id'] = None
            
            # Get initial blaster data and set combo box
            blaster_data = customer_data.get('blaster_data', {})
            if not blaster_data and current_blaster_id:
                blaster = self.db.get_blaster(current_blaster_id)
                if blaster:
                    blaster_data = {
                        'blaster_name': blaster.get('name', ''),
                        'blaster_document_no': blaster.get('document_no', ''),
                        'blaster_address': blaster.get('address', '')
                    }
                    customer_data['blaster_data'] = blaster_data
                    customer_data['blaster_id'] = current_blaster_id
                    # Set combo box to current blaster
                    index = blaster_combo.findData(current_blaster_id)
                    if index >= 0:
                        blaster_combo.setCurrentIndex(index)
            
            blaster_doc_value = blaster_data.get('blaster_document_no', '') or customer.get('blaster_document_no', '')
            blaster_addr_value = blaster_data.get('blaster_address', '') or customer.get('blaster_address', '')
            
            # Blaster Document No (Editable)
            blaster_doc_label = QLabel("Document No:")
            blaster_doc_label.setStyleSheet(blaster_key_label_style)
            blaster_doc_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            blaster_doc_edit = QLineEdit(blaster_doc_value)
            blaster_doc_edit.setPlaceholderText("Enter document number")
            blaster_doc_edit.setMaximumWidth(400)
            # Convert to uppercase as user types and update
            def update_blaster_doc(text):
                upper_text = text.upper()
                if text != upper_text:
                    blaster_doc_edit.setText(upper_text)
                else:
                    self.update_customer_blaster_doc(customer_id, upper_text)
            blaster_doc_edit.textChanged.connect(update_blaster_doc)
            blaster_layout.addRow(blaster_doc_label, blaster_doc_edit)
            
            # Blaster Address (Editable)
            blaster_addr_label = QLabel("Address:")
            blaster_addr_label.setStyleSheet(blaster_key_label_style)
            blaster_addr_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            blaster_addr_edit = QLineEdit(blaster_addr_value)
            blaster_addr_edit.setPlaceholderText("Enter blaster address")
            blaster_addr_edit.setMaximumWidth(400)
            # Convert to uppercase as user types and update
            def update_blaster_addr(text):
                upper_text = text.upper()
                if text != upper_text:
                    blaster_addr_edit.setText(upper_text)
                else:
                    self.update_customer_blaster_address(customer_id, upper_text)
            blaster_addr_edit.textChanged.connect(update_blaster_addr)
            blaster_layout.addRow(blaster_addr_label, blaster_addr_edit)
            
            # Connect signal after fields are created to avoid errors
            blaster_combo.currentIndexChanged.connect(lambda: on_blaster_selected())
            
            blaster_group.setLayout(blaster_layout)
            self.details_layout.addWidget(blaster_group)
            
            # Freight Charges (Editable)
            freight_row = QHBoxLayout()
            freight_label = QLabel("Freight Charges:")
            freight_label.setMinimumWidth(100)
            freight_row.addWidget(freight_label)
            freight_edit = QLineEdit()
            freight_value = customer_data.get('freight_charges', 0.0)
            freight_edit.setText(f"{freight_value:.2f}" if freight_value else "0.00")
            freight_edit.setPlaceholderText("0.00")
            freight_edit.setMaximumWidth(400)
            freight_edit.textChanged.connect(
                lambda text: self.update_customer_freight_charges(customer_id, text)
            )
            freight_row.addWidget(freight_edit)
            freight_row.addStretch()
            self.details_layout.addLayout(freight_row)
            
            # Items section - Excel-like table
            items_group = QGroupBox("Goods Selection")
            items_layout = QVBoxLayout()
            items_layout.setContentsMargins(15, 15, 15, 15)  # Add margins so borders are visible
            items_layout.setSpacing(10)  # Add spacing between button and table
            
            add_item_btn = ModernButton("+ Add Good", primary=True)
            add_item_btn.clicked.connect(lambda: self.add_good_to_customer(customer_id))
            items_layout.addWidget(add_item_btn)
            
            # Create table - NO separate header widget, just rows!
            items_table = QTableWidget()
            items_table.setColumnCount(6)
            items_table.setRowCount(1)  # Start with 1 row for header
            
            # HIDE the built-in header widgets - we'll use row 0 as header
            items_table.horizontalHeader().setVisible(False)
            items_table.verticalHeader().setVisible(False)
            
            # Excel-like styling - use cell borders for complete grid
            items_table.setStyleSheet("""
                QTableWidget {
                    background-color: white;
                    border: 1px solid #c0c0c0;
                    outline: none;
                }
                QTableWidget::item {
                    border: 1px solid #c0c0c0;
                    padding: 2px;
                    color: #000000;
                }
                QTableWidget::item:selected {
                    background-color: #cfe2f3;
                }
            """)
            
            # Set column widths
            items_table.setColumnWidth(0, 220)  # Description
            items_table.setColumnWidth(1, 90)   # HSN
            items_table.setColumnWidth(2, 60)   # Qty
            items_table.setColumnWidth(3, 90)   # Rate
            items_table.setColumnWidth(4, 90)   # Total
            items_table.setColumnWidth(5, 120)  # Actions
            
            # Create header row (row 0) with grey background
            header_labels = ["Description", "HSN", "Qty", "Rate", "Total", "Actions"]
            for col, label in enumerate(header_labels):
                header_item = QTableWidgetItem(label)
                header_item.setBackground(QColor("#d9d9d9"))
                header_item.setForeground(QColor("#000000"))
                if PYQT_VERSION == 5:
                    from PyQt5.QtGui import QFont
                else:
                    from PyQt6.QtGui import QFont
                font = QFont()
                font.setBold(True)
                font.setPointSize(10)
                header_item.setFont(font)
                header_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                try:
                    header_item.setFlags(header_item.flags() & ~Qt.ItemFlag.ItemIsSelectable & ~Qt.ItemFlag.ItemIsEditable)
                except:
                    header_item.setFlags(header_item.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEditable)
                items_table.setItem(0, col, header_item)
            
            # Set header row height
            items_table.setRowHeight(0, 32)
            
            # Table settings
            items_table.setShowGrid(False)  # Using cell borders instead
            items_table.setMinimumHeight(150)
            items_table.setMaximumHeight(400)
            
            # Add small left margin to push content right and make left border visible
            items_table.setViewportMargins(3, 0, 0, 0)
            
            items_table.setAlternatingRowColors(False)
            
            # Enable scrollbars inside the table widget
            try:
                items_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                items_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                items_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
                items_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
                items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            except AttributeError:
                items_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                items_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                items_table.setSelectionBehavior(QTableWidget.SelectRows)
                items_table.setSelectionMode(QTableWidget.SingleSelection)
                items_table.setEditTriggers(QTableWidget.NoEditTriggers)
            
            # Prevent columns from auto-stretching so horizontal scrollbar appears when needed
            try:
                items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
            except AttributeError:
                items_table.horizontalHeader().setResizeMode(QHeaderView.Fixed)
            
            # Set size policy to expand horizontally to match button width
            try:
                items_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            except AttributeError:
                items_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            
            items_layout.addWidget(items_table)
            items_group.setLayout(items_layout)
            self.details_layout.addWidget(items_group)
            
            # Store references
            customer_data['items_table'] = items_table
            self.refresh_customer_items(customer_id)
        else:
            info_label = QLabel("Select this customer (checkbox) to add invoice details and items")
            info_label.setStyleSheet("font-size: 13px; color: #6c757d; padding: 20px;")
            info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.details_layout.addWidget(info_label)
        
        self.details_layout.addStretch()
    
    def clear_customer_details(self):
        """Clear customer details display"""
        while self.details_layout.count():
            item = self.details_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        initial_label = QLabel("Click the arrow (▶) next to a customer to view/edit details")
        initial_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        initial_label.setStyleSheet("font-size: 14px; color: #6c757d; padding: 50px;")
        self.details_layout.addWidget(initial_label)
    
    def update_customer_invoice_no(self, customer_id, invoice_no):
        """Update invoice number"""
        if customer_id in self.selected_customers:
            self.selected_customers[customer_id]['invoice_no'] = invoice_no
    
    def update_customer_eway_doc(self, customer_id, eway_doc):
        """Update E-way document number"""
        if customer_id in self.selected_customers:
            self.selected_customers[customer_id]['e_way_doc_no'] = eway_doc
    
    def update_customer_place_of_supply(self, customer_id, place_of_supply):
        """Update place of supply"""
        if customer_id in self.selected_customers:
            self.selected_customers[customer_id]['place_of_supply'] = place_of_supply
    
    def update_customer_gstin_unique_id(self, customer_id, gstin_unique_id):
        """Update GSTIN/Unique ID"""
        if customer_id in self.selected_customers:
            self.selected_customers[customer_id]['gstin_unique_id'] = gstin_unique_id
    
    def update_customer_blaster_name(self, customer_id, blaster_name):
        """Update blaster name"""
        if customer_id in self.selected_customers:
            customer_data = self.selected_customers[customer_id]
            if 'blaster_data' not in customer_data:
                customer_data['blaster_data'] = {}
            customer_data['blaster_data']['blaster_name'] = blaster_name
    
    def update_customer_blaster_doc(self, customer_id, blaster_doc):
        """Update blaster document number"""
        if customer_id in self.selected_customers:
            customer_data = self.selected_customers[customer_id]
            if 'blaster_data' not in customer_data:
                customer_data['blaster_data'] = {}
            customer_data['blaster_data']['blaster_document_no'] = blaster_doc
    
    def update_customer_blaster_address(self, customer_id, blaster_address):
        """Update blaster address"""
        if customer_id in self.selected_customers:
            customer_data = self.selected_customers[customer_id]
            if 'blaster_data' not in customer_data:
                customer_data['blaster_data'] = {}
            customer_data['blaster_data']['blaster_address'] = blaster_address
    
    def update_customer_freight_charges(self, customer_id, freight_charges):
        """Update freight charges"""
        if customer_id in self.selected_customers:
            try:
                value = float(freight_charges) if freight_charges else 0.0
                self.selected_customers[customer_id]['freight_charges'] = value
            except ValueError:
                # If invalid input, keep previous value or set to 0
                pass
    
    def add_blaster_from_details(self, customer_id, blaster_combo):
        """Add a new blaster from customer details section"""
        from dialogs_modern import AddBlasterDialog
        dialog = AddBlasterDialog(self, self.db)
        result = dialog.exec_() if PYQT_VERSION == 5 else dialog.exec()
        if result == DIALOG_ACCEPTED:
            # Refresh blaster combo
            blaster_combo.clear()
            blaster_combo.addItem("-- No Blaster --", None)
            blasters = self.db.get_blasters()
            current_blaster_id = None
            if customer_id in self.selected_customers:
                current_blaster_id = self.selected_customers[customer_id].get('blaster_id')
            
            for blaster in blasters:
                blaster_combo.addItem(blaster['name'], blaster['id'])
                if blaster['id'] == current_blaster_id:
                    blaster_combo.setCurrentIndex(blaster_combo.count() - 1)
            
            # Select the newly added blaster
            new_blaster = blasters[-1]  # Last added
            index = blaster_combo.findData(new_blaster['id'])
            if index >= 0:
                blaster_combo.setCurrentIndex(index)
    
    def manage_blasters_from_details(self, customer_id, blaster_combo):
        """Manage blasters from customer details section"""
        self.manage_blasters()
        # Refresh blaster combo after management
        blaster_combo.clear()
        blaster_combo.addItem("-- No Blaster --", None)
        blasters = self.db.get_blasters()
        current_blaster_id = None
        if customer_id in self.selected_customers:
            current_blaster_id = self.selected_customers[customer_id].get('blaster_id')
        
        for blaster in blasters:
            blaster_combo.addItem(blaster['name'], blaster['id'])
            if blaster['id'] == current_blaster_id:
                blaster_combo.setCurrentIndex(blaster_combo.count() - 1)
    
    def increment_customer_invoice(self, customer_id, invoice_edit):
        """Increment invoice number for a customer"""
        current_value = invoice_edit.text().strip()
        incremented = self.auto_increment_number(current_value, 1)
        invoice_edit.setText(incremented)
        # Update in selected_customers
        if customer_id in self.selected_customers:
            self.selected_customers[customer_id]['invoice_no'] = incremented
    
    def increment_customer_eway(self, customer_id, eway_edit):
        """Increment E-Way document number for a customer"""
        current_value = eway_edit.text().strip()
        incremented = self.auto_increment_number(current_value, 1)
        eway_edit.setText(incremented)
        # Update in selected_customers
        if customer_id in self.selected_customers:
            self.selected_customers[customer_id]['e_way_doc_no'] = incremented
    
    def refresh_customer_items(self, customer_id):
        """Refresh items table for customer"""
        if customer_id not in self.selected_customers:
            return
        
        customer_data = self.selected_customers[customer_id]
        if 'items_table' not in customer_data:
            return
        
        table = customer_data['items_table']
        items = customer_data['items']
        
        # Set row count: 1 for header + number of items
        table.setRowCount(1 + len(items))
        
        # Recreate header row (row 0)
        header_labels = ["Description", "HSN", "Qty", "Rate", "Total", "Actions"]
        for col, label in enumerate(header_labels):
            header_item = QTableWidgetItem(label)
            header_item.setBackground(QColor("#d9d9d9"))
            header_item.setForeground(QColor("#000000"))
            if PYQT_VERSION == 5:
                from PyQt5.QtGui import QFont
            else:
                from PyQt6.QtGui import QFont
            font = QFont()
            font.setBold(True)
            font.setPointSize(10)
            header_item.setFont(font)
            header_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            try:
                header_item.setFlags(header_item.flags() & ~Qt.ItemFlag.ItemIsSelectable & ~Qt.ItemFlag.ItemIsEditable)
            except:
                header_item.setFlags(header_item.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEditable)
            table.setItem(0, col, header_item)
        
        table.setRowHeight(0, 32)
        
        # Add data rows starting from row 1
        for idx, item in enumerate(items):
            row = idx + 1  # Row 0 is header, data starts at row 1
            
            # Data columns
            desc_item = QTableWidgetItem(item.get('description', ''))
            table.setItem(row, 0, desc_item)
            
            hsn_item = QTableWidgetItem(item.get('hsn_code', ''))
            hsn_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 1, hsn_item)
            
            qty_item = QTableWidgetItem(str(item.get('qty', 0)))
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 2, qty_item)
            
            rate_item = QTableWidgetItem(f"₹{item.get('rate', 0):.2f}")
            rate_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 3, rate_item)
            
            total_item = QTableWidgetItem(f"₹{item.get('total_amount', 0):.2f}")
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 4, total_item)
            
            # Actions column with compact Edit and Delete buttons
            action_widget = QWidget()
            action_widget.setStyleSheet("background-color: transparent;")
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(1, 0, 1, 0)
            action_layout.setSpacing(5)
            
            # Edit button
            edit_btn = QPushButton("Edit")
            edit_btn.setFixedSize(45, 22)
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4472c4;
                    color: white;
                    border: none;
                    border-radius: 2px;
                    font-size: 9px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2f5597;
                }
            """)
            edit_btn.clicked.connect(lambda checked, i=idx: self.edit_customer_item(customer_id, i))
            action_layout.addWidget(edit_btn)
            
            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.setFixedSize(50, 22)
            delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #c65911;
                    color: white;
                    border: none;
                    border-radius: 2px;
                    font-size: 9px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #a04a0d;
                }
            """)
            delete_btn.clicked.connect(lambda checked, i=idx: self.delete_customer_item(customer_id, i))
            action_layout.addWidget(delete_btn)
            
            action_layout.addStretch()
            table.setCellWidget(row, 5, action_widget)
            
            # Set consistent row height for data rows
            table.setRowHeight(row, 32)
    
    def add_good_to_customer(self, customer_id):
        """Add good to customer"""
        if customer_id not in self.selected_customers:
            return
        
        if not self.current_category:
            QMessageBox.warning(self, "Warning", "Please select a category (Detonator or Explosives) first")
            return
        
        dialog = AddGoodDialog(self, self.db, self.default_cgst_rate, self.default_sgst_rate, 
                              category=self.current_category)
        result = dialog.exec_() if PYQT_VERSION == 5 else dialog.exec()
        if result == DIALOG_ACCEPTED and dialog.item_data:
            self.selected_customers[customer_id]['items'].append(dialog.item_data)
            self.refresh_customer_items(customer_id)
            # Refresh the details view if this customer is expanded
            if self.expanded_customer_id == customer_id:
                self.show_customer_details(customer_id)
    
    def delete_customer_item(self, customer_id, row):
        """Delete item from customer"""
        if customer_id in self.selected_customers:
            items = self.selected_customers[customer_id]['items']
            if 0 <= row < len(items):
                item = items[row]
                # Show confirmation dialog
                item_description = item.get('description', 'this item')
                reply = QMessageBox.question(
                    self, "Confirm Delete",
                    f"Are you sure you want to delete '{item_description}' from this customer?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    items.pop(row)
                    self.refresh_customer_items(customer_id)
    
    def edit_customer_item(self, customer_id, row):
        """Edit an existing item for a customer (change quantity, recalc totals)"""
        if customer_id not in self.selected_customers:
            return
        
        items = self.selected_customers[customer_id]['items']
        if not (0 <= row < len(items)):
            return
        
        item = items[row]
        current_qty = float(item.get('qty', 0) or 0)
        if current_qty <= 0:
            current_qty = 1.0
        
        # Ask for new quantity using a simple dialog
        qty, ok = QInputDialog.getDouble(
            self,
            "Edit Quantity",
            f"Enter new quantity for {item.get('description', '')}:",
            current_qty,
            0.01,
            999999,
            2
        )
        if not ok:
            return
        
        # Recalculate totals with same rate and tax rates
        rate = float(item.get('rate', 0) or 0)
        total = qty * rate
        taxable_value = total
        cgst_rate = float(item.get('cgst_rate', self.default_cgst_rate))
        sgst_rate = float(item.get('sgst_rate', self.default_sgst_rate))
        cgst_rs = (taxable_value * cgst_rate) / 100
        sgst_rs = (taxable_value * sgst_rate) / 100
        total_amount = total + cgst_rs + sgst_rs
        
        item.update({
            'qty': qty,
            'rate': rate,
            'total': total,
            'taxable_value': taxable_value,
            'cgst_rate': cgst_rate,
            'cgst_rs': cgst_rs,
            'sgst_rate': sgst_rate,
            'sgst_rs': sgst_rs,
            'total_amount': total_amount,
        })
        
        self.refresh_customer_items(customer_id)
    
    def add_area(self):
        """Add new area"""
        dialog = AddAreaDialog(self, self.db)
        result = dialog.exec_() if PYQT_VERSION == 5 else dialog.exec()
        if result == DIALOG_ACCEPTED:
            self.refresh_areas()
            # Select the newly added area
            areas = self.db.get_locations()
            new_area = areas[-1]  # Last added
            index = self.area_combo.findData(new_area['id'])
            if index >= 0:
                self.area_combo.setCurrentIndex(index)
    
    def manage_areas(self):
        """Manage areas (add, rename, delete)"""
        def add_fn():
            dialog = AddAreaDialog(self, self.db)
            result = dialog.exec_() if PYQT_VERSION == 5 else dialog.exec()
            if result == DIALOG_ACCEPTED:
                self.refresh_areas()
                return True
            return False
        
        def edit_fn(area):
            current_name = area.get('name', '').upper()
            new_name, ok = QInputDialog.getText(self, "Rename Area", "Area name:", text=current_name)
            if ok and new_name.strip():
                try:
                    # update_location will convert to uppercase automatically
                    self.db.update_location(area['id'], new_name.strip())
                    self.refresh_areas()
                    return True
                except Exception as e:
                    QMessageBox.warning(self, "Error", str(e))
            return False
        
        def delete_fn(area):
            reply = QMessageBox.question(
                self, "Delete Area",
                f"Delete area '{area.get('name', '')}'? This will remove the area reference from customers.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.db.delete_location(area['id'])
                self.refresh_areas()
                self.refresh_customer_list()
                return True
            return False
        
        self._open_simple_manager(
            "Manage Areas",
            self.db.get_locations,
            add_fn,
            edit_fn,
            delete_fn,
            "name"
        )
    
    def add_vehicle(self):
        """Add new vehicle"""
        dialog = AddVehicleDialog(self, self.db)
        result = dialog.exec_() if PYQT_VERSION == 5 else dialog.exec()
        if result == DIALOG_ACCEPTED:
            self.refresh_vehicles()
            # Select the newly added vehicle
            vehicles = self.db.get_vehicles()
            new_vehicle = vehicles[-1]
            index = self.vehicle_combo.findText(new_vehicle['vehicle_number'])
            if index >= 0:
                self.vehicle_combo.setCurrentIndex(index)
            else:
                # If not found, refresh and try again
                self.refresh_vehicles()
                index = self.vehicle_combo.findText(new_vehicle['vehicle_number'])
                if index >= 0:
                    self.vehicle_combo.setCurrentIndex(index)
    
    def manage_vehicles(self):
        """Manage vehicles (add, rename, delete)"""
        def add_fn():
            dialog = AddVehicleDialog(self, self.db)
            result = dialog.exec_() if PYQT_VERSION == 5 else dialog.exec()
            if result == DIALOG_ACCEPTED:
                self.refresh_vehicles()
                return True
            return False
        
        def edit_fn(vehicle):
            new_no, ok = QInputDialog.getText(self, "Rename Vehicle", "Vehicle number:", text=vehicle.get('vehicle_number', ''))
            if ok and new_no.strip():
                try:
                    # Convert to uppercase
                    self.db.update_vehicle(vehicle['id'], new_no.strip().upper())
                    self.refresh_vehicles()
                    return True
                except Exception as e:
                    QMessageBox.warning(self, "Error", str(e))
            return False
        
        def delete_fn(vehicle):
            reply = QMessageBox.question(
                self, "Delete Vehicle",
                f"Delete vehicle '{vehicle.get('vehicle_number', '')}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.db.delete_vehicle(vehicle['id'])
                self.refresh_vehicles()
                return True
            return False
        
        self._open_simple_manager(
            "Manage Vehicles",
            self.db.get_vehicles,
            add_fn,
            edit_fn,
            delete_fn,
            "vehicle_number"
        )
    
    def manage_units(self):
        """Manage units (add, rename, delete)"""
        def add_fn():
            dialog = AddUnitDialog(self, self.db)
            result = dialog.exec_() if PYQT_VERSION == 5 else dialog.exec()
            if result == DIALOG_ACCEPTED:
                return True
            return False
        
        def edit_fn(unit):
            current_name = unit.get('name', '').upper()
            new_name, ok = QInputDialog.getText(self, "Rename Unit", "Unit name:", text=current_name)
            if ok and new_name.strip():
                try:
                    self.db.update_unit(unit['id'], new_name.strip())
                    return True
                except Exception as e:
                    QMessageBox.warning(self, "Error", str(e))
            return False
        
        def delete_fn(unit):
            reply = QMessageBox.question(
                self, "Delete Unit",
                f"Delete unit '{unit.get('name', '')}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.db.delete_unit(unit['id'])
                    return True
                except Exception as e:
                    QMessageBox.warning(self, "Error", str(e))
            return False
        
        self._open_simple_manager(
            "Manage Units",
            self.db.get_units,
            add_fn,
            edit_fn,
            delete_fn,
            "name"
        )
    
    def on_vehicle_activated(self, index):
        """Handle special commands from vehicle dropdown"""
        data = self.vehicle_combo.itemData(index, Qt.ItemDataRole.UserRole)
        if isinstance(data, str) and data.startswith("__cmd_vehicle_"):
            if data == "__cmd_vehicle_add":
                self.add_vehicle()
            elif data == "__cmd_vehicle_manage":
                self.manage_vehicles()
            if hasattr(self, "_last_vehicle_index") and self._last_vehicle_index is not None:
                self.vehicle_combo.setCurrentIndex(self._last_vehicle_index)
            else:
                self.vehicle_combo.setCurrentIndex(0)
            return
        self._last_vehicle_index = index
    
    def add_customer(self):
        """Add new customer"""
        if not self.current_category:
            QMessageBox.warning(self, "Category Required", "Please select a Category first.")
            return
        if not self.current_area_id:
            QMessageBox.warning(self, "Warning", "Please select an area first")
            return
        
        dialog = AddCustomerDialog(self, self.db, area_id=self.current_area_id)
        result = dialog.exec_() if PYQT_VERSION == 5 else dialog.exec()
        if result == DIALOG_ACCEPTED:
            self.refresh_customer_list()
    
    def edit_selected_customer(self):
        """Edit selected customer"""
        if not self.current_area_id:
            QMessageBox.warning(self, "Warning", "Please select an area first")
            return
        
        customers = self.db.get_customers(location_id=self.current_area_id)
        if not customers:
            QMessageBox.warning(self, "Warning", "No customers to edit for this area")
            return
        
        # Show selection dialog
        select_dialog = SelectCustomerDialog(self, customers)
        result1 = select_dialog.exec_() if PYQT_VERSION == 5 else select_dialog.exec()
        if result1 == DIALOG_ACCEPTED:
            customer = select_dialog.selected_customer
            if customer:
                edit_dialog = AddCustomerDialog(self, self.db, customer=customer, area_id=self.current_area_id)
                result2 = edit_dialog.exec_() if PYQT_VERSION == 5 else edit_dialog.exec()
                if result2 == DIALOG_ACCEPTED:
                    self.refresh_customer_list()
                    # Refresh if this customer is expanded
                    if self.expanded_customer_id == customer['id']:
                        self.show_customer_details(customer['id'])
    
    def edit_customer_from_details(self, customer_id):
        """Edit customer from details view"""
        customer = self.db.get_customer(customer_id)
        if not customer:
            return
        
        dialog = AddCustomerDialog(self, self.db, customer=customer, area_id=self.current_area_id)
        result = dialog.exec_() if PYQT_VERSION == 5 else dialog.exec()
        if result == DIALOG_ACCEPTED:
            # Refresh customer data
            updated_customer = self.db.get_customer(customer_id)
            if updated_customer:
                if customer_id in self.selected_customers:
                    self.selected_customers[customer_id]['customer'] = updated_customer
                self.refresh_customer_list()
                if self.expanded_customer_id == customer_id:
                    self.show_customer_details(customer_id)
    
    def manage_customers(self):
        """Manage customers for the selected area"""
        if not self.current_area_id:
            QMessageBox.warning(self, "Warning", "Please select an area first")
            return
        
        def add_fn():
            self.add_customer()
            return True
        
        def edit_fn(customer):
            full = self.db.get_customer(customer['id'])
            if not full:
                QMessageBox.warning(self, "Error", "Customer not found")
                return False
            dialog = AddCustomerDialog(self, self.db, customer=full, area_id=self.current_area_id)
            result = dialog.exec_() if PYQT_VERSION == 5 else dialog.exec()
            if result == DIALOG_ACCEPTED:
                self.refresh_customer_list()
                if self.expanded_customer_id == customer['id']:
                    self.show_customer_details(customer['id'])
                return True
            return False
        
        def delete_fn(customer):
            reply = QMessageBox.question(
                self, "Delete Customer",
                f"Delete customer '{customer.get('name', '').upper() if customer.get('name') else ''}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.db.delete_customer(customer['id'])
                self.refresh_customer_list()
                return True
            return False
        
        self._open_simple_manager(
            "Manage Customers",
            lambda: self.db.get_customers(location_id=self.current_area_id),
            add_fn,
            edit_fn,
            delete_fn,
            "name"
        )

    def manage_blasters(self):
        """Manage blasters"""
        def add_fn():
            dialog = AddBlasterDialog(self, self.db)
            result = dialog.exec_() if PYQT_VERSION == 5 else dialog.exec()
            return result == DIALOG_ACCEPTED
        
        def edit_fn(blaster):
            editor = QDialog(self)
            editor.setWindowTitle("Edit Blaster")
            layout = QVBoxLayout(editor)
            
            name_row = QHBoxLayout()
            name_row.addWidget(QLabel("Name *:"))
            name_edit = QLineEdit()
            name_edit.setText(blaster.get('name', ''))
            # Convert to uppercase as user types
            name_edit.textChanged.connect(lambda text: name_edit.setText(text.upper()))
            name_row.addWidget(name_edit)
            layout.addLayout(name_row)
            
            doc_row = QHBoxLayout()
            doc_row.addWidget(QLabel("Document No:"))
            doc_edit = QLineEdit()
            doc_edit.setText(blaster.get('document_no', ''))
            # Convert to uppercase as user types
            doc_edit.textChanged.connect(lambda text: doc_edit.setText(text.upper()))
            doc_row.addWidget(doc_edit)
            layout.addLayout(doc_row)
            
            address_row = QVBoxLayout()
            address_row.addWidget(QLabel("Address:"))
            address_edit = QTextEdit()
            address_edit.setMaximumHeight(80)
            address_edit.setPlainText(blaster.get('address', ''))
            # Convert to uppercase as user types
            def make_address_upper():
                current_text = address_edit.toPlainText()
                cursor = address_edit.textCursor()
                cursor_pos = cursor.position()
                upper_text = current_text.upper()
                if current_text != upper_text:
                    address_edit.setPlainText(upper_text)
                    # Restore cursor position
                    cursor.setPosition(min(cursor_pos, len(upper_text)))
                    address_edit.setTextCursor(cursor)
            address_edit.textChanged.connect(make_address_upper)
            address_row.addWidget(address_edit)
            layout.addLayout(address_row)
            
            btn_row = QHBoxLayout()
            btn_save = ModernButton("Save", primary=True)
            btn_cancel = ModernButton("Cancel", primary=False)
            btn_row.addStretch()
            btn_row.addWidget(btn_cancel)
            btn_row.addWidget(btn_save)
            layout.addLayout(btn_row)
            
            saved = {"ok": False}
            def save():
                name = name_edit.text().strip()
                if not name:
                    QMessageBox.warning(editor, "Error", "Name is required")
                    return
                self.db.update_blaster(
                    blaster['id'],
                    name,
                    doc_edit.text().strip(),
                    address_edit.toPlainText().strip()
                )
                saved["ok"] = True
                editor.accept()
            btn_save.clicked.connect(save)
            btn_cancel.clicked.connect(editor.reject)
            
            editor.exec_() if PYQT_VERSION == 5 else editor.exec()
            return saved["ok"]
        
        def delete_fn(blaster):
            reply = QMessageBox.question(
                self, "Delete Blaster",
                f"Delete blaster '{blaster.get('name', '')}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.db.delete_blaster(blaster['id'])
                return True
            return False
        
        self._open_simple_manager(
            "Manage Blasters",
            self.db.get_blasters,
            add_fn,
            edit_fn,
            delete_fn,
            "name"
        )
    
    def manage_goods(self):
        """Manage goods"""
        from goods_manager_modern import GoodsManagerDialog
        dialog = GoodsManagerDialog(self, self.db)
        result = dialog.exec_() if PYQT_VERSION == 5 else dialog.exec()
        if result == DIALOG_ACCEPTED:
            # Refresh if needed
            pass
    
    def generate_pdfs(self):
        """Generate PDFs for selected customers"""
        if not self.current_category:
            QMessageBox.warning(self, "Category Required", "Please select a Category first.")
            return
        
        if not self.selected_customers:
            QMessageBox.warning(self, "Warning", "Please select at least one customer")
            return
        
        if not self.current_area_id:
            QMessageBox.warning(self, "Warning", "Please select an area")
            return
        
        vehicle_text = self.vehicle_combo.currentText()
        if not vehicle_text or vehicle_text == "-- Select Vehicle --":
            QMessageBox.warning(self, "Warning", "Please select a vehicle")
            return
        
        # Validate invoice numbers are entered for all customers
        missing_invoices = []
        for customer_id, customer_data in self.selected_customers.items():
            invoice_no = customer_data.get('invoice_no', '').strip()
            if not invoice_no:
                customer_name = customer_data['customer'].get('name', 'Unknown')
                missing_invoices.append(customer_name.upper() if customer_name else 'Unknown')
        
        if missing_invoices:
            QMessageBox.warning(self, "Warning", 
                f"Invoice number is required for:\n" + "\n".join(missing_invoices))
            return
        
        # Get date of supply
        if PYQT_VERSION == 6:
            date_of_supply = self.date_edit.date().toString("dd-MM-yyyy")
        else:
            date_of_supply = self.date_edit.date().toString("dd-MM-yyyy")
        vehicle_number = self.vehicle_combo.currentText()
        mode_of_transport = "Road"  # Default
        e_way_bill_no = self.eway_bill_edit.text().strip()  # Get from configuration input
        
        # Ask for save file path (single PDF file)
        # Format: <First 3 chars of category>_<First 3 chars of area>_<date>.pdf
        category_prefix = ""
        if self.current_category:
            category_str = str(self.current_category).upper()
            category_prefix = category_str[:3] if len(category_str) >= 3 else category_str.ljust(3, 'X')
        else:
            category_prefix = "XXX"
        
        area_prefix = ""
        if self.current_area_name:
            area_str = str(self.current_area_name).upper()
            area_prefix = area_str[:3] if len(area_str) >= 3 else area_str.ljust(3, 'X')
        else:
            area_prefix = "XXX"
        
        date_str = date_of_supply.replace('-', '_')
        default_filename = f"{category_prefix}_{area_prefix}_{date_str}.pdf"
        
        # Get last saved directory from settings
        last_dir = self.settings.value("last_pdf_save_dir", "")
        if last_dir and os.path.exists(last_dir):
            # Use last directory + default filename
            default_path = os.path.join(last_dir, default_filename)
        else:
            # Use just the filename (will open in default location)
            default_path = default_filename
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, 
            "Save PDF File", 
            default_path,
            "PDF Files (*.pdf)"
        )
        if not filepath:
            return
        
        # Save the directory for next time
        save_dir = os.path.dirname(filepath)
        if save_dir:
            self.settings.setValue("last_pdf_save_dir", save_dir)
        
        # Prepare invoice data for all customers
        invoice_data_list = []
        
        for customer_id, customer_data in self.selected_customers.items():
            try:
                # Prepare invoice data
                customer = customer_data['customer']
                items = customer_data.get('items', [])  # Allow empty items list
                
                # Calculate totals (handle empty items)
                total_items = sum(item.get('total_amount', 0) for item in items) if items else 0
                freight = customer_data.get('freight_charges', 0)
                grand_total = total_items + freight
                rounded_total = self._round_total(grand_total)
                total_in_words = number_to_words(rounded_total) if rounded_total > 0 else 'Zero'
                
                # Get blaster info - check customer_data first (editable), then customer (from DB)
                blaster_data = customer_data.get('blaster_data', {})
                blaster_name = blaster_data.get('blaster_name') or customer.get('blaster_name', '')
                blaster_doc = blaster_data.get('blaster_document_no') or customer.get('blaster_document_no', '')
                blaster_address = blaster_data.get('blaster_address') or customer.get('blaster_address', '')
                
                # Ensure all required fields have default values
                invoice_data = {
                    'invoice_number': customer_data.get('invoice_no', ''),
                    'date_of_supply': date_of_supply,
                    'category': self.current_category or '',
                    'location_name': self.current_area_name or '',
                    'vehicle_number': vehicle_number or '',
                    'customer': customer or {},
                    'mode_of_transport': mode_of_transport,
                    'is_original': self.original_checkbox.isChecked(),
                    'is_duplicate': self.duplicate_checkbox.isChecked(),
                    'is_triplicate': self.triplicate_checkbox.isChecked(),
                    'e_way_bill_no': e_way_bill_no,
                    'e_way_document_no': customer_data.get('e_way_doc_no', ''),
                    'place_of_supply': customer_data.get('place_of_supply', '') or customer.get('address', ''),
                    'state_code': '33',
                    'gstin_unique_id': customer_data.get('gstin_unique_id', ''),
                    'items': items or [],
                    'freight_charges': float(freight) if freight else 0.0,
                    'grand_total': float(rounded_total),
                    'total_in_words': total_in_words or '',
                    'blaster_name': blaster_name or '',
                    'document_no': blaster_doc or '',
                    'blaster_address': blaster_address or ''
                }
                
                invoice_data_list.append(invoice_data)
                
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                error_msg = f"Failed to prepare data for {customer_data['customer']['name']}\n\nError: {str(e)}\n\nDetails:\n{error_details}"
                QMessageBox.critical(self, "Data Preparation Error", error_msg)
                print(f"Data Preparation Error: {error_details}")
                return
        
        # Generate single multi-page PDF
        try:
            self.pdf_gen.generate_multi_page_pdf(invoice_data_list, filepath)
            success_count = len(invoice_data_list)
            error_count = 0
            
            # Show success message
            QMessageBox.information(self, "Success", 
                f"Successfully generated PDF with {success_count} page(s)\n\nSaved to:\n{filepath}")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            error_msg = f"Failed to generate PDF\n\nError: {str(e)}\n\nDetails:\n{error_details}"
            QMessageBox.critical(self, "PDF Generation Error", error_msg)
            print(f"PDF Generation Error: {error_details}")
    
    def _round_total(self, amount):
        """Round to nearest integer"""
        return math.floor(amount) if (amount - math.floor(amount)) < 0.5 else math.ceil(amount)
    
    def clear_form(self):
        """Clear form"""
        reply = QMessageBox.question(
            self, "Confirm", "Are you sure you want to clear the form?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Clear category selection
            self.category_combo.setCurrentIndex(0)  # Reset to placeholder
            self.current_category = None
            
            # Clear area selection
            self.area_combo.setCurrentIndex(0)  # Reset to placeholder
            self.current_area_id = None
            self.current_area_name = None
            
            # Clear vehicle selection
            self.vehicle_combo.setCurrentIndex(0)  # Reset to placeholder
            
            # Reset date to today
            self.date_edit.setDate(QDate.currentDate())
            
            # Clear E-Way Bill Number
            self.eway_bill_edit.clear()
            
            # Clear invoice number fields (handled in customer details now)
            
            # Reset checkboxes to default (Original checked)
            self.original_checkbox.setChecked(True)
            self.duplicate_checkbox.setChecked(False)
            self.triplicate_checkbox.setChecked(False)
            
            # Clear selected customers
            self.selected_customers = {}
            self.expanded_customer_id = None
            
            # Refresh displays
            self.refresh_customer_list()
            self.clear_customer_details()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern style
    
    # Set application icon (for taskbar)
    import os
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        script_dir = sys._MEIPASS
    else:
        # Running as script
        script_dir = os.path.dirname(os.path.abspath(__file__))
    
    logo_path = os.path.join(script_dir, "logo.png")
    if os.path.exists(logo_path):
        app_icon = QIcon(logo_path)
        app.setWindowIcon(app_icon)
    
    # Set application palette for professional look
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(245, 246, 250))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(33, 37, 41))
    app.setPalette(palette)
    
    # Show main window directly (no license check)
    window = BatchProcessingWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

