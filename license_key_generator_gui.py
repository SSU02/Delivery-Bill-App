#!/usr/bin/env python3
"""
Professional License Key Generator GUI
Clean, spacious design that actually works
"""
import sys
# Try PyQt5 first, fallback to PyQt6
try:
    from PyQt5.QtWidgets import (
        QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
        QLineEdit, QPushButton, QTextEdit, QSpinBox, QMessageBox,
        QGroupBox, QGridLayout, QScrollArea, QWidget
    )
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont, QPalette, QColor
    PYQT_VERSION = 5
except ImportError:
    from PyQt6.QtWidgets import (
        QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
        QLineEdit, QPushButton, QTextEdit, QSpinBox, QMessageBox,
        QGroupBox, QGridLayout, QScrollArea, QWidget
    )
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont, QPalette, QColor
    PYQT_VERSION = 6

from license_manager import generate_license_for_client


class LicenseKeyGeneratorGUI(QDialog):
    """Professional GUI for generating license keys"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("License Key Generator")
        self.setMinimumWidth(750)
        self.setMinimumHeight(800)
        self.resize(850, 900)
        self.setup_ui()
    
    def setup_ui(self):
        # Create scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        # Main widget
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        title = QLabel("🔑 License Key Generator")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #212529;
            padding: 15px 0px;
        """)
        main_layout.addWidget(title)
        
        subtitle = QLabel("Generate license keys for your clients")
        subtitle.setStyleSheet("font-size: 13px; color: #6c757d; padding-bottom: 20px;")
        main_layout.addWidget(subtitle)
        
        # Hardware ID Section
        hw_group = QGroupBox("Client Hardware ID")
        hw_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #212529;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        hw_layout = QVBoxLayout()
        hw_layout.setSpacing(12)
        hw_layout.setContentsMargins(15, 20, 15, 15)
        
        hw_info = QLabel("Enter the Hardware ID provided by your client:")
        hw_info.setStyleSheet("font-size: 12px; color: #6c757d;")
        hw_layout.addWidget(hw_info)
        
        self.hardware_id_edit = QLineEdit()
        self.hardware_id_edit.setPlaceholderText("Enter Hardware ID (e.g., 00952C7AD8723027)")
        self.hardware_id_edit.setMinimumHeight(45)
        self.hardware_id_edit.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                border: 2px solid #ced4da;
                border-radius: 6px;
                font-size: 14px;
                font-family: monospace;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #007bff;
            }
        """)
        hw_layout.addWidget(self.hardware_id_edit)
        hw_group.setLayout(hw_layout)
        main_layout.addWidget(hw_group)
        
        # License Period Section
        period_group = QGroupBox("License Period")
        period_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #212529;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        period_layout = QVBoxLayout()
        period_layout.setSpacing(15)
        period_layout.setContentsMargins(15, 20, 15, 15)
        
        period_info = QLabel("Select a license period:")
        period_info.setStyleSheet("font-size: 12px; color: #6c757d; padding-bottom: 10px;")
        period_layout.addWidget(period_info)
        
        # Preset buttons - 3 columns
        preset_grid = QGridLayout()
        preset_grid.setSpacing(10)
        
        presets = [
            ("Trial\n30 days", 30, False),
            ("Monthly\n30 days", 30, False),
            ("Quarterly\n90 days", 90, False),
            ("6 Months\n180 days", 180, False),
            ("1 Year\n365 days", 365, False),
            ("2 Years\n730 days", 730, False),
            ("5 Years\n1825 days", 1825, False),
            ("Lifetime\n10 years", 3650, False),
            ("🌟 Forever", 0, True),
        ]
        
        self.preset_buttons = []
        self.forever_mode = False
        
        for idx, (label, days, forever) in enumerate(presets):
            btn = QPushButton(label)
            btn.setMinimumHeight(60)
            btn.setMinimumWidth(150)
            
            if forever:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ffc107;
                        color: #212529;
                        border: 2px solid #ff9800;
                        border-radius: 6px;
                        font-size: 12px;
                        font-weight: bold;
                        padding: 8px;
                    }
                    QPushButton:hover {
                        background-color: #ffb300;
                    }
                    QPushButton:pressed {
                        background-color: #ffa000;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #f8f9fa;
                        color: #212529;
                        border: 2px solid #dee2e6;
                        border-radius: 6px;
                        font-size: 12px;
                        padding: 8px;
                    }
                    QPushButton:hover {
                        background-color: #e9ecef;
                        border: 2px solid #007bff;
                    }
                    QPushButton:pressed {
                        background-color: #007bff;
                        color: white;
                    }
                """)
            
            if forever:
                btn.clicked.connect(lambda checked: self.set_forever())
            else:
                btn.clicked.connect(lambda checked, d=days: self.set_days(d))
            
            preset_grid.addWidget(btn, idx // 3, idx % 3)
            self.preset_buttons.append(btn)
        
        period_layout.addLayout(preset_grid)
        
        # Custom days
        custom_layout = QHBoxLayout()
        custom_layout.setSpacing(12)
        
        custom_label = QLabel("Custom Days:")
        custom_label.setStyleSheet("font-size: 13px; font-weight: bold; min-width: 100px;")
        custom_layout.addWidget(custom_label)
        
        self.days_spinbox = QSpinBox()
        self.days_spinbox.setMinimum(1)
        self.days_spinbox.setMaximum(36500)
        self.days_spinbox.setValue(365)
        self.days_spinbox.setMinimumHeight(40)
        self.days_spinbox.setMinimumWidth(120)
        self.days_spinbox.setStyleSheet("""
            QSpinBox {
                padding: 8px;
                border: 2px solid #ced4da;
                border-radius: 6px;
                font-size: 13px;
            }
            QSpinBox:focus {
                border: 2px solid #007bff;
            }
        """)
        custom_layout.addWidget(self.days_spinbox)
        
        self.expiry_preview = QLabel("")
        self.expiry_preview.setStyleSheet("""
            font-size: 12px;
            color: #28a745;
            font-weight: 500;
            padding: 8px 12px;
            background-color: #d4edda;
            border-radius: 4px;
        """)
        custom_layout.addWidget(self.expiry_preview)
        custom_layout.addStretch()
        
        self.days_spinbox.valueChanged.connect(self.on_days_changed)
        self.update_expiry_preview()
        
        period_layout.addLayout(custom_layout)
        period_group.setLayout(period_layout)
        main_layout.addWidget(period_group)
        
        # Generate Button
        btn_generate = QPushButton("✨ Generate License Key")
        btn_generate.setMinimumHeight(55)
        btn_generate.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        btn_generate.clicked.connect(self.generate_key)
        main_layout.addWidget(btn_generate)
        
        # Result Section
        result_group = QGroupBox("Generated License Key")
        result_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #212529;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        result_layout = QVBoxLayout()
        result_layout.setSpacing(12)
        result_layout.setContentsMargins(15, 20, 15, 15)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMinimumHeight(150)
        self.result_text.setStyleSheet("""
            QTextEdit {
                padding: 15px;
                border: 2px solid #ced4da;
                border-radius: 6px;
                font-size: 13px;
                font-family: monospace;
                background-color: #f8f9fa;
            }
        """)
        result_layout.addWidget(self.result_text)
        
        # Copy button
        btn_copy = QPushButton("📋 Copy License Key")
        btn_copy.setMinimumHeight(45)
        btn_copy.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        btn_copy.clicked.connect(self.copy_to_clipboard)
        result_layout.addWidget(btn_copy)
        
        result_group.setLayout(result_layout)
        main_layout.addWidget(result_group)
        
        main_layout.addStretch()
        main_widget.setLayout(main_layout)
        scroll.setWidget(main_widget)
        
        # Dialog layout
        dialog_layout = QVBoxLayout()
        dialog_layout.setContentsMargins(0, 0, 0, 0)
        dialog_layout.addWidget(scroll)
        self.setLayout(dialog_layout)
    
    def on_days_changed(self):
        """Reset forever mode when days are manually changed"""
        self.forever_mode = False
        self.update_expiry_preview()
    
    def set_days(self, days):
        """Set days from preset button"""
        self.forever_mode = False
        self.days_spinbox.setValue(days)
        self.update_expiry_preview()
    
    def set_forever(self):
        """Set forever license mode"""
        self.forever_mode = True
        self.update_expiry_preview()
    
    def update_expiry_preview(self):
        """Update the expiry date preview"""
        if self.forever_mode:
            self.expiry_preview.setText("🌟 FOREVER - Never expires!")
            self.expiry_preview.setStyleSheet("""
                font-size: 12px;
                color: #ff9800;
                font-weight: bold;
                padding: 8px 12px;
                background-color: #fff3cd;
                border-radius: 4px;
            """)
            return
        
        from datetime import datetime, timedelta
        days = self.days_spinbox.value()
        expiry_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        
        years = days // 365
        months = (days % 365) // 30
        
        if years > 0:
            preview_text = f"Expires: {expiry_date} (~{years} year{'s' if years > 1 else ''})"
        elif months > 0:
            preview_text = f"Expires: {expiry_date} (~{months} month{'s' if months > 1 else ''})"
        else:
            preview_text = f"Expires: {expiry_date} ({days} days)"
        
        self.expiry_preview.setText(preview_text)
        self.expiry_preview.setStyleSheet("""
            font-size: 12px;
            color: #28a745;
            font-weight: 500;
            padding: 8px 12px;
            background-color: #d4edda;
            border-radius: 4px;
        """)
    
    def generate_key(self):
        """Generate license key for the entered hardware ID"""
        hardware_id = self.hardware_id_edit.text().strip().upper()
        
        if not hardware_id:
            QMessageBox.warning(self, "Error", "Please enter a Hardware ID")
            return
        
        if len(hardware_id) < 8:
            QMessageBox.warning(self, "Error", "Hardware ID seems too short. Please check and try again.")
            return
        
        days_valid = self.days_spinbox.value()
        forever = self.forever_mode
        
        try:
            license_key, license_data = generate_license_for_client(hardware_id, days_valid, forever)
            
            # Format result
            if license_data.get('forever', False):
                result = f"""✅ License Key Generated Successfully!

Hardware ID: {license_data['hardware_id']}

License Key: {license_key}

Type: 🌟 FOREVER LICENSE (Never expires!)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Copy the License Key above and send it to your client.
"""
            else:
                result = f"""✅ License Key Generated Successfully!

Hardware ID: {license_data['hardware_id']}

License Key: {license_key}

Valid Until: {license_data['expiry_date']}
Days Valid: {license_data['days_valid']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Copy the License Key above and send it to your client.
"""
            
            self.result_text.setText(result)
            self.generated_license_key = license_key
            
            QMessageBox.information(self, "Success", "License key generated successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate license key:\n{str(e)}")
    
    def copy_to_clipboard(self):
        """Copy the generated license key to clipboard"""
        if hasattr(self, 'generated_license_key'):
            clipboard = QApplication.clipboard()
            clipboard.setText(self.generated_license_key)
            QMessageBox.information(self, "Copied", "License key copied to clipboard!")
        else:
            QMessageBox.warning(self, "No Key", "Please generate a license key first")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = LicenseKeyGeneratorGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
