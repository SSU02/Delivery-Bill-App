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
        QListWidget, QListWidgetItem
    )
    from PyQt5.QtCore import Qt, pyqtSignal
    from PyQt5.QtGui import QFont
    PYQT_VERSION = 5
    DIALOG_ACCEPTED = QDialog.Accepted
except ImportError:
    # Fallback to PyQt6
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QComboBox, QMessageBox, QTextEdit, QDoubleSpinBox,
        QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
        QListWidget, QListWidgetItem
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QFont
    PYQT_VERSION = 6
    DIALOG_ACCEPTED = QDialog.DialogCode.Accepted
from database import Database


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
        vehicle_no = self.vehicle_edit.text().strip()
        if not vehicle_no:
            QMessageBox.warning(self, "Error", "Vehicle number cannot be empty")
            return
        
        try:
            self.db.add_vehicle(vehicle_no)
            QMessageBox.information(self, "Success", "Vehicle added successfully")
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
            ("Address", "address"),
            ("SF.NO", "sf_no"),
            ("RC.NO", "rc_no"),
            ("State", "state"),
            ("GSTIN", "gstin")
        ]
        
        self.entries = {}
        for label, key in fields:
            row_layout = QHBoxLayout()
            row_layout.addWidget(QLabel(label))
            entry = QLineEdit()
            if customer:
                entry.setText(customer.get(key, ''))
            elif key == 'state':
                entry.setText('Tamilnadu')
            elif key == 'address' and area_id:
                # Get area name
                areas = db.get_locations()
                area = next((a for a in areas if a['id'] == area_id), None)
                if area:
                    entry.setText(area['name'])
            entry.setPlaceholderText(f"Enter {label.lower()}")
            self.entries[key] = entry
            row_layout.addWidget(entry)
            self.layout.addLayout(row_layout)
        
        # Blaster selection
        blaster_layout = QHBoxLayout()
        blaster_layout.addWidget(QLabel("Blaster:"))
        self.blaster_combo = QComboBox()
        blasters = db.get_blasters()
        self.blaster_combo.addItem("", None)
        for blaster in blasters:
            self.blaster_combo.addItem(blaster['name'], blaster['id'])
        
        if customer and customer.get('blaster_id'):
            index = self.blaster_combo.findData(customer['blaster_id'])
            if index >= 0:
                self.blaster_combo.setCurrentIndex(index)
        
        blaster_layout.addWidget(self.blaster_combo)
        btn_add_blaster = QPushButton("+ Add Blaster")
        btn_add_blaster.setStyleSheet("background-color: #28a745; color: white; padding: 5px 10px;")
        btn_add_blaster.clicked.connect(self.add_blaster)
        blaster_layout.addWidget(btn_add_blaster)
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
    
    def add_blaster(self):
        """Add a new blaster"""
        dialog = AddBlasterDialog(self, self.db)
        result = dialog.exec_() if PYQT_VERSION == 5 else dialog.exec()
        if result == DIALOG_ACCEPTED:
            # Refresh blaster combo
            self.blaster_combo.clear()
            self.blaster_combo.addItem("", None)
            blasters = self.db.get_blasters()
            for blaster in blasters:
                self.blaster_combo.addItem(blaster['name'], blaster['id'])
    
    def save(self):
        """Save the customer"""
        name = self.entries['name'].text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Customer name is required")
            return
        
        blaster_id = self.blaster_combo.currentData()
        
        try:
            if self.customer:
                # Update
                self.db.update_customer(
                    self.customer['id'],
                    name,
                    self.entries['address'].text().strip(),
                    self.entries['sf_no'].text().strip(),
                    self.entries['rc_no'].text().strip(),
                    self.entries['state'].text().strip(),
                    self.entries['gstin'].text().strip(),
                    blaster_id,
                    self.area_id
                )
                QMessageBox.information(self, "Success", "Customer updated successfully")
            else:
                # Add
                self.db.add_customer(
                    name,
                    self.entries['address'].text().strip(),
                    self.entries['sf_no'].text().strip(),
                    self.entries['rc_no'].text().strip(),
                    self.entries['state'].text().strip(),
                    self.entries['gstin'].text().strip(),
                    blaster_id,
                    self.area_id
                )
                QMessageBox.information(self, "Success", "Customer added successfully")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save customer: {str(e)}")


