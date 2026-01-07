"""
Modern Beautiful Calendar Widget for Delivery Bill App
A professionally designed calendar popup with clean aesthetics
"""
try:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QGridLayout, QWidget, QFrame, QComboBox
    )
    from PyQt5.QtCore import Qt, QDate, pyqtSignal
    from PyQt5.QtGui import QFont, QColor, QPalette
    PYQT_VERSION = 5
except ImportError:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QGridLayout, QWidget, QFrame, QComboBox
    )
    from PyQt6.QtCore import Qt, QDate, pyqtSignal
    from PyQt6.QtGui import QFont, QColor, QPalette
    PYQT_VERSION = 6

import calendar
from datetime import datetime


class ModernCalendar(QDialog):
    """Beautiful modern calendar popup"""
    date_selected = pyqtSignal(QDate)
    
    def __init__(self, initial_date=None, parent=None):
        super().__init__(parent)
        self.selected_date = initial_date if initial_date else QDate.currentDate()
        self.current_month = self.selected_date.month()
        self.current_year = self.selected_date.year()
        self.today = QDate.currentDate()
        
        self.setWindowTitle("Select Date")
        self.setModal(True)
        self.setFixedSize(380, 420)
        
        # Remove window frame for modern look
        self.setWindowFlags(Qt.WindowType.Popup if PYQT_VERSION == 6 else Qt.Popup)
        
        self.setup_ui()
        self.apply_styles()
        self.update_calendar()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Main container
        container = QFrame()
        container.setObjectName("calendarContainer")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(10)
        
        # Header with month/year dropdowns and navigation
        header = self.create_header()
        container_layout.addWidget(header)
        
        # Weekday labels
        weekday_row = self.create_weekday_row()
        container_layout.addWidget(weekday_row)
        
        # Calendar grid
        self.calendar_grid = QGridLayout()
        self.calendar_grid.setSpacing(2)
        self.calendar_grid.setContentsMargins(0, 0, 0, 0)
        container_layout.addLayout(self.calendar_grid)
        
        # Footer with buttons
        footer = self.create_footer()
        container_layout.addWidget(footer)
        
        layout.addWidget(container)
    
    def create_header(self):
        """Create calendar header with month/year dropdowns and navigation"""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 5)
        header_layout.setSpacing(5)
        
        # Previous month button
        self.prev_btn = QPushButton("◀")
        self.prev_btn.setObjectName("navButton")
        self.prev_btn.setFixedSize(30, 30)
        self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor if PYQT_VERSION == 6 else Qt.PointingHandCursor)
        self.prev_btn.clicked.connect(self.previous_month)
        header_layout.addWidget(self.prev_btn)
        
        # Month dropdown
        self.month_combo = QComboBox()
        months = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
        self.month_combo.addItems(months)
        self.month_combo.setCurrentIndex(self.current_month - 1)
        self.month_combo.currentIndexChanged.connect(self.on_month_changed)
        self.month_combo.setCursor(Qt.CursorShape.PointingHandCursor if PYQT_VERSION == 6 else Qt.PointingHandCursor)
        header_layout.addWidget(self.month_combo, 1)
        
        # Year dropdown
        self.year_combo = QComboBox()
        years = [str(year) for year in range(1900, 2101)]
        self.year_combo.addItems(years)
        self.year_combo.setCurrentText(str(self.current_year))
        self.year_combo.currentTextChanged.connect(self.on_year_changed)
        self.year_combo.setCursor(Qt.CursorShape.PointingHandCursor if PYQT_VERSION == 6 else Qt.PointingHandCursor)
        header_layout.addWidget(self.year_combo, 1)
        
        # Next month button
        self.next_btn = QPushButton("▶")
        self.next_btn.setObjectName("navButton")
        self.next_btn.setFixedSize(30, 30)
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor if PYQT_VERSION == 6 else Qt.PointingHandCursor)
        self.next_btn.clicked.connect(self.next_month)
        header_layout.addWidget(self.next_btn)
        
        return header
    
    def create_weekday_row(self):
        """Create row with weekday names"""
        weekday_widget = QWidget()
        weekday_widget.setStyleSheet("background: transparent;")
        weekday_layout = QHBoxLayout(weekday_widget)
        weekday_layout.setContentsMargins(0, 5, 0, 5)
        weekday_layout.setSpacing(2)
        
        weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for day in weekdays:
            label = QLabel(day)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter if PYQT_VERSION == 6 else Qt.AlignCenter)
            label.setFixedSize(48, 25)
            font = QFont()
            font.setPointSize(10)
            font.setBold(True)
            label.setFont(font)
            label.setStyleSheet("color: #333; background: transparent; padding: 0px; margin: 0px; border: none;")
            weekday_layout.addWidget(label)
        
        return weekday_widget
    
    def create_footer(self):
        """Create footer with action buttons"""
        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(0, 10, 0, 0)
        footer_layout.setSpacing(10)
        
        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.setFixedHeight(35)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor if PYQT_VERSION == 6 else Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        
        # Today button
        today_btn = QPushButton("Today")
        today_btn.setObjectName("todayButton")
        today_btn.setFixedHeight(35)
        today_btn.setCursor(Qt.CursorShape.PointingHandCursor if PYQT_VERSION == 6 else Qt.PointingHandCursor)
        today_btn.clicked.connect(self.select_today)
        
        footer_layout.addWidget(cancel_btn)
        footer_layout.addStretch()
        footer_layout.addWidget(today_btn)
        
        return footer
    
    def update_calendar(self):
        """Update calendar display for current month/year"""
        # Update combo boxes (block signals to prevent recursion)
        self.month_combo.blockSignals(True)
        self.year_combo.blockSignals(True)
        self.month_combo.setCurrentIndex(self.current_month - 1)
        self.year_combo.setCurrentText(str(self.current_year))
        self.month_combo.blockSignals(False)
        self.year_combo.blockSignals(False)
        
        # Clear existing calendar cells
        for i in reversed(range(self.calendar_grid.count())):
            widget = self.calendar_grid.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # Get calendar data
        cal = calendar.monthcalendar(self.current_year, self.current_month)
        
        # Create date buttons
        for week_idx, week in enumerate(cal):
            for day_idx, day in enumerate(week):
                if day == 0:
                    # Empty cell for days from other months
                    empty_label = QLabel()
                    empty_label.setFixedSize(48, 38)
                    self.calendar_grid.addWidget(empty_label, week_idx, day_idx)
                else:
                    # Day button
                    btn = QPushButton(str(day))
                    btn.setFixedSize(48, 38)
                    btn.setCursor(Qt.CursorShape.PointingHandCursor if PYQT_VERSION == 6 else Qt.PointingHandCursor)
                    
                    # Create QDate for this day
                    date = QDate(self.current_year, self.current_month, day)
                    
                    # Apply styling based on date type
                    if date == self.today:
                        btn.setObjectName("todayCell")
                    elif date == self.selected_date:
                        btn.setObjectName("selectedCell")
                    else:
                        btn.setObjectName("dayCell")
                    
                    # Connect click event
                    btn.clicked.connect(lambda checked, d=date: self.select_date(d))
                    
                    self.calendar_grid.addWidget(btn, week_idx, day_idx)
        
        # Refresh styles
        self.style().unpolish(self)
        self.style().polish(self)
    
    def select_date(self, date):
        """Select a date and close the dialog"""
        self.selected_date = date
        self.date_selected.emit(date)
        self.accept()
    
    def select_today(self):
        """Select today's date"""
        self.select_date(self.today)
    
    def on_month_changed(self, index):
        """Handle month selection change"""
        self.current_month = index + 1
        self.update_calendar()
    
    def on_year_changed(self, year_text):
        """Handle year selection change"""
        try:
            self.current_year = int(year_text)
            self.update_calendar()
        except ValueError:
            pass
    
    def previous_month(self):
        """Navigate to previous month"""
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self.update_calendar()
    
    def next_month(self):
        """Navigate to next month"""
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        self.update_calendar()
    
    def apply_styles(self):
        """Apply modern styling to calendar"""
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            
            #calendarContainer {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 8px;
            }
            
            QComboBox {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px 8px;
                font-size: 12px;
                color: #333;
            }
            
            QComboBox:hover {
                border-color: #007bff;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #ddd;
                selection-background-color: #007bff;
                selection-color: white;
            }
            
            QPushButton#navButton {
                background-color: #f8f9fa;
                border: 1px solid #ddd;
                border-radius: 4px;
                color: #333;
                font-size: 12px;
                font-weight: bold;
            }
            
            QPushButton#navButton:hover {
                background-color: #007bff;
                border-color: #007bff;
                color: white;
            }
            
            QPushButton#dayCell {
                background-color: white;
                border: 1px solid #eee;
                border-radius: 4px;
                color: #333;
                font-size: 13px;
                padding: 0px;
                margin: 0px;
            }
            
            QPushButton#dayCell:hover {
                background-color: #e7f3ff;
                border-color: #007bff;
                color: #007bff;
            }
            
            QPushButton#todayCell {
                background-color: #fff8e1;
                border: 2px solid #ffc107;
                border-radius: 4px;
                color: #333;
                font-size: 13px;
                font-weight: bold;
                padding: 0px;
                margin: 0px;
            }
            
            QPushButton#todayCell:hover {
                background-color: #ffecb3;
            }
            
            QPushButton#selectedCell {
                background-color: #007bff;
                border: 1px solid #0056b3;
                border-radius: 4px;
                color: white;
                font-size: 13px;
                font-weight: bold;
                padding: 0px;
                margin: 0px;
            }
            
            QPushButton#selectedCell:hover {
                background-color: #0056b3;
            }
            
            QPushButton#todayButton {
                background-color: #007bff;
                border: none;
                border-radius: 4px;
                color: white;
                font-size: 12px;
                font-weight: bold;
                padding: 8px 20px;
            }
            
            QPushButton#todayButton:hover {
                background-color: #0056b3;
            }
            
            QPushButton#cancelButton {
                background-color: #6c757d;
                border: none;
                border-radius: 4px;
                color: white;
                font-size: 12px;
                font-weight: bold;
                padding: 8px 20px;
            }
            
            QPushButton#cancelButton:hover {
                background-color: #5a6268;
            }
        """)


class DateEditWithModernCalendar:
    """Helper class to attach modern calendar to QDateEdit"""
    
    @staticmethod
    def attach_to_date_edit(date_edit):
        """Attach modern calendar popup to a QDateEdit widget"""
        # Disable default calendar popup
        date_edit.setCalendarPopup(False)
        
        # Store original mouse press event
        line_edit = date_edit.lineEdit()
        if line_edit:
            original_mouse_press = line_edit.mousePressEvent
            
            def custom_mouse_press(event):
                # Show modern calendar
                current_date = date_edit.date()
                calendar = ModernCalendar(current_date, date_edit)
                
                # Position the calendar below the date edit
                global_pos = date_edit.mapToGlobal(date_edit.rect().bottomLeft())
                calendar.move(global_pos)
                
                # Connect date selection
                def on_date_selected(selected_date):
                    date_edit.setDate(selected_date)
                
                calendar.date_selected.connect(on_date_selected)
                calendar.exec_() if PYQT_VERSION == 5 else calendar.exec()
                
                # Call original handler if exists
                if original_mouse_press:
                    original_mouse_press(event)
            
            line_edit.mousePressEvent = custom_mouse_press
        
        # Also handle clicks on the date edit itself
        original_date_mouse_press = date_edit.mousePressEvent
        
        def date_edit_mouse_press(event):
            current_date = date_edit.date()
            calendar = ModernCalendar(current_date, date_edit)
            
            # Position the calendar below the date edit
            global_pos = date_edit.mapToGlobal(date_edit.rect().bottomLeft())
            calendar.move(global_pos)
            
            # Connect date selection
            def on_date_selected(selected_date):
                date_edit.setDate(selected_date)
            
            calendar.date_selected.connect(on_date_selected)
            calendar.exec_() if PYQT_VERSION == 5 else calendar.exec()
        
        date_edit.mousePressEvent = date_edit_mouse_press
