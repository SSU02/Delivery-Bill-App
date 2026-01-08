"""
Goods Management Dialog for Modern UI
Allows editing, deleting, and managing goods with category filtering
"""
try:
    from PyQt5.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QComboBox, QMessageBox, QTableWidget, QTableWidgetItem,
        QHeaderView, QGroupBox, QDoubleSpinBox, QListWidget, QListWidgetItem,
        QInputDialog, QListView
    )
    from PyQt5.QtCore import Qt, QEvent
    from PyQt5.QtGui import QWheelEvent
    PYQT_VERSION = 5
    DIALOG_ACCEPTED = QDialog.Accepted
except ImportError:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QComboBox, QMessageBox, QTableWidget, QTableWidgetItem,
        QHeaderView, QGroupBox, QDoubleSpinBox, QListWidget, QListWidgetItem,
        QInputDialog, QListView
    )
    from PyQt6.QtCore import Qt, QEvent
    from PyQt6.QtGui import QWheelEvent
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
        # Convert to uppercase as user types
        self.desc_edit.textChanged.connect(lambda text: self.desc_edit.setText(text.upper()))
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
        # Convert to uppercase as user types
        self.hsn_edit.textChanged.connect(lambda text: self.hsn_edit.setText(text.upper()))
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
        # Set current unit if it exists
        current_unit = good.get('unit', '')
        if current_unit:
            index = self.unit_combo.findText(current_unit)
            if index >= 0:
                self.unit_combo.setCurrentIndex(index)
            else:
                # If unit not found, keep "--Select Unit--" selected
                self.unit_combo.setCurrentIndex(0)
        else:
            # No unit set, show "--Select Unit--"
            self.unit_combo.setCurrentIndex(0)
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
        from dialogs_modern import AddUnitDialog
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
        from dialogs_modern import AddUnitDialog
        
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