class AddBlasterDialog(ModernDialog):
    """Dialog for adding a blaster"""
    def __init__(self, parent=None, db=None):
        super().__init__("Add Blaster", parent)
        self.db = db
        
        # Name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name *:"))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        self.layout.addLayout(name_layout)
        
        # Document No
        doc_layout = QHBoxLayout()
        doc_layout.addWidget(QLabel("Document No:"))
        self.doc_edit = QLineEdit()
        doc_layout.addWidget(self.doc_edit)
        self.layout.addLayout(doc_layout)
        
        # Address
        address_layout = QVBoxLayout()
        address_layout.addWidget(QLabel("Address:"))
        self.address_edit = QTextEdit()
        self.address_edit.setMaximumHeight(80)
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
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Blaster name is required")
            return
        
        try:
            self.db.add_blaster(
                name,
                self.doc_edit.text().strip(),
                self.address_edit.toPlainText().strip()
            )
            QMessageBox.information(self, "Success", "Blaster added successfully")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to add blaster: {str(e)}")


class AddGoodDialog(ModernDialog):
    """Dialog for adding a good to customer"""
    def __init__(self, parent=None, db=None, default_cgst_rate=9.0, default_sgst_rate=9.0, category=None):
        super().__init__("Add Good to Customer", parent)
        self.db = db
        self.default_cgst_rate = default_cgst_rate
        self.default_sgst_rate = default_sgst_rate
        self.category = category
        self.item_data = None
        
        # Good selection (filtered by category)
        good_layout = QHBoxLayout()
        good_layout.addWidget(QLabel("Select Good:"))
        self.good_combo = QComboBox()
        goods = db.get_goods(category=category) if category else db.get_goods()
        self.good_combo.addItem("", None)
        for good in goods:
            self.good_combo.addItem(f"{good['description']} ({good['hsn_code']})", good)
        self.good_combo.currentIndexChanged.connect(self.on_good_selected)
        good_layout.addWidget(self.good_combo)
        btn_new_good = QPushButton("+ New Good")
        btn_new_good.setStyleSheet("background-color: #28a745; color: white; padding: 5px 10px;")
        btn_new_good.clicked.connect(self.add_new_good)
        good_layout.addWidget(btn_new_good)
        self.layout.addLayout(good_layout)
        
        # Tax rate editing
        tax_layout = QHBoxLayout()
        tax_layout.addWidget(QLabel("CGST Rate %:"))
        self.cgst_spin = QDoubleSpinBox()
        self.cgst_spin.setMinimum(0)
        self.cgst_spin.setMaximum(100)
        self.cgst_spin.setValue(default_cgst_rate)
        self.cgst_spin.setDecimals(2)
        self.cgst_spin.valueChanged.connect(self.calculate)
        tax_layout.addWidget(self.cgst_spin)
        
        tax_layout.addWidget(QLabel("SGST Rate %:"))
        self.sgst_spin = QDoubleSpinBox()
        self.sgst_spin.setMinimum(0)
        self.sgst_spin.setMaximum(100)
        self.sgst_spin.setValue(default_sgst_rate)
        self.sgst_spin.setDecimals(2)
        self.sgst_spin.valueChanged.connect(self.calculate)
        tax_layout.addWidget(self.sgst_spin)
        self.layout.addLayout(tax_layout)
        
        # Quantity
        qty_layout = QHBoxLayout()
        qty_layout.addWidget(QLabel("Quantity:"))
        self.qty_spin = QDoubleSpinBox()
        self.qty_spin.setMinimum(0.01)
        self.qty_spin.setMaximum(999999)
        self.qty_spin.setValue(1.0)
        self.qty_spin.setDecimals(2)
        self.qty_spin.valueChanged.connect(self.calculate)
        qty_layout.addWidget(self.qty_spin)
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
        cgst_rs = (taxable_value * cgst_rate) / 100
        sgst_rs = (taxable_value * sgst_rate) / 100
        total_amount = total + cgst_rs + sgst_rs
        
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
            self.good_combo.addItem("", None)
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
        cgst_rs = (taxable_value * cgst_rate) / 100
        sgst_rs = (taxable_value * sgst_rate) / 100
        total_amount = total + cgst_rs + sgst_rs
        
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
            'igst_rate': 0,
            'igst_rs': 0,
            'total_amount': total_amount
        }
        
        self.accept()


