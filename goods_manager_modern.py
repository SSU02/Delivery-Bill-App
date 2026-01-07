"""
Goods Management Dialog for Modern UI
Allows editing, deleting, and managing goods with category filtering
"""
try:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QComboBox, QMessageBox, QTableWidget, QTableWidgetItem,
        QHeaderView, QGroupBox, QDoubleSpinBox
    )
    from PyQt5.QtCore import Qt, QEvent
    from PyQt5.QtGui import QWheelEvent
    PYQT_VERSION = 5
    DIALOG_ACCEPTED = QDialog.Accepted
except ImportError:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QComboBox, QMessageBox, QTableWidget, QTableWidgetItem,
        QHeaderView, QGroupBox, QDoubleSpinBox
    )
    from PyQt6.QtCore import Qt, QEvent
    from PyQt6.QtGui import QWheelEvent
    PYQT_VERSION = 6
    DIALOG_ACCEPTED = QDialog.DialogCode.Accepted

from database import Database


class NoWheelComboBox(QComboBox):
    """QComboBox that only responds to wheel events when focused/clicked"""
    def wheelEvent(self, event: QWheelEvent):
        # Only process wheel events if the combo box is focused
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            # Ignore wheel events when not focused
            event.ignore()


class GoodsManagerDialog(QDialog):
    """Dialog for managing goods"""
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Manage Goods")
        self.setMinimumSize(900, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: #212529;
                font-size: 12px;
            }
            QLineEdit, QComboBox, QDoubleSpinBox {
                padding: 8px;
                border: 2px solid #ced4da;
                border-radius: 4px;
                font-size: 12px;
                background-color: white;
                color: #212529;
            }
            QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #007bff;
            }
            QPushButton {
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QTableWidget {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                background-color: white;
                gridline-color: #dee2e6;
            }
            QHeaderView::section {
                background-color: #007bff;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Filter by category
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Category:"))
        self.category_filter = NoWheelComboBox()
        self.category_filter.addItem("All Goods", None)
        self.category_filter.addItem("Detonator", "Detonator")
        self.category_filter.addItem("Explosives", "Explosives")
        self.category_filter.currentIndexChanged.connect(self.refresh_table)
        filter_layout.addWidget(self.category_filter)
        filter_layout.addStretch()
        
        # Buttons
        btn_add = QPushButton("+ Add Good")
        btn_add.setStyleSheet("background-color: #28a745; color: white;")
        btn_add.clicked.connect(self.add_good)
        btn_edit = QPushButton("Edit Selected")
        btn_edit.setStyleSheet("background-color: #007bff; color: white;")
        btn_edit.clicked.connect(self.edit_good)
        btn_delete = QPushButton("Delete Selected")
        btn_delete.setStyleSheet("background-color: #dc3545; color: white;")
        btn_delete.clicked.connect(self.delete_good)
        filter_layout.addWidget(btn_add)
        filter_layout.addWidget(btn_edit)
        filter_layout.addWidget(btn_delete)
        layout.addLayout(filter_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Description", "HSN Code", "Unit", "Rate", "Category"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        # Close button
        btn_close = QPushButton("Close")
        btn_close.setStyleSheet("background-color: #6c757d; color: white;")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
        
        self.refresh_table()
    
    def refresh_table(self):
        """Refresh the goods table"""
        category = self.category_filter.currentData()
        goods = self.db.get_goods(category=category) if category else self.db.get_goods()
        
        self.table.setRowCount(len(goods))
        for row, good in enumerate(goods):
            # Store good ID in the first item's data
            desc_item = QTableWidgetItem(good.get('description', ''))
            if PYQT_VERSION == 6:
                desc_item.setData(Qt.ItemDataRole.UserRole, good.get('id'))
            else:
                desc_item.setData(Qt.UserRole, good.get('id'))
            self.table.setItem(row, 0, desc_item)
            self.table.setItem(row, 1, QTableWidgetItem(good.get('hsn_code', '')))
            self.table.setItem(row, 2, QTableWidgetItem(good.get('unit', '')))
            self.table.setItem(row, 3, QTableWidgetItem(f"{good.get('rate', 0):.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(good.get('category', '') or 'N/A'))
    
    def get_selected_good(self):
        """Get the selected good from table"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return None
        
        # Get good ID from the first item's data
        desc_item = self.table.item(current_row, 0)
        if not desc_item:
            return None
        
        if PYQT_VERSION == 6:
            good_id = desc_item.data(Qt.ItemDataRole.UserRole)
        else:
            good_id = desc_item.data(Qt.UserRole)
        if good_id is None:
            return None
        
        return self.db.get_good(good_id)
    
    def add_good(self):
        """Add a new good"""
        from dialogs_modern import NewGoodDialog
        category = self.category_filter.currentData()
        dialog = NewGoodDialog(self, self.db, category=category)
        result = dialog.exec_() if PYQT_VERSION == 5 else dialog.exec()
        if result == DIALOG_ACCEPTED:
            self.refresh_table()
    
    def edit_good(self):
        """Edit selected good"""
        good = self.get_selected_good()
        if not good:
            QMessageBox.warning(self, "Warning", "Please select a good to edit")
            return
        
        dialog = EditGoodDialog(self, self.db, good)
        result = dialog.exec_() if PYQT_VERSION == 5 else dialog.exec()
        if result == DIALOG_ACCEPTED:
            self.refresh_table()
    
    def delete_good(self):
        """Delete selected good"""
        good = self.get_selected_good()
        if not good:
            QMessageBox.warning(self, "Warning", "Please select a good to delete")
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete '{good['description']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.delete_good(good['id'])
                QMessageBox.information(self, "Success", "Good deleted successfully")
                self.refresh_table()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete good: {str(e)}")


class EditGoodDialog(QDialog):
    """Dialog for editing a good - matches NewGoodDialog layout"""
    def __init__(self, parent=None, db=None, good=None):
        super().__init__(parent)
        self.db = db
        self.good = good
        self.setWindowTitle("Edit Good")
        self.setMinimumWidth(500)
        
        # Use same styling as ModernDialog
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
            QLineEdit, QComboBox, QDoubleSpinBox {
                padding: 8px;
                border: 2px solid #ced4da;
                border-radius: 4px;
                font-size: 12px;
                background-color: white;
                color: #212529;
                selection-background-color: #007bff;
                selection-color: white;
            }
            QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
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
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Uniform field width (same as NewGoodDialog)
        field_width = 250
        
        # Description
        desc_layout = QHBoxLayout()
        desc_label = QLabel("Description *:")
        desc_label.setMinimumWidth(100)
        desc_layout.addWidget(desc_label)
        self.desc_edit = QLineEdit(good.get('description', ''))
        self.desc_edit.setMinimumWidth(field_width)
        self.desc_edit.setMaximumWidth(field_width)
        desc_layout.addWidget(self.desc_edit)
        desc_layout.addStretch()
        layout.addLayout(desc_layout)
        
        # Category dropdown - same style as NewGoodDialog
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
        # Exact same styling as NewGoodDialog
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
        current_category = good.get('category', '')
        if current_category:
            index = self.category_combo.findData(current_category)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
        category_layout.addWidget(self.category_combo)
        category_layout.addStretch()
        layout.addLayout(category_layout)
        
        # HSN Code
        hsn_layout = QHBoxLayout()
        hsn_label = QLabel("HSN Code *:")
        hsn_label.setMinimumWidth(100)
        hsn_layout.addWidget(hsn_label)
        self.hsn_edit = QLineEdit(good.get('hsn_code', ''))
        self.hsn_edit.setMinimumWidth(field_width)
        self.hsn_edit.setMaximumWidth(field_width)
        hsn_layout.addWidget(self.hsn_edit)
        hsn_layout.addStretch()
        layout.addLayout(hsn_layout)
        
        # Rate 
        rate_layout = QHBoxLayout()
        rate_label = QLabel("Rate *:")
        rate_label.setMinimumWidth(100)
        rate_layout.addWidget(rate_label)
        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setMinimum(0.01)
        self.rate_spin.setMaximum(999999)
        self.rate_spin.setDecimals(2)
        self.rate_spin.setValue(good.get('rate', 0))
        self.rate_spin.setMinimumWidth(field_width)
        self.rate_spin.setMaximumWidth(field_width)
        # Same styling as NewGoodDialog
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
        layout.addLayout(rate_layout)
        
        # Unit
        unit_layout = QHBoxLayout()
        unit_label = QLabel("Unit *:")
        unit_label.setMinimumWidth(100)
        unit_layout.addWidget(unit_label)
        self.unit_combo = NoWheelComboBox()
        self.unit_combo.addItems(['NOS', 'KG'])
        self.unit_combo.setCurrentText(good.get('unit', 'NOS'))
        self.unit_combo.setMinimumWidth(field_width)
        self.unit_combo.setMaximumWidth(field_width)
        # Simplified Unit Style
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
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px; 
                border-left: 1px solid #ced4da;
                background-color: #f8f9fa;
            }
            /* DELETE the QComboBox::down-arrow block entirely */
        """)
        unit_layout.addWidget(self.unit_combo)
        unit_layout.addStretch()
        layout.addLayout(unit_layout)
        
        # Buttons (same order as NewGoodDialog: Cancel, Save)
        btn_save = QPushButton("Save")
        btn_save.setStyleSheet("background-color: #007bff; color: white;")
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("background-color: #6c757d; color: white;")
        btn_save.clicked.connect(self.save)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)
        
        self.desc_edit.setFocus()
    
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
        
        try:
            self.db.update_good(
                self.good['id'],
                description,
                hsn_code,
                unit,
                rate,
                category
            )
            QMessageBox.information(self, "Success", "Good updated successfully")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to update good: {str(e)}")

