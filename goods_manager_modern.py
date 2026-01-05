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
    from PyQt5.QtCore import Qt
    PYQT_VERSION = 5
    DIALOG_ACCEPTED = QDialog.Accepted
except ImportError:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QComboBox, QMessageBox, QTableWidget, QTableWidgetItem,
        QHeaderView, QGroupBox, QDoubleSpinBox
    )
    from PyQt6.QtCore import Qt
    PYQT_VERSION = 6
    DIALOG_ACCEPTED = QDialog.DialogCode.Accepted

from database import Database


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
        self.category_filter = QComboBox()
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
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Description", "HSN Code", "Unit", "Rate", "Category"
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
            self.table.setItem(row, 0, QTableWidgetItem(str(good.get('id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(good.get('description', '')))
            self.table.setItem(row, 2, QTableWidgetItem(good.get('hsn_code', '')))
            self.table.setItem(row, 3, QTableWidgetItem(good.get('unit', '')))
            self.table.setItem(row, 4, QTableWidgetItem(f"{good.get('rate', 0):.2f}"))
            self.table.setItem(row, 5, QTableWidgetItem(good.get('category', '') or 'N/A'))
    
    def get_selected_good(self):
        """Get the selected good from table"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return None
        
        good_id = int(self.table.item(current_row, 0).text())
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
    """Dialog for editing a good"""
    def __init__(self, parent=None, db=None, good=None):
        super().__init__(parent)
        self.db = db
        self.good = good
        self.setWindowTitle("Edit Good")
        self.setMinimumWidth(500)
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
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Description
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Description *:"))
        self.desc_edit = QLineEdit(good.get('description', ''))
        desc_layout.addWidget(self.desc_edit)
        layout.addLayout(desc_layout)
        
        # HSN Code
        hsn_layout = QHBoxLayout()
        hsn_layout.addWidget(QLabel("HSN Code *:"))
        self.hsn_edit = QLineEdit(good.get('hsn_code', ''))
        hsn_layout.addWidget(self.hsn_edit)
        layout.addLayout(hsn_layout)
        
        # Unit
        unit_layout = QHBoxLayout()
        unit_layout.addWidget(QLabel("Unit *:"))
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(['NOS', 'KG'])
        self.unit_combo.setCurrentText(good.get('unit', 'NOS'))
        unit_layout.addWidget(self.unit_combo)
        layout.addLayout(unit_layout)
        
        # Category
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("", None)
        self.category_combo.addItem("Detonator", "Detonator")
        self.category_combo.addItem("Explosives", "Explosives")
        current_category = good.get('category', '')
        if current_category:
            index = self.category_combo.findData(current_category)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
        category_layout.addWidget(self.category_combo)
        layout.addLayout(category_layout)
        
        # Rate
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(QLabel("Rate *:"))
        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setMinimum(0.01)
        self.rate_spin.setMaximum(999999)
        self.rate_spin.setDecimals(2)
        self.rate_spin.setValue(good.get('rate', 0))
        rate_layout.addWidget(self.rate_spin)
        layout.addLayout(rate_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_save = QPushButton("Save")
        btn_save.setStyleSheet("background-color: #007bff; color: white;")
        btn_save.clicked.connect(self.save)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("background-color: #6c757d; color: white;")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)
    
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