class NewGoodDialog(ModernDialog):
    """Dialog for adding a new good"""
    def __init__(self, parent=None, db=None, category=None):
        super().__init__("Add New Good", parent)
        self.db = db
        self.category = category
        
        # Description
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Description *:"))
        self.desc_edit = QLineEdit()
        desc_layout.addWidget(self.desc_edit)
        self.layout.addLayout(desc_layout)
        
        # HSN Code
        hsn_layout = QHBoxLayout()
        hsn_layout.addWidget(QLabel("HSN Code *:"))
        self.hsn_edit = QLineEdit()
        hsn_layout.addWidget(self.hsn_edit)
        self.layout.addLayout(hsn_layout)
        
        # Unit
        unit_layout = QHBoxLayout()
        unit_layout.addWidget(QLabel("Unit *:"))
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(['NOS', 'KG'])
        unit_layout.addWidget(self.unit_combo)
        self.layout.addLayout(unit_layout)
        
        # Category (if provided)
        if category:
            category_layout = QHBoxLayout()
            category_layout.addWidget(QLabel("Category:"))
            category_label = QLabel(category)
            category_label.setStyleSheet("font-weight: bold; color: #007bff;")
            category_layout.addWidget(category_label)
            category_layout.addStretch()
            self.layout.addLayout(category_layout)
        
        # Rate
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(QLabel("Rate *:"))
        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setMinimum(0.01)
        self.rate_spin.setMaximum(999999)
        self.rate_spin.setDecimals(2)
        rate_layout.addWidget(self.rate_spin)
        self.layout.addLayout(rate_layout)
        
        # Buttons
        btn_save = QPushButton("Save")
        btn_save.setStyleSheet("background-color: #007bff; color: white;")
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("background-color: #6c757d; color: white;")
        btn_save.clicked.connect(self.save)
        btn_cancel.clicked.connect(self.reject)
        self.add_button_row([btn_cancel, btn_save])
        
        self.desc_edit.setFocus()
    
    def save(self):
        """Save the good"""
        description = self.desc_edit.text().strip()
        hsn_code = self.hsn_edit.text().strip()
        unit = self.unit_combo.currentText()
        rate = self.rate_spin.value()
        
        if not description:
            QMessageBox.warning(self, "Error", "Description is required")
            return
        
        if not hsn_code:
            QMessageBox.warning(self, "Error", "HSN Code is required")
            return
        
        try:
            self.db.add_good(description, hsn_code, unit, rate, self.category)
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
        self.setMinimumWidth(600)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
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
        self.license_key_edit = QLineEdit()
        self.license_key_edit.setPlaceholderText("XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX")
        self.license_key_edit.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #ced4da;
                border-radius: 5px;
                font-size: 14px;
                font-family: monospace;
                letter-spacing: 2px;
            }
            QLineEdit:focus {
                border: 2px solid #007bff;
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
        
        self.setLayout(layout)
    
    def format_license_key(self, text):
        """Format license key with dashes"""
        # Remove all non-alphanumeric characters
        clean = ''.join(c for c in text.upper() if c.isalnum())
        
        # Add dashes every 4 characters
        formatted = '-'.join([clean[i:i+4] for i in range(0, len(clean), 4)])
        
        # Limit to 35 characters (8 groups of 4 + 7 dashes)
        if len(formatted) > 35:
            formatted = formatted[:35]
        
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

