"""
Modern PyQt6 dialogs for Delivery Bill Generator
Professional dialogs matching Tally/ZohoBooks style
"""
# Try PyQt5 first (more stable on macOS), fallback to PyQt6
try:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QComboBox, QMessageBox, QTextEdit, QDoubleSpinBox,
        QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
        QListWidget, QListWidgetItem, QInputDialog
    )
    from PyQt5.QtCore import Qt, pyqtSignal, QEvent
    from PyQt5.QtGui import QFont, QWheelEvent
    PYQT_VERSION = 5
    DIALOG_ACCEPTED = QDialog.Accepted
except ImportError:
    # Fallback to PyQt6
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QComboBox, QMessageBox, QTextEdit, QDoubleSpinBox,
        QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
        QListWidget, QListWidgetItem, QInputDialog
    )
    from PyQt6.QtCore import Qt, pyqtSignal, QEvent
    from PyQt6.QtGui import QFont, QWheelEvent
    PYQT_VERSION = 6
    DIALOG_ACCEPTED = QDialog.DialogCode.Accepted
from database import Database


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


class ModernDialog(QDialog):
    """Base class for modern dialogs"""
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QWidget {
                background-color: white;
                color: #212529;
            }
            QLabel {
                color: #212529;
                font-size: 12px;
                background-color: transparent;
            }
            QLineEdit, QComboBox, QTextEdit, QSpinBox, QDoubleSpinBox {
                padding: 8px;
                border: 2px solid #ced4da;
                border-radius: 4px;
                font-size: 12px;
                background-color: white;
                color: #212529;
                selection-background-color: #007bff;
                selection-color: white;
            }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #007bff;
                background-color: white;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #f8f9fa;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: #212529;
                selection-background-color: #007bff;
                selection-color: white;
                border: 1px solid #ced4da;
            }
            QPushButton {
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(20, 20, 20, 20)
    
    def add_button_row(self, buttons):
        """Add a row of buttons"""
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        for btn in buttons:
            btn_layout.addWidget(btn)
        self.layout.addLayout(btn_layout)


class AddAreaDialog(ModernDialog):
    """Dialog for adding a new area"""
    def __init__(self, parent=None, db=None):
        super().__init__("Add Area", parent)
        self.db = db
        
        # Area name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Area Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter area name")
        # Convert to uppercase as user types
        self.name_edit.textChanged.connect(lambda text: self.name_edit.setText(text.upper()))
        name_layout.addWidget(self.name_edit)
        self.layout.addLayout(name_layout)
        
        # Buttons
        btn_save = QPushButton("Save")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        btn_save.clicked.connect(self.save)
        btn_cancel.clicked.connect(self.reject)
        self.add_button_row([btn_cancel, btn_save])
        
        self.name_edit.setFocus()
    
    def save(self):
        """Save the area"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Area name cannot be empty")
            return
        
        try:
            self.db.add_location(name)
            QMessageBox.information(self, "Success", "Area added successfully")
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))


class AddVehicleDialog(ModernDialog):
    """Dialog for adding a new vehicle"""
    def __init__(self, parent=None, db=None):
        super().__init__("Add Vehicle", parent)
        self.db = db
        
        # Vehicle number
        vehicle_layout = QHBoxLayout()
        vehicle_layout.addWidget(QLabel("Vehicle Number:"))
        self.vehicle_edit = QLineEdit()
        self.vehicle_edit.setPlaceholderText("Enter vehicle number")
        # Convert to uppercase as user types
        self.vehicle_edit.textChanged.connect(lambda text: self.vehicle_edit.setText(text.upper()))
        vehicle_layout.addWidget(self.vehicle_edit)
        self.layout.addLayout(vehicle_layout)
        
        # Buttons
        btn_save = QPushButton("Save")
        btn_save.setStyleSheet("background-color: #007bff; color: white;")
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("background-color: #6c757d; color: white;")
        btn_save.clicked.connect(self.save)
        btn_cancel.clicked.connect(self.reject)
        self.add_button_row([btn_cancel, btn_save])
        
        self.vehicle_edit.setFocus()
    
    def save(self):
        """Save the vehicle"""
        vehicle_no = self.vehicle_edit.text().strip().upper()
        if not vehicle_no:
            QMessageBox.warning(self, "Error", "Vehicle number cannot be empty")
            return
        
        try:
            self.db.add_vehicle(vehicle_no)
            QMessageBox.information(self, "Success", "Vehicle added successfully")
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))


class AddUnitDialog(ModernDialog):
    """Dialog for adding a new unit"""
    def __init__(self, parent=None, db=None):
        super().__init__("Add Unit", parent)
        self.db = db
        
        # Unit name
        unit_layout = QHBoxLayout()
        unit_layout.addWidget(QLabel("Unit Name:"))
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText("Enter unit name")
        # Convert to uppercase as user types
        self.unit_edit.textChanged.connect(lambda text: self.unit_edit.setText(text.upper()))
        unit_layout.addWidget(self.unit_edit)
        self.layout.addLayout(unit_layout)
        
        # Buttons
        btn_save = QPushButton("Save")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        btn_save.clicked.connect(self.save)
        btn_cancel.clicked.connect(self.reject)
        self.add_button_row([btn_cancel, btn_save])
        
        self.unit_edit.setFocus()
    
    def save(self):
        """Save the unit"""
        name = self.unit_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Unit name cannot be empty")
            return
        
        try:
            self.db.add_unit(name)
            QMessageBox.information(self, "Success", "Unit added successfully")
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))


class AddCustomerDialog(ModernDialog):
    """Dialog for adding/editing a customer"""
    def __init__(self, parent=None, db=None, customer=None, area_id=None):
        title = "Edit Customer" if customer else "Add Customer"
        super().__init__(title, parent)
        self.db = db
        self.customer = customer
        self.area_id = area_id
        
        # Fields
        fields = [
            ("Name *", "name"),
            # Phone is handled as a custom row with fixed +91 prefix
            ("Address", "address"),
            ("SF.NO", "sf_no"),
            ("RC.NO", "rc_no"),
            ("State", "state"),
            ("GSTIN", "gstin")
        ]
        
        self.entries = {}
        
        # Name row (keep first for focus + required)
        for label, key in fields:
            row_layout = QHBoxLayout()
            row_layout.addWidget(QLabel(label))
            entry = QLineEdit()
            if customer:
                # Display in uppercase
                entry.setText(customer.get(key, '').upper() if customer.get(key) else '')
            elif key == 'state':
                entry.setText('TAMILNADU')
            elif key == 'address' and area_id:
                # Get area name
                areas = db.get_locations()
                area = next((a for a in areas if a['id'] == area_id), None)
                if area:
                    entry.setText(area['name'].upper() if area.get('name') else '')
            entry.setPlaceholderText(f"Enter {label.lower()}")
            # Convert to uppercase as user types
            if key in ['name', 'address', 'sf_no', 'rc_no', 'state', 'gstin']:
                entry.textChanged.connect(lambda text, e=entry: e.setText(text.upper()))
            self.entries[key] = entry
            row_layout.addWidget(entry)
            self.layout.addLayout(row_layout)
            
            # Insert Phone row right after Name row
            if key == "name":
                phone_row = QHBoxLayout()
                phone_row.addWidget(QLabel("Phone"))
                
                prefix = QLabel("+91")
                prefix.setFixedWidth(45)
                prefix.setMinimumHeight(32)
                prefix.setAlignment(Qt.AlignCenter if PYQT_VERSION == 5 else Qt.AlignmentFlag.AlignCenter)
                prefix.setStyleSheet("""
                    QLabel {
                        border: 2px solid #ced4da;
                        border-radius: 4px;
                        padding: 6px 6px;
                        background-color: #f8f9fa;
                        font-size: 12px;
                        font-weight: bold;
                        color: #212529;
                    }
                """)
                phone_row.addWidget(prefix)
                
                self.phone_edit = QLineEdit()
                self.phone_edit.setPlaceholderText("10-digit mobile number")
                self.phone_edit.setMaxLength(10)
                self.phone_edit.setFixedWidth(200)
                
                # Prefill digits when editing (+91XXXXXXXXXX or plain 10 digits)
                if customer:
                    existing = (customer.get("phone") or "").strip()
                    digits = "".join(ch for ch in existing if ch.isdigit())
                    # If stored with country code, keep last 10 digits
                    if len(digits) >= 10:
                        digits = digits[-10:]
                    self.phone_edit.setText(digits)
                
                def _enforce_digits(text):
                    digits_only = "".join(ch for ch in text if ch.isdigit())
                    if digits_only != text:
                        self.phone_edit.blockSignals(True)
                        self.phone_edit.setText(digits_only[:10])
                        self.phone_edit.blockSignals(False)
                    elif len(text) > 10:
                        self.phone_edit.blockSignals(True)
                        self.phone_edit.setText(text[:10])
                        self.phone_edit.blockSignals(False)
                
                self.phone_edit.textChanged.connect(_enforce_digits)
                phone_row.addWidget(self.phone_edit)
                phone_row.addStretch()
                self.layout.addLayout(phone_row)
        
        # Blaster selection - styled like area/vehicle/category
        blaster_layout = QHBoxLayout()
        blaster_label = QLabel("Blaster:")
        blaster_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #212529; min-width: 80px; padding: 2px 0px;")
        blaster_label.setMinimumHeight(45)
        if PYQT_VERSION == 6:
            blaster_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        else:
            blaster_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        blaster_layout.addWidget(blaster_label)
        
        self.blaster_combo = NoWheelComboBox()
        self.blaster_combo.setMinimumWidth(180)
        self.blaster_combo.setMaximumWidth(180)
        self.blaster_combo.setMinimumHeight(45)
        self.blaster_combo.setEditable(False)
        
        # Apply the same dropdown style as category/area/vehicle
        dropdown_field_style = """
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
        self.blaster_combo.setStyleSheet(dropdown_field_style)
        
        # Populate blasters
        blasters = db.get_blasters()
        self.blaster_combo.addItem("-- Select Blaster --", None)
        for blaster in blasters:
            self.blaster_combo.addItem(blaster['name'], blaster['id'])
        
        if customer and customer.get('blaster_id'):
            index = self.blaster_combo.findData(customer['blaster_id'])
            if index >= 0:
                self.blaster_combo.setCurrentIndex(index)
        
        # Create custom popup with add/manage buttons
        self._create_blaster_popup()
        # Override showPopup to use custom popup
        self.blaster_combo.showPopup = self._show_blaster_popup
        # Disable default popup
        self.blaster_combo.setMaxVisibleItems(0)
        if hasattr(self.blaster_combo, 'view'):
            self.blaster_combo.view().setVisible(False)
        
        blaster_layout.addWidget(self.blaster_combo)
        blaster_layout.addStretch()
        self.layout.addLayout(blaster_layout)
        
        # Buttons
        btn_save = QPushButton("Save")
        btn_save.setStyleSheet("background-color: #007bff; color: white;")
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("background-color: #6c757d; color: white;")
        btn_save.clicked.connect(self.save)
        btn_cancel.clicked.connect(self.reject)
        self.add_button_row([btn_cancel, btn_save])
        
        self.entries['name'].setFocus()
    
    def _create_blaster_popup(self):
        """Create a custom popup for blaster selection with add/manage buttons."""
        if PYQT_VERSION == 6:
            from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListView, QPushButton
            from PyQt6.QtCore import Qt
        else:
            from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListView, QPushButton
            from PyQt5.QtCore import Qt
        
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
        list_view.setMinimumWidth(self.blaster_combo.width())
        list_view.setFocus()
        list_view.clicked.connect(lambda index: self._handle_blaster_selection(popup, index))
        
        # Add keyboard support
        def list_key_press(event):
            if PYQT_VERSION == 6:
                if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                    current_index = list_view.currentIndex()
                    if current_index.isValid():
                        self._handle_blaster_selection(popup, current_index)
                elif event.key() == Qt.Key.Key_Escape:
                    popup.close()
                else:
                    QListView.keyPressEvent(list_view, event)
            else:
                if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                    current_index = list_view.currentIndex()
                    if current_index.isValid():
                        self._handle_blaster_selection(popup, current_index)
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
        
        add_btn = QPushButton("+ Add")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        add_btn.clicked.connect(lambda: self._handle_blaster_action(popup, self.add_blaster))
        
        manage_btn = QPushButton("Manage")
        manage_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        manage_btn.clicked.connect(lambda: self._handle_blaster_action(popup, self.manage_blasters))
        
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
        """)
        
        self.blaster_combo._custom_popup = popup
        self.blaster_combo._custom_list_view = list_view
    
    def _show_blaster_popup(self):
        """Show the custom popup for blaster combo box."""
        if not hasattr(self.blaster_combo, '_custom_popup'):
            return
        
        popup = self.blaster_combo._custom_popup
        list_view = self.blaster_combo._custom_list_view
        
        # Create a model with all combo box items
        if PYQT_VERSION == 6:
            from PyQt6.QtGui import QStandardItemModel, QStandardItem
            from PyQt6.QtCore import Qt
        else:
            from PyQt5.QtGui import QStandardItemModel, QStandardItem
            from PyQt5.QtCore import Qt
        
        model = QStandardItemModel()
        # Add all items from combo box
        for i in range(self.blaster_combo.count()):
            item = QStandardItem(self.blaster_combo.itemText(i))
            model.appendRow(item)
        
        list_view.setModel(model)
        
        # Set current selection in list view to match combo box
        current_index = self.blaster_combo.currentIndex()
        if current_index >= 0:
            list_view.setCurrentIndex(model.index(current_index, 0))
        
        # Position popup below combo box
        global_pos = self.blaster_combo.mapToGlobal(self.blaster_combo.rect().bottomLeft())
        popup.move(global_pos)
        popup.show()
        popup.raise_()
        popup.activateWindow()
        list_view.setFocus()
    
    def _handle_blaster_selection(self, popup, index):
        """Handle selection from custom popup."""
        self.blaster_combo.setCurrentIndex(index.row())
        popup.close()
    
    def _handle_blaster_action(self, popup, callback):
        """Handle action button click from popup."""
        popup.close()
        if callback:
            callback()
            # Refresh blaster combo after add/manage
            self.refresh_blaster_combo()
    
    def refresh_blaster_combo(self):
        """Refresh the blaster combo box from database"""
        current_id = self.blaster_combo.currentData()
        self.blaster_combo.clear()
        self.blaster_combo.addItem("-- Select Blaster --", None)
        blasters = self.db.get_blasters()
        for blaster in blasters:
            self.blaster_combo.addItem(blaster['name'], blaster['id'])
        
        # Restore previous selection if it still exists
        if current_id:
            index = self.blaster_combo.findData(current_id)
            if index >= 0:
                self.blaster_combo.setCurrentIndex(index)
    
    def add_blaster(self):
        """Add a new blaster"""
        dialog = AddBlasterDialog(self, self.db)
        result = dialog.exec_() if PYQT_VERSION == 5 else dialog.exec()
        if result == DIALOG_ACCEPTED:
            self.refresh_blaster_combo()
    
    def manage_blasters(self):
        """Manage blasters (add, edit, delete)"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Manage Blasters")
        layout = QVBoxLayout(dialog)
        list_widget = QListWidget()
        layout.addWidget(list_widget)
        
        def refresh():
            list_widget.clear()
            for blaster in self.db.get_blasters():
                display = blaster.get('name', '') or "(No name)"
                list_item = QListWidgetItem(display)
                if PYQT_VERSION == 6:
                    list_item.setData(Qt.ItemDataRole.UserRole, blaster)
                else:
                    list_item.setData(Qt.UserRole, blaster)
                list_widget.addItem(list_item)
        refresh()
        
        btn_row = QHBoxLayout()
        btn_add = QPushButton("Add")
        btn_add.setStyleSheet("background-color: #28a745; color: white;")
        btn_edit = QPushButton("Edit")
        btn_edit.setStyleSheet("background-color: #007bff; color: white;")
        btn_delete = QPushButton("Delete")
        btn_delete.setStyleSheet("background-color: #dc3545; color: white;")
        btn_close = QPushButton("Close")
        btn_close.setStyleSheet("background-color: #6c757d; color: white;")
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_delete)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)
        
        def current_item():
            item = list_widget.currentItem()
            if not item:
                QMessageBox.warning(dialog, "Select Item", "Please select a blaster first.")
                return None
            if PYQT_VERSION == 6:
                return item.data(Qt.ItemDataRole.UserRole)
            else:
                return item.data(Qt.UserRole)
        
        def add_action():
            blaster_dialog = AddBlasterDialog(dialog, self.db)
            result = blaster_dialog.exec_() if PYQT_VERSION == 5 else blaster_dialog.exec()
            if result == DIALOG_ACCEPTED:
                refresh()
                self.refresh_blaster_combo()
        
        def edit_action():
            data = current_item()
            if not data:
                return
            # Create edit dialog (reuse AddBlasterDialog with existing data)
            blaster_dialog = AddBlasterDialog(dialog, self.db, blaster=data)
            result = blaster_dialog.exec_() if PYQT_VERSION == 5 else blaster_dialog.exec()
            if result == DIALOG_ACCEPTED:
                refresh()
                self.refresh_blaster_combo()
        
        def delete_action():
            data = current_item()
            if not data:
                return
            reply = QMessageBox.question(
                dialog, "Delete Blaster",
                f"Delete blaster '{data.get('name', '')}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.db.delete_blaster(data['id'])
                    refresh()
                    self.refresh_blaster_combo()
                except Exception as e:
                    QMessageBox.warning(dialog, "Error", str(e))
        
        btn_add.clicked.connect(add_action)
        btn_edit.clicked.connect(edit_action)
        btn_delete.clicked.connect(delete_action)
        btn_close.clicked.connect(dialog.close)
        
        dialog.exec_() if PYQT_VERSION == 5 else dialog.exec()
    
    def save(self):
        """Save the customer - convert all text fields to uppercase"""
        name = self.entries['name'].text().strip().upper()
        if not name:
            QMessageBox.warning(self, "Error", "Customer name is required")
            return
        
        blaster_id = self.blaster_combo.currentData()
        
        # Convert all text fields to uppercase
        address = self.entries['address'].text().strip().upper()
        sf_no = self.entries['sf_no'].text().strip().upper()
        rc_no = self.entries['rc_no'].text().strip().upper()
        state = self.entries['state'].text().strip().upper()
        gstin = self.entries['gstin'].text().strip().upper()
        
        phone_digits = (self.phone_edit.text().strip() if hasattr(self, "phone_edit") else "")
        if phone_digits and len(phone_digits) != 10:
            QMessageBox.warning(self, "Error", "Phone number must be exactly 10 digits")
            return
        phone_full = f"+91{phone_digits}" if phone_digits else ""
        
        try:
            if self.customer:
                # Update
                self.db.update_customer(
                    self.customer['id'],
                    name,
                    address,
                    sf_no,
                    rc_no,
                    state,
                    gstin,
                    phone_full,
                    blaster_id,
                    self.area_id
                )
                QMessageBox.information(self, "Success", "Customer updated successfully")
            else:
                # Add
                self.db.add_customer(
                    name,
                    address,
                    sf_no,
                    rc_no,
                    state,
                    gstin,
                    phone_full,
                    blaster_id,
                    self.area_id
                )
                QMessageBox.information(self, "Success", "Customer added successfully")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save customer: {str(e)}")


class AddBlasterDialog(ModernDialog):
    """Dialog for adding/editing a blaster"""
    def __init__(self, parent=None, db=None, blaster=None):
        title = "Edit Blaster" if blaster else "Add Blaster"
        super().__init__(title, parent)
        self.db = db
        self.blaster = blaster
        
        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name *:"))
        self.name_edit = QLineEdit()
        if blaster:
            self.name_edit.setText(blaster.get('name', '').upper() if blaster.get('name') else '')
        # Convert to uppercase as user types
        self.name_edit.textChanged.connect(lambda text: self.name_edit.setText(text.upper()))
        name_layout.addWidget(self.name_edit)
        self.layout.addLayout(name_layout)
        
        # Document No
        doc_layout = QHBoxLayout()
        doc_layout.addWidget(QLabel("Document No:"))
        self.doc_edit = QLineEdit()
        if blaster:
            self.doc_edit.setText(blaster.get('document_no', '').upper() if blaster.get('document_no') else '')
        # Convert to uppercase as user types
        self.doc_edit.textChanged.connect(lambda text: self.doc_edit.setText(text.upper()))
        doc_layout.addWidget(self.doc_edit)
        self.layout.addLayout(doc_layout)
        
        # Address
        address_layout = QVBoxLayout()
        address_layout.addWidget(QLabel("Address:"))
        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(80)
        if blaster:
            self.address_edit.setPlainText(blaster.get('address', '').upper() if blaster.get('address') else '')
        # Convert to uppercase as user types
        def make_address_upper():
            current_text = self.address_edit.toPlainText()
            cursor = self.address_edit.textCursor()
            cursor_pos = cursor.position()
            upper_text = current_text.upper()
            if current_text != upper_text:
                self.address_edit.setPlainText(upper_text)
                # Restore cursor position
                cursor.setPosition(min(cursor_pos, len(upper_text)))
                self.address_edit.setTextCursor(cursor)
        self.address_edit.textChanged.connect(make_address_upper)
        address_layout.addWidget(self.address_edit)
        self.layout.addLayout(address_layout)
        
        # Buttons
        btn_save = QPushButton("Save")
        btn_save.setStyleSheet("background-color: #007bff; color: white;")
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("background-color: #6c757d; color: white;")
        btn_save.clicked.connect(self.save)
        btn_cancel.clicked.connect(self.reject)
        self.add_button_row([btn_cancel, btn_save])
        
        self.name_edit.setFocus()
    
    def save(self):
        """Save the blaster"""
        name = self.name_edit.text().strip().upper()
        if not name:
            QMessageBox.warning(self, "Error", "Blaster name is required")
            return
        
        try:
            if self.blaster:
                # Update existing blaster
                self.db.update_blaster(
                    self.blaster['id'],
                    name,
                    self.doc_edit.text().strip().upper(),
                    self.address_edit.toPlainText().strip().upper()
                )
                QMessageBox.information(self, "Success", "Blaster updated successfully")
            else:
                # Add new blaster
                self.db.add_blaster(
                    name,
                    self.doc_edit.text().strip().upper(),
                    self.address_edit.toPlainText().strip().upper()
                )
                QMessageBox.information(self, "Success", "Blaster added successfully")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save blaster: {str(e)}")


class AddGoodDialog(ModernDialog):
    """Dialog for adding a good to customer"""
    def __init__(self, parent=None, db=None, default_cgst_rate=9.0, default_sgst_rate=9.0, category=None):
        super().__init__("Add Good to Customer", parent)
        self.db = db
        self.default_cgst_rate = default_cgst_rate
        self.default_sgst_rate = default_sgst_rate
        self.category = category
        self.item_data = None
        
        field_width = 250
        
        # Good selection (filtered by category) - styled like area/vehicle
        good_layout = QHBoxLayout()
        good_label = QLabel("Good description:")
        good_label.setMinimumWidth(120)
        good_layout.addWidget(good_label)
        
        self.good_combo = NoWheelComboBox()
        self.good_combo.setMinimumWidth(field_width)
        self.good_combo.setMaximumWidth(field_width)
        self.good_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #ced4da;
                border-radius: 4px;
                font-size: 12px;
                background-color: white;
            }
            QComboBox:focus {
                border: 2px solid #007bff;
            }
            QComboBox::drop-down {
                border: none;
                width: 0px;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
        """)
        goods = db.get_goods(category=category) if category else db.get_goods()
        self.good_combo.addItem("--Select Good--", None)
        for good in goods:
            self.good_combo.addItem(f"{good['description']} ({good['hsn_code']})", good)
        self.good_combo.currentIndexChanged.connect(self.on_good_selected)
        good_layout.addWidget(self.good_combo)
        
        btn_new_good = QPushButton("+ New Good")
        btn_new_good.setStyleSheet("background-color: #28a745; color: white; padding: 8px 15px; border-radius: 4px;")
        btn_new_good.clicked.connect(self.add_new_good)
        good_layout.addWidget(btn_new_good)
        good_layout.addStretch()
        self.layout.addLayout(good_layout)
        
        # Tax rate editing - styled like Manage Goods Rate field
        # CGST Rate
        cgst_layout = QHBoxLayout()
        cgst_label = QLabel("CGST Rate %:")
        cgst_label.setMinimumWidth(120)
        cgst_layout.addWidget(cgst_label)
        self.cgst_spin = QDoubleSpinBox()
        self.cgst_spin.setMinimum(0)
        self.cgst_spin.setMaximum(100)
        self.cgst_spin.setValue(default_cgst_rate)
        self.cgst_spin.setDecimals(2)
        self.cgst_spin.setMinimumWidth(field_width)
        self.cgst_spin.setMaximumWidth(field_width)
        self.cgst_spin.setStyleSheet("""
            QDoubleSpinBox {
                padding: 8px;
                border: 2px solid #ced4da;
                border-radius: 4px;
                font-size: 12px;
                background-color: white;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #007bff;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 20px;
            }
        """)
        self.cgst_spin.valueChanged.connect(self.calculate)
        cgst_layout.addWidget(self.cgst_spin)
        cgst_layout.addStretch()
        self.layout.addLayout(cgst_layout)
        
        # SGST Rate
        sgst_layout = QHBoxLayout()
        sgst_label = QLabel("SGST Rate %:")
        sgst_label.setMinimumWidth(120)
        sgst_layout.addWidget(sgst_label)
        self.sgst_spin = QDoubleSpinBox()
        self.sgst_spin.setMinimum(0)
        self.sgst_spin.setMaximum(100)
        self.sgst_spin.setValue(default_sgst_rate)
        self.sgst_spin.setDecimals(2)
        self.sgst_spin.setMinimumWidth(field_width)
        self.sgst_spin.setMaximumWidth(field_width)
        self.sgst_spin.setStyleSheet("""
            QDoubleSpinBox {
                padding: 8px;
                border: 2px solid #ced4da;
                border-radius: 4px;
                font-size: 12px;
                background-color: white;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #007bff;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 20px;
            }
        """)
        self.sgst_spin.valueChanged.connect(self.calculate)
        sgst_layout.addWidget(self.sgst_spin)
        sgst_layout.addStretch()
        self.layout.addLayout(sgst_layout)
        
        # IGST Rate (empty by default)
        igst_layout = QHBoxLayout()
        igst_label = QLabel("IGST Rate %:")
        igst_label.setMinimumWidth(120)
        igst_layout.addWidget(igst_label)
        self.igst_spin = QDoubleSpinBox()
        self.igst_spin.setMinimum(0)
        self.igst_spin.setMaximum(100)
        self.igst_spin.setValue(0)  # Empty by default
        self.igst_spin.setDecimals(2)
        self.igst_spin.setMinimumWidth(field_width)
        self.igst_spin.setMaximumWidth(field_width)
        self.igst_spin.setStyleSheet("""
            QDoubleSpinBox {
                padding: 8px;
                border: 2px solid #ced4da;
                border-radius: 4px;
                font-size: 12px;
                background-color: white;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #007bff;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 20px;
            }
        """)
        self.igst_spin.valueChanged.connect(self.calculate)
        igst_layout.addWidget(self.igst_spin)
        igst_layout.addStretch()
        self.layout.addLayout(igst_layout)
        
        # Quantity - styled like Rate fields
        qty_layout = QHBoxLayout()
        qty_label = QLabel("Quantity:")
        qty_label.setMinimumWidth(120)
        qty_layout.addWidget(qty_label)
        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setMinimum(0.01)
        self.qty_spin.setMaximum(999999)
        self.qty_spin.setValue(1.0)
        self.qty_spin.setDecimals(2)
        self.qty_spin.setMinimumWidth(field_width)
        self.qty_spin.setMaximumWidth(field_width)
        self.qty_spin.setStyleSheet("""
            QDoubleSpinBox {
                padding: 8px;
                border: 2px solid #ced4da;
                border-radius: 4px;
                font-size: 12px;
                background-color: white;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #007bff;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 20px;
            }
        """)
        self.qty_spin.valueChanged.connect(self.calculate)
        qty_layout.addWidget(self.qty_spin)
        qty_layout.addStretch()
        self.layout.addLayout(qty_layout)
        
        # Display selected good details
        self.details_group = QGroupBox("Good Details")
        self.details_layout = QVBoxLayout()
        self.details_group.setLayout(self.details_layout)
        self.layout.addWidget(self.details_group)
        
        # Buttons
        btn_add = QPushButton("Add to Bill")
        btn_add.setStyleSheet("background-color: #28a745; color: white;")
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("background-color: #6c757d; color: white;")
        btn_add.clicked.connect(self.add_item)
        btn_cancel.clicked.connect(self.reject)
        self.add_button_row([btn_cancel, btn_add])
    
    def on_good_selected(self):
        """Handle good selection"""
        # Clear details
        while self.details_layout.count():
            item = self.details_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        good_data = self.good_combo.currentData()
        if not good_data:
            return
        
        # Show good details
        self.details_layout.addWidget(QLabel(f"<b>Description:</b> {good_data['description']}"))
        self.details_layout.addWidget(QLabel(f"<b>HSN Code:</b> {good_data['hsn_code']}"))
        self.details_layout.addWidget(QLabel(f"<b>Unit:</b> {good_data['unit']}"))
        self.details_layout.addWidget(QLabel(f"<b>Rate:</b> ₹{good_data['rate']:.2f}"))
        
        self.calculate()
    
    def calculate(self):
        """Calculate item totals"""
        good_data = self.good_combo.currentData()
        if not good_data:
            return
        
        qty = self.qty_spin.value()
        rate = good_data['rate']
        total = qty * rate
        taxable_value = total
        # Use editable tax rates
        cgst_rate = self.cgst_spin.value()
        sgst_rate = self.sgst_spin.value()
        igst_rate = self.igst_spin.value()
        cgst_rs = (taxable_value * cgst_rate) / 100
        sgst_rs = (taxable_value * sgst_rate) / 100
        igst_rs = (taxable_value * igst_rate) / 100
        total_amount = total + cgst_rs + sgst_rs + igst_rs
        
        # Update or add total display
        if self.details_layout.count() > 4:
            # Remove old total
            item = self.details_layout.takeAt(4)
            if item.widget():
                item.widget().deleteLater()
        
        total_label = QLabel(f"<b>Total Amount:</b> ₹{total_amount:.2f}")
        total_label.setStyleSheet("font-size: 14px; color: #007bff; font-weight: bold;")
        self.details_layout.addWidget(total_label)
    
    def add_new_good(self):
        """Add a new good"""
        dialog = NewGoodDialog(self, self.db, category=self.category)
        result = dialog.exec_() if PYQT_VERSION == 5 else dialog.exec()
        if result == DIALOG_ACCEPTED:
            # Refresh good combo (filtered by category)
            self.good_combo.clear()
            self.good_combo.addItem("--Select Good--", None)
            goods = self.db.get_goods(category=self.category) if self.category else self.db.get_goods()
            for good in goods:
                self.good_combo.addItem(f"{good['description']} ({good['hsn_code']})", good)
    
    def add_item(self):
        """Add item to customer"""
        good_data = self.good_combo.currentData()
        if not good_data:
            QMessageBox.warning(self, "Error", "Please select a good")
            return
        
        qty = self.qty_spin.value()
        rate = good_data['rate']
        total = qty * rate
        taxable_value = total
        # Use editable tax rates
        cgst_rate = self.cgst_spin.value()
        sgst_rate = self.sgst_spin.value()
        igst_rate = self.igst_spin.value()
        cgst_rs = (taxable_value * cgst_rate) / 100
        sgst_rs = (taxable_value * sgst_rate) / 100
        igst_rs = (taxable_value * igst_rate) / 100
        total_amount = total + cgst_rs + sgst_rs + igst_rs
        
        self.item_data = {
            'description': good_data['description'],
            'hsn_code': good_data['hsn_code'],
            'unit': good_data['unit'],
            'qty': qty,
            'rate': rate,
            'total': total,
            'taxable_value': taxable_value,
            'cgst_rate': cgst_rate,
            'cgst_rs': cgst_rs,
            'sgst_rate': sgst_rate,
            'sgst_rs': sgst_rs,
            'igst_rate': igst_rate,
            'igst_rs': igst_rs,
            'total_amount': total_amount
        }
        
        self.accept()


class NewGoodDialog(ModernDialog):
    """Dialog for adding a new good"""
    def __init__(self, parent=None, db=None, category=None):
        super().__init__("Add New Good", parent)
        self.db = db
        self.category = category
        
        # Uniform field width
        field_width = 250
        
        # Description
        desc_layout = QHBoxLayout()
        desc_label = QLabel("Description *:")
        desc_label.setMinimumWidth(100)
        desc_layout.addWidget(desc_label)
        self.desc_edit = QLineEdit()
        self.desc_edit.setMinimumWidth(field_width)
        self.desc_edit.setMaximumWidth(field_width)
        # Convert to uppercase as user types
        self.desc_edit.textChanged.connect(lambda text: self.desc_edit.setText(text.upper()))
        desc_layout.addWidget(self.desc_edit)
        desc_layout.addStretch()
        self.layout.addLayout(desc_layout)
        
        # Category dropdown - same style as in configuration
        category_layout = QHBoxLayout()
        category_label = QLabel("Category *:")
        category_label.setMinimumWidth(100)
        category_layout.addWidget(category_label)
        self.category_combo = NoWheelComboBox()
        self.category_combo.addItem("-- Select Category --", None)  # Placeholder
        self.category_combo.addItem("Detonator", "Detonator")
        self.category_combo.addItem("Explosives", "Explosives")
        self.category_combo.setMinimumWidth(field_width)
        self.category_combo.setMaximumWidth(field_width)
        self.category_combo.setEditable(False)
        # Exact same styling as configuration category field
        self.category_combo.setStyleSheet("""
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
        """)
        if category:
            index = self.category_combo.findData(category)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
        category_layout.addWidget(self.category_combo)
        category_layout.addStretch()
        self.layout.addLayout(category_layout)
        
        # HSN Code
        hsn_layout = QHBoxLayout()
        hsn_label = QLabel("HSN Code *:")
        hsn_label.setMinimumWidth(100)
        hsn_layout.addWidget(hsn_label)
        self.hsn_edit = QLineEdit()
        self.hsn_edit.setMinimumWidth(field_width)
        self.hsn_edit.setMaximumWidth(field_width)
        # Convert to uppercase as user types
        self.hsn_edit.textChanged.connect(lambda text: self.hsn_edit.setText(text.upper()))
        hsn_layout.addWidget(self.hsn_edit)
        hsn_layout.addStretch()
        self.layout.addLayout(hsn_layout)
        
        # Rate 
        rate_layout = QHBoxLayout()
        rate_label = QLabel("Rate *:")
        rate_label.setMinimumWidth(100)
        rate_layout.addWidget(rate_label)
        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setMinimum(0.01)
        self.rate_spin.setMaximum(999999)
        self.rate_spin.setDecimals(2)
        self.rate_spin.setMinimumWidth(field_width)
        self.rate_spin.setMaximumWidth(field_width)
        # Minimal styling to show arrows clearly
        self.rate_spin.setStyleSheet("""
            QDoubleSpinBox {
                padding: 8px 8px 8px 8px;
                border: 2px solid #ced4da;
                border-radius: 4px;
                font-size: 12px;
                background-color: white;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #007bff;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 20px;
            }
        """)
        rate_layout.addWidget(self.rate_spin)
        rate_layout.addStretch()
        self.layout.addLayout(rate_layout)
        
        # Unit
        unit_layout = QHBoxLayout()
        unit_label = QLabel("Unit *:")
        unit_label.setMinimumWidth(100)
        unit_layout.addWidget(unit_label)
        self.unit_combo = NoWheelComboBox()
        self.unit_combo.setMinimumWidth(field_width)
        self.unit_combo.setMaximumWidth(field_width)
        self.unit_combo.setEditable(False)
        # Style similar to area/vehicle combo
        self.unit_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            QComboBox:focus {
                border: 2px solid #007bff;
            }
            QComboBox::drop-down {
                border: none;
                width: 0px;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
        """)
        # Disable default popup, use custom one
        self.unit_combo.setMaxVisibleItems(0)
        if hasattr(self.unit_combo, 'view'):
            self.unit_combo.view().setVisible(False)
        # Create custom popup
        self._create_unit_popup()
        # Override showPopup to use custom popup
        self.unit_combo.showPopup = self._show_unit_popup
        self.refresh_units()
        unit_layout.addWidget(self.unit_combo)
        unit_layout.addStretch()
        self.layout.addLayout(unit_layout)
        
        # Buttons
        btn_save = QPushButton("Save")
        btn_save.setStyleSheet("background-color: #007bff; color: white;")
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("background-color: #6c757d; color: white;")
        btn_save.clicked.connect(self.save)
        btn_cancel.clicked.connect(self.reject)
        self.add_button_row([btn_cancel, btn_save])
        
        self.desc_edit.setFocus()
    
    def _create_unit_popup(self):
        """Create a custom popup for unit selection with add/manage buttons."""
        if PYQT_VERSION == 6:
            from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListView
            from PyQt6.QtCore import Qt
        else:
            from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListView
            from PyQt5.QtCore import Qt
        
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
        list_view.setMinimumWidth(self.unit_combo.width())
        list_view.setFocus()
        list_view.clicked.connect(lambda index: self._handle_unit_selection(popup, index))
        
        # Add keyboard support
        def list_key_press(event):
            if PYQT_VERSION == 6:
                if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                    current_index = list_view.currentIndex()
                    if current_index.isValid():
                        self._handle_unit_selection(popup, current_index)
                elif event.key() == Qt.Key.Key_Escape:
                    popup.close()
                else:
                    QListView.keyPressEvent(list_view, event)
            else:
                if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                    current_index = list_view.currentIndex()
                    if current_index.isValid():
                        self._handle_unit_selection(popup, current_index)
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
        
        add_btn = QPushButton("+ Add")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        add_btn.clicked.connect(lambda: self._handle_unit_action(popup, self.add_new_unit))
        
        manage_btn = QPushButton("Manage")
        manage_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        manage_btn.clicked.connect(lambda: self._handle_unit_action(popup, self.manage_units))
        
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
        """)
        
        self.unit_combo._custom_popup = popup
        self.unit_combo._custom_list_view = list_view
    
    def _show_unit_popup(self):
        """Show the custom popup for unit combo box."""
        if not hasattr(self.unit_combo, '_custom_popup'):
            return
        
        popup = self.unit_combo._custom_popup
        list_view = self.unit_combo._custom_list_view
        
        # Create a model with all combo box items
        if PYQT_VERSION == 6:
            from PyQt6.QtGui import QStandardItemModel, QStandardItem
            from PyQt6.QtCore import Qt
        else:
            from PyQt5.QtGui import QStandardItemModel, QStandardItem
            from PyQt5.QtCore import Qt
        
        model = QStandardItemModel()
        # Add all items from combo box
        for i in range(self.unit_combo.count()):
            item = QStandardItem(self.unit_combo.itemText(i))
            model.appendRow(item)
        
        list_view.setModel(model)
        
        # Set current selection in list view to match combo box
        current_index = self.unit_combo.currentIndex()
        if current_index >= 0:
            list_view.setCurrentIndex(model.index(current_index, 0))
        
        # Position popup below combo box
        global_pos = self.unit_combo.mapToGlobal(self.unit_combo.rect().bottomLeft())
        popup.move(global_pos)
        popup.show()
        popup.raise_()
        popup.activateWindow()
        list_view.setFocus()
    
    def _handle_unit_selection(self, popup, index):
        """Handle selection from custom popup."""
        self.unit_combo.setCurrentIndex(index.row())
        popup.close()
    
    def _handle_unit_action(self, popup, callback):
        """Handle action button click from popup."""
        popup.close()
        if callback:
            callback()
            # Refresh units after add/manage
            self.refresh_units()
    
    def refresh_units(self):
        """Refresh the unit combo box from database"""
        self.unit_combo.clear()
        self.unit_combo.addItem("--Select Unit--", None)
        units = self.db.get_units()
        for unit in units:
            self.unit_combo.addItem(unit['name'])
    
    def add_new_unit(self):
        """Add a new unit"""
        dialog = AddUnitDialog(self, self.db)
        result = dialog.exec_() if PYQT_VERSION == 5 else dialog.exec()
        if result == DIALOG_ACCEPTED:
            self.refresh_units()
            # Select the newly added unit
            units = self.db.get_units()
            if units:
                new_unit = units[-1]  # Last added
                index = self.unit_combo.findText(new_unit['name'])
                if index >= 0:
                    self.unit_combo.setCurrentIndex(index)
    
    def manage_units(self):
        """Manage units (add, rename, delete)"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Manage Units")
        layout = QVBoxLayout(dialog)
        list_widget = QListWidget()
        layout.addWidget(list_widget)
        
        def refresh():
            list_widget.clear()
            for unit in self.db.get_units():
                display = unit.get('name', '') or "(No name)"
                list_item = QListWidgetItem(display)
                if PYQT_VERSION == 6:
                    list_item.setData(Qt.ItemDataRole.UserRole, unit)
                else:
                    list_item.setData(Qt.UserRole, unit)
                list_widget.addItem(list_item)
        refresh()
        
        btn_row = QHBoxLayout()
        btn_add = QPushButton("Add")
        btn_add.setStyleSheet("background-color: #28a745; color: white;")
        btn_edit = QPushButton("Edit")
        btn_edit.setStyleSheet("background-color: #007bff; color: white;")
        btn_delete = QPushButton("Delete")
        btn_delete.setStyleSheet("background-color: #dc3545; color: white;")
        btn_close = QPushButton("Close")
        btn_close.setStyleSheet("background-color: #6c757d; color: white;")
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
            if PYQT_VERSION == 6:
                return item.data(Qt.ItemDataRole.UserRole)
            else:
                return item.data(Qt.UserRole)
        
        def add_action():
            unit_dialog = AddUnitDialog(dialog, self.db)
            result = unit_dialog.exec_() if PYQT_VERSION == 5 else unit_dialog.exec()
            if result == DIALOG_ACCEPTED:
                refresh()
                self.refresh_units()
        
        def edit_action():
            data = current_item()
            if not data:
                return
            current_name = data.get('name', '').upper()
            new_name, ok = QInputDialog.getText(dialog, "Rename Unit", "Unit name:", text=current_name)
            if ok and new_name.strip():
                try:
                    self.db.update_unit(data['id'], new_name.strip())
                    refresh()
                    self.refresh_units()
                except Exception as e:
                    QMessageBox.warning(dialog, "Error", str(e))
        
        def delete_action():
            data = current_item()
            if not data:
                return
            reply = QMessageBox.question(
                dialog, "Delete Unit",
                f"Delete unit '{data.get('name', '')}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.db.delete_unit(data['id'])
                    refresh()
                    self.refresh_units()
                except Exception as e:
                    QMessageBox.warning(dialog, "Error", str(e))
        
        btn_add.clicked.connect(add_action)
        btn_edit.clicked.connect(edit_action)
        btn_delete.clicked.connect(delete_action)
        btn_close.clicked.connect(dialog.close)
        
        dialog.exec_() if PYQT_VERSION == 5 else dialog.exec()
    
    def save(self):
        """Save the good"""
        description = self.desc_edit.text().strip()
        hsn_code = self.hsn_edit.text().strip()
        unit = self.unit_combo.currentText()
        rate = self.rate_spin.value()
        category = self.category_combo.currentData()
        
        if not description:
            QMessageBox.warning(self, "Error", "Description is required")
            return
        
        if not hsn_code:
            QMessageBox.warning(self, "Error", "HSN Code is required")
            return
        
        if not category:
            QMessageBox.warning(self, "Error", "Please select a Category")
            return
        
        if not unit:
            QMessageBox.warning(self, "Error", "Please select a Unit")
            return
        
        try:
            self.db.add_good(description, hsn_code, unit, rate, category)
            QMessageBox.information(self, "Success", "Good added successfully")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to add good: {str(e)}")


class SelectCustomerDialog(ModernDialog):
    """Dialog for selecting a customer to edit"""
    def __init__(self, parent=None, customers=None):
        super().__init__("Select Customer to Edit", parent)
        self.selected_customer = None
        
        self.list_widget = QListWidget()
        for customer in customers:
            item = QListWidgetItem(customer['name'])
            item.setData(Qt.ItemDataRole.UserRole, customer)
            self.list_widget.addItem(item)
        
        self.list_widget.itemDoubleClicked.connect(self.accept_selection)
        self.layout.addWidget(self.list_widget)
        
        # Buttons
        btn_edit = QPushButton("Edit Selected")
        btn_edit.setStyleSheet("background-color: #007bff; color: white;")
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("background-color: #6c757d; color: white;")
        btn_edit.clicked.connect(self.accept_selection)
        btn_cancel.clicked.connect(self.reject)
        self.add_button_row([btn_cancel, btn_edit])
    
    def accept_selection(self):
        """Accept the selected customer"""
        current_item = self.list_widget.currentItem()
        if current_item:
            self.selected_customer = current_item.data(Qt.ItemDataRole.UserRole)
            self.accept()
        else:
            QMessageBox.warning(self, "Warning", "Please select a customer")


class LicenseActivationDialog(ModernDialog):
    """Dialog for activating the application license"""
    def __init__(self, hardware_id, parent=None):
        super().__init__("Activate License", parent)
        self.hardware_id = hardware_id
        self.setMinimumWidth(750)
        self.setMinimumHeight(550)
        self.resize(800, 600)
        
        self.setup_ui()
        
        # macOS-specific: Ensure dialog is visible and on top
        self.raise_()
        self.activateWindow()
    
    def setup_ui(self):
        # Use the base class layout instead of creating a new one
        layout = self.layout
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("License Activation Required")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #212529; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Info text
        info_text = QLabel(
            "This application requires a valid license to run.\n"
            "Please enter your license key below to activate."
        )
        info_text.setStyleSheet("font-size: 12px; color: #6c757d; margin-bottom: 20px;")
        layout.addWidget(info_text)
        
        # Hardware ID display
        hw_group = QGroupBox("Your Computer ID")
        hw_layout = QVBoxLayout()
        hw_label = QLabel(f"Hardware ID: {self.hardware_id}")
        hw_label.setStyleSheet("font-family: monospace; font-size: 13px; padding: 10px; background-color: #f8f9fa; border-radius: 5px;")
        hw_layout.addWidget(hw_label)
        hw_info = QLabel("Please provide this Hardware ID to your vendor to obtain a license key.")
        hw_info.setStyleSheet("font-size: 11px; color: #6c757d; margin-top: 5px;")
        hw_layout.addWidget(hw_info)
        hw_group.setLayout(hw_layout)
        layout.addWidget(hw_group)
        
        # License key input
        key_group = QGroupBox("Enter License Key")
        key_layout = QVBoxLayout()
        key_layout.setContentsMargins(10, 10, 10, 10)
        self.license_key_edit = QLineEdit()
        self.license_key_edit.setPlaceholderText("XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX")
        self.license_key_edit.setMinimumHeight(50)
        self.license_key_edit.setMaxLength(39)  # 32 chars + 7 dashes
        self.license_key_edit.setStyleSheet("""
            QLineEdit {
                padding: 15px;
                border: 2px solid #ced4da;
                border-radius: 6px;
                font-size: 15px;
                font-family: 'Courier New', monospace;
                letter-spacing: 1px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 3px solid #007bff;
                background-color: #f8f9ff;
            }
        """)
        self.license_key_edit.textChanged.connect(self.format_license_key)
        key_layout.addWidget(self.license_key_edit)
        key_group.setLayout(key_layout)
        layout.addWidget(key_group)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 11px; padding: 5px;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_activate = QPushButton("Activate")
        btn_activate.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 10px 30px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        btn_activate.clicked.connect(self.activate_license)
        
        btn_exit = QPushButton("Exit")
        btn_exit.setStyleSheet("background-color: #6c757d; color: white; padding: 10px 30px; border-radius: 5px; font-size: 13px;")
        btn_exit.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_exit)
        btn_layout.addWidget(btn_activate)
        layout.addLayout(btn_layout)
        
        # Layout is already set by base class, no need to set it again
    
    def format_license_key(self, text):
        """Format license key with dashes"""
        # Remove all non-alphanumeric characters
        clean = ''.join(c for c in text.upper() if c.isalnum())
        
        # Limit to 32 characters (8 groups of 4)
        if len(clean) > 32:
            clean = clean[:32]
        
        # Add dashes every 4 characters
        formatted = '-'.join([clean[i:i+4] for i in range(0, len(clean), 4)])
        
        # Result should be max 39 characters (32 chars + 7 dashes)
        if formatted != text:
            self.license_key_edit.blockSignals(True)
            self.license_key_edit.setText(formatted)
            self.license_key_edit.blockSignals(False)
    
    def activate_license(self):
        """Validate and activate the license"""
        from license_manager import LicenseManager
        
        license_key = self.license_key_edit.text().strip()
        
        if not license_key or len(license_key.replace('-', '')) < 32:
            self.status_label.setText("Please enter a valid license key")
            self.status_label.setStyleSheet("font-size: 11px; padding: 5px; color: #dc3545;")
            return
        
        license_manager = LicenseManager()
        is_valid, message = license_manager.validate_license_key(license_key)
        
        if is_valid:
            self.status_label.setText(message)
            self.status_label.setStyleSheet("font-size: 11px; padding: 5px; color: #28a745;")
            QMessageBox.information(self, "Success", message)
            self.accept()
        else:
            self.status_label.setText(message)
            self.status_label.setStyleSheet("font-size: 11px; padding: 5px; color: #dc3545;")

