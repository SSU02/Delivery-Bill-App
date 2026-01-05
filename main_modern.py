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
        QAbstractItemView, QStackedWidget
    )
    from PyQt5.QtCore import Qt, QDate, QSize, pyqtSignal
    from PyQt5.QtGui import QFont, QIcon, QColor, QPalette
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
        QAbstractItemView, QStackedWidget
    )
    from PyQt6.QtCore import Qt, QDate, QSize, pyqtSignal
    from PyQt6.QtGui import QFont, QIcon, QColor, QPalette
    PYQT_VERSION = 6
    DIALOG_ACCEPTED = QDialog.DialogCode.Accepted
from datetime import datetime
from database import Database
from pdf_generator import PDFGenerator
from number_to_words import number_to_words
from dialogs_modern import (
    AddAreaDialog, AddVehicleDialog, AddCustomerDialog,
    AddGoodDialog, AddBlasterDialog, NewGoodDialog, SelectCustomerDialog
)
import re
import math


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
        title = QLabel("Delivery Bill\nGenerator")
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
    
    def __init__(self, customer_id, customer_name, is_selected=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.customer_id = customer_id
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
            }
            QWidget:hover {
                background-color: #f8f9fa;
                border: 1px solid #007bff;
            }
            QCheckBox {
                font-size: 13px;
                color: #212529;
                background-color: transparent;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #ced4da;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #007bff;
                border-color: #007bff;
            }
            QLabel {
                font-size: 13px;
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
        layout.setContentsMargins(15, 12, 15, 12)  # Increased margins for broader appearance
        layout.setSpacing(12)  # Increased spacing between elements
        
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(is_selected)
        layout.addWidget(self.checkbox)
        
        self.name_label = QLabel(customer_name)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 14px;")  # Slightly larger font
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
    
    def set_expanded(self, expanded):
        self.expand_btn.setText("▼" if expanded else "▶")


class BatchProcessingWindow(QMainWindow):
    """Main window for batch processing with modern UI"""
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.pdf_gen = PDFGenerator()
        
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
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Delivery Bill Generator - Professional Edition")
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
                width: 18px;
                height: 18px;
                border: 2px solid #ced4da;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #007bff;
                border-color: #007bff;
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
        left_config_layout.setSpacing(20)  # More space between rows
        
        # Row 1: Category and Area - CLEAR AND VISIBLE
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(20)
        row1_layout.setContentsMargins(0, 0, 0, 0)
        
        # Category - Larger and clearer
        category_label = QLabel("Category:")
        category_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #212529; min-width: 80px; padding: 2px 0px;")
        category_label.setMinimumHeight(45)
        category_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.category_detonator = QCheckBox("Detonator")
        self.category_explosives = QCheckBox("Explosives")
        self.category_detonator.setStyleSheet("font-size: 14px; padding: 5px;")
        self.category_explosives.setStyleSheet("font-size: 14px; padding: 5px;")
        self.category_detonator.setMinimumHeight(45)
        self.category_explosives.setMinimumHeight(45)
        self.category_detonator.toggled.connect(self.on_category_changed)
        self.category_explosives.toggled.connect(self.on_category_changed)
        row1_layout.addWidget(category_label)
        row1_layout.addWidget(self.category_detonator)
        row1_layout.addWidget(self.category_explosives)
        
        # Fixed spacing to align Area with Vehicle - Date section takes same space as Category section
        # Category: 80px (label) + checkboxes (~200px) = ~280px
        # Date: 60px (label) + 200px (field) = ~260px
        # So we need ~20px more spacing before Area to match Date position
        row1_layout.addSpacing(40)  # Fixed spacing to align with Date position
        
        # Area - Larger and clearer
        area_label = QLabel("Area:")
        area_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #212529; min-width: 60px; padding: 2px 0px;")
        area_label.setMinimumHeight(45)
        area_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.area_combo = QComboBox()
        self.area_combo.setMinimumWidth(250)
        self.area_combo.setMinimumHeight(45)
        self.area_combo.setEditable(False)
        self.area_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 2px solid #ced4da;
                border-radius: 5px;
                background-color: white;
                font-size: 14px;
                color: #212529;
            }
            QComboBox:focus {
                border: 2px solid #007bff;
                background-color: white;
            }
            QComboBox::drop-down {
                border: none;
                width: 35px;
                background-color: transparent;
            }
            QComboBox::drop-down:hover {
                background-color: transparent;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #ced4da;
                selection-background-color: #007bff;
                font-size: 14px;
            }
        """)
        self.area_combo.currentTextChanged.connect(self.on_area_changed)
        area_btn_add = ModernButton("+ Add", primary=False)
        area_btn_add.setMinimumHeight(45)
        area_btn_add.setMinimumWidth(90)
        area_btn_manage = ModernButton("Manage", primary=False)
        area_btn_manage.setMinimumHeight(45)
        area_btn_manage.setMinimumWidth(100)
        area_btn_add.clicked.connect(self.add_area)
        area_btn_manage.clicked.connect(self.manage_areas)
        row1_layout.addWidget(area_label)
        row1_layout.addWidget(self.area_combo)
        row1_layout.addWidget(area_btn_add)
        row1_layout.addWidget(area_btn_manage)
        
        row1_layout.addStretch()
        left_config_layout.addLayout(row1_layout)
        
        # Row 2: Date and Vehicle - Vehicle aligned with Area column
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(20)
        row2_layout.setContentsMargins(0, 0, 0, 0)
        
        # Date - Large and visible
        date_label = QLabel("Date:")
        date_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #212529; min-width: 60px; padding: 2px 0px;")
        date_label.setMinimumHeight(45)
        date_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setMinimumWidth(200)
        self.date_edit.setMinimumHeight(45)
        self.date_edit.setStyleSheet("""
            QDateEdit {
                padding: 10px;
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
                border: none;
                width: 35px;
                background-color: transparent;
            }
            QDateEdit::drop-down:hover {
                background-color: transparent;
            }
        """)
        if PYQT_VERSION == 6:
            self.date_edit.setDisplayFormat("dd-MM-yyyy")
        else:
            self.date_edit.setDisplayFormat("dd/MM/yyyy")
        row2_layout.addWidget(date_label)
        row2_layout.addWidget(self.date_edit)
        
        # Same fixed spacing as Row 1 to align Vehicle with Area
        row2_layout.addSpacing(40)  # Same spacing as Row 1
        
        # Vehicle - Large and visible, aligned with Area
        vehicle_label = QLabel("Vehicle:")
        vehicle_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #212529; min-width: 60px; padding: 2px 0px;")
        vehicle_label.setMinimumHeight(45)
        vehicle_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.vehicle_combo = QComboBox()
        self.vehicle_combo.setMinimumWidth(250)  # Same width as area_combo
        self.vehicle_combo.setMinimumHeight(45)
        self.vehicle_combo.setEditable(False)
        self.vehicle_combo.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 2px solid #ced4da;
                border-radius: 5px;
                background-color: white;
                font-size: 14px;
                color: #212529;
            }
            QComboBox:focus {
                border: 2px solid #007bff;
                background-color: white;
            }
            QComboBox::drop-down {
                border: none;
                width: 35px;
                background-color: transparent;
            }
            QComboBox::drop-down:hover {
                background-color: transparent;
            }
            QComboBox QAbstractItemView {
                border: 2px solid #ced4da;
                selection-background-color: #007bff;
                font-size: 14px;
            }
        """)
        vehicle_btn_add = ModernButton("+ Add", primary=False)
        vehicle_btn_add.setMinimumHeight(45)
        vehicle_btn_add.setMinimumWidth(90)  # Same width as area_btn_add
        vehicle_btn_manage = ModernButton("Manage", primary=False)
        vehicle_btn_manage.setMinimumHeight(45)
        vehicle_btn_manage.setMinimumWidth(100)  # Same width as area_btn_manage
        vehicle_btn_add.clicked.connect(self.add_vehicle)
        vehicle_btn_manage.clicked.connect(self.manage_vehicles)
        row2_layout.addWidget(vehicle_label)
        row2_layout.addWidget(self.vehicle_combo)
        row2_layout.addWidget(vehicle_btn_add)
        row2_layout.addWidget(vehicle_btn_manage)
        
        row2_layout.addStretch()
        left_config_layout.addLayout(row2_layout)
        
        # Row 3: Original/Duplicate/Triplicate checkboxes
        row3_layout = QHBoxLayout()
        row3_layout.setSpacing(20)
        row3_layout.setContentsMargins(0, 0, 0, 0)
        
        checkbox_label = QLabel("Copy Type:")
        checkbox_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #212529; min-width: 80px; padding: 2px 0px;")
        checkbox_label.setMinimumHeight(45)
        checkbox_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        self.original_checkbox = QCheckBox("Original")
        self.duplicate_checkbox = QCheckBox("Duplicate")
        self.triplicate_checkbox = QCheckBox("Triplicate")
        self.original_checkbox.setStyleSheet("font-size: 14px; padding: 5px;")
        self.duplicate_checkbox.setStyleSheet("font-size: 14px; padding: 5px;")
        self.triplicate_checkbox.setStyleSheet("font-size: 14px; padding: 5px;")
        self.original_checkbox.setMinimumHeight(45)
        self.duplicate_checkbox.setMinimumHeight(45)
        self.triplicate_checkbox.setMinimumHeight(45)
        # Default to Original checked
        self.original_checkbox.setChecked(True)
        
        row3_layout.addWidget(checkbox_label)
        row3_layout.addWidget(self.original_checkbox)
        row3_layout.addWidget(self.duplicate_checkbox)
        row3_layout.addWidget(self.triplicate_checkbox)
        row3_layout.addStretch()
        left_config_layout.addLayout(row3_layout)
        
        config_splitter.addWidget(left_config_widget)
        config_splitter.setStretchFactor(0, 3)
        
        # Right side: Goods Management partition
        right_goods_widget = QWidget()
        right_goods_layout = QVBoxLayout(right_goods_widget)
        right_goods_layout.setContentsMargins(15, 10, 15, 10)  # Reduced padding
        right_goods_layout.setSpacing(15)  # Slightly increased spacing
        
        goods_label = QLabel("Goods Management")
        goods_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #212529; padding: 8px 0px; min-height: 30px;")
        goods_label.setMinimumHeight(30)  # Ensure enough height for text
        right_goods_layout.addWidget(goods_label)
        
        btn_manage_goods = ModernButton("Manage Goods", primary=True)
        btn_manage_goods.setMinimumHeight(45)  # Make button taller
        btn_manage_goods.setMinimumWidth(150)  # Make button wider
        btn_manage_goods.clicked.connect(self.manage_goods)
        right_goods_layout.addWidget(btn_manage_goods)
        
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
        customer_btn_add.clicked.connect(self.add_customer)
        customer_btn_edit.clicked.connect(self.edit_selected_customer)
        customer_btn_manage.clicked.connect(self.manage_customers)
        customer_btn_layout.addWidget(customer_btn_add)
        customer_btn_layout.addWidget(customer_btn_edit)
        customer_btn_layout.addWidget(customer_btn_manage)
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
        btn_clear = ModernButton("Clear Form", primary=False)
        btn_generate.clicked.connect(self.generate_pdfs)
        btn_clear.clicked.connect(self.clear_form)
        action_layout.addWidget(btn_generate)
        action_layout.addWidget(btn_clear)
        main_layout.addLayout(action_layout)
        
        # Load initial data (with placeholder selections)
        self.refresh_areas()
        self.area_combo.setCurrentIndex(0)  # Set to placeholder "-- Select Area --"
        self.refresh_vehicles()
        self.vehicle_combo.setCurrentIndex(0)  # Set to placeholder "-- Select Vehicle --"
        self.refresh_customer_list()
    
    def on_category_changed(self):
        """Handle category selection"""
        if self.category_detonator.isChecked():
            self.current_category = "Detonator"
        elif self.category_explosives.isChecked():
            self.current_category = "Explosives"
        else:
            self.current_category = None
        
        self.current_area_id = None
        self.area_combo.setCurrentIndex(-1)
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
        if self.area_combo.currentIndex() > 0:  # > 0 because 0 is placeholder
            self.current_area_id = self.area_combo.currentData()
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
            item_widget = CustomerItemWidget(customer_id, customer['name'], is_selected)
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
                
                self.selected_customers[customer_id] = {
                    'customer': customer,
                    'invoice_no': invoice_no,
                    'e_way_doc_no': eway_doc_no,
                    'items': [],
                    'place_of_supply': customer.get('address', '') or self.current_area_name or '',
                    'freight_charges': 0.0
                }
        else:
            if customer_id in self.selected_customers:
                del self.selected_customers[customer_id]
            if self.expanded_customer_id == customer_id:
                self.clear_customer_details()
                self.expanded_customer_id = None
    
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
        
        name_label = QLabel(customer['name'])
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
                value_label = QLabel(str(value))
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
            invoice_layout = QVBoxLayout()
            
            # Invoice No (Mandatory)
            invoice_row = QHBoxLayout()
            invoice_label = QLabel("Invoice No: *")
            invoice_label.setStyleSheet("font-weight: bold; color: #212529;")
            invoice_row.addWidget(invoice_label)
            invoice_edit = QLineEdit(customer_data.get('invoice_no', ''))
            invoice_edit.setPlaceholderText("Enter invoice number (required)")
            invoice_edit.textChanged.connect(
                lambda text: self.update_customer_invoice_no(customer_id, text)
            )
            invoice_row.addWidget(invoice_edit)
            # Auto-increment button
            btn_increment_invoice = ModernButton("+1", primary=False)
            btn_increment_invoice.setMaximumWidth(50)
            btn_increment_invoice.setToolTip("Auto-increment invoice number")
            btn_increment_invoice.clicked.connect(
                lambda: self.increment_customer_invoice(customer_id, invoice_edit)
            )
            invoice_row.addWidget(btn_increment_invoice)
            invoice_layout.addLayout(invoice_row)
            
            # E-Way Doc No
            eway_row = QHBoxLayout()
            eway_label = QLabel("E-Way Document No:")
            eway_row.addWidget(eway_label)
            eway_edit = QLineEdit(customer_data.get('e_way_doc_no', ''))
            eway_edit.setPlaceholderText("Enter E-Way document number")
            eway_edit.textChanged.connect(
                lambda text: self.update_customer_eway_doc(customer_id, text)
            )
            eway_row.addWidget(eway_edit)
            # Auto-increment button
            btn_increment_eway = ModernButton("+1", primary=False)
            btn_increment_eway.setMaximumWidth(50)
            btn_increment_eway.setToolTip("Auto-increment E-Way document number")
            btn_increment_eway.clicked.connect(
                lambda: self.increment_customer_eway(customer_id, eway_edit)
            )
            eway_row.addWidget(btn_increment_eway)
            invoice_layout.addLayout(eway_row)
            
            invoice_group.setLayout(invoice_layout)
            self.details_layout.addWidget(invoice_group)
            
            # Items section
            items_group = QGroupBox("Goods Selection")
            items_layout = QVBoxLayout()
            
            add_item_btn = ModernButton("+ Add Good", primary=True)
            add_item_btn.clicked.connect(lambda: self.add_good_to_customer(customer_id))
            items_layout.addWidget(add_item_btn)
            
            # Items table
            items_table = QTableWidget()
            items_table.setColumnCount(6)
            items_table.setHorizontalHeaderLabels([
                "Description", "HSN", "Qty", "Rate", "Total", "Actions"
            ])
            items_table.horizontalHeader().setStretchLastSection(True)
            items_table.setAlternatingRowColors(True)
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
        
        table.setRowCount(len(items))
        for row, item in enumerate(items):
            table.setItem(row, 0, QTableWidgetItem(item.get('description', '')))
            table.setItem(row, 1, QTableWidgetItem(item.get('hsn_code', '')))
            table.setItem(row, 2, QTableWidgetItem(str(item.get('qty', 0))))
            table.setItem(row, 3, QTableWidgetItem(f"{item.get('rate', 0):.2f}"))
            table.setItem(row, 4, QTableWidgetItem(f"{item.get('total_amount', 0):.2f}"))
            
            # Delete button
            delete_btn = ModernButton("Delete", primary=False)
            delete_btn.clicked.connect(lambda checked, r=row: self.delete_customer_item(customer_id, r))
            table.setCellWidget(row, 5, delete_btn)
    
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
                items.pop(row)
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
        """Manage areas"""
        QMessageBox.information(self, "Info", "Area management - to be implemented in future version")
    
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
        """Manage vehicles"""
        QMessageBox.information(self, "Info", "Vehicle management - to be implemented in future version")
    
    def add_customer(self):
        """Add new customer"""
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
        """Manage customers"""
        QMessageBox.information(self, "Info", "Customer management - to be implemented in future version")
    
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
        if not self.selected_customers:
            QMessageBox.warning(self, "Warning", "Please select at least one customer")
            return
        
        if not self.current_category:
            QMessageBox.warning(self, "Warning", "Please select a category")
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
                missing_invoices.append(customer_name)
        
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
        e_way_bill_no = "5019 3382 6386"  # Default
        
        # Ask for save file path (single PDF file)
        default_filename = f"Delivery_Bills_{date_of_supply.replace('-', '_')}.pdf"
        filepath, _ = QFileDialog.getSaveFileName(
            self, 
            "Save PDF File", 
            default_filename,
            "PDF Files (*.pdf)"
        )
        if not filepath:
            return
        
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
                
                # Get blaster info
                blaster_name = customer.get('blaster_name', '')
                blaster_doc = customer.get('blaster_document_no', '')
                blaster_address = customer.get('blaster_address', '')
                
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
                    'gstin_unique_id': customer.get('gstin', ''),
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
            self.category_detonator.setChecked(False)
            self.category_explosives.setChecked(False)
            self.current_category = None
            
            # Clear area selection
            self.area_combo.setCurrentIndex(0)  # Reset to placeholder
            self.current_area_id = None
            self.current_area_name = None
            
            # Clear vehicle selection
            self.vehicle_combo.setCurrentIndex(0)  # Reset to placeholder
            
            # Reset date to today
            self.date_edit.setDate(QDate.currentDate())
            
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
    
    # Set application palette for professional look
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(245, 246, 250))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(33, 37, 41))
    app.setPalette(palette)
    
    window = BatchProcessingWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

