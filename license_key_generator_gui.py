#!/usr/bin/env python3
"""
Simple GUI tool to generate license keys for clients
"""
import sys
# Try PyQt5 first, fallback to PyQt6
try:
    from PyQt5.QtWidgets import (
        QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
        QLineEdit, QPushButton, QTextEdit, QSpinBox, QMessageBox,
        QGroupBox, QGridLayout
    )
    from PyQt5.QtCore import Qt
    PYQT_VERSION = 5
except ImportError:
    from PyQt6.QtWidgets import (
        QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
        QLineEdit, QPushButton, QTextEdit, QSpinBox, QMessageBox,
        QGroupBox, QGridLayout
    )
    from PyQt6.QtCore import Qt
    PYQT_VERSION = 6

from license_manager import generate_license_for_client


class LicenseKeyGeneratorGUI(QDialog):
    """Simple GUI for generating license keys"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("License Key Generator")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("License Key Generator")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #212529; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Hardware ID input
        hw_label = QLabel("Client Hardware ID:")
        hw_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(hw_label)
        
        self.hardware_id_edit = QLineEdit()
        self.hardware_id_edit.setPlaceholderText("Enter Hardware ID (e.g., 00952C7AD8723027)")
        self.hardware_id_edit.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #ced4da;
                border-radius: 5px;
                font-size: 13px;
                font-family: monospace;
            }
            QLineEdit:focus {
                border: 2px solid #007bff;
            }
        """)
        layout.addWidget(self.hardware_id_edit)
        
        # License Period Presets
        preset_group = QGroupBox("License Period (Quick Select)")
        preset_layout = QGridLayout()
        preset_layout.setSpacing(8)
        
        # Define presets: (label, days, forever)
        presets = [
            ("Trial (30 days)", 30, False),
            ("Monthly (30 days)", 30, False),
            ("Quarterly (90 days)", 90, False),
            ("6 Months (180 days)", 180, False),
            ("1 Year (365 days)", 365, False),
            ("2 Years (730 days)", 730, False),
            ("5 Years (1825 days)", 1825, False),
            ("Lifetime (10 years)", 3650, False),
            ("🌟 Forever (Never expires)", 0, True),
        ]
        
        self.preset_buttons = []
        self.forever_mode = False
        for idx, (label, days, forever) in enumerate(presets):
            btn = QPushButton(label)
            if forever:
                # Special styling for Forever button
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #ffc107;
                        color: #212529;
                        padding: 8px 12px;
                        border: 2px solid #ff9800;
                        border-radius: 4px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #ffb300;
                        border: 2px solid #f57c00;
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
                        padding: 8px 12px;
                        border: 1px solid #dee2e6;
                        border-radius: 4px;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #e9ecef;
                        border: 1px solid #007bff;
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
            preset_layout.addWidget(btn, idx // 4, idx % 4)
            self.preset_buttons.append(btn)
        
        preset_group.setLayout(preset_layout)
        layout.addWidget(preset_group)
        
        # Custom Days Valid
        days_layout = QHBoxLayout()
        days_label = QLabel("Custom Days (or use presets above):")
        days_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        days_layout.addWidget(days_label)
        
        self.days_spinbox = QSpinBox()
        self.days_spinbox.setMinimum(1)
        self.days_spinbox.setMaximum(36500)  # Up to 100 years
        self.days_spinbox.setValue(365)
        self.days_spinbox.setStyleSheet("""
            QSpinBox {
                padding: 8px;
                border: 2px solid #ced4da;
                border-radius: 5px;
                font-size: 12px;
            }
            QSpinBox:focus {
                border: 2px solid #007bff;
            }
        """)
        days_layout.addWidget(self.days_spinbox)
        
        # Show expiry date preview
        self.expiry_preview = QLabel("")
        self.expiry_preview.setStyleSheet("font-size: 11px; color: #6c757d; font-style: italic;")
        days_layout.addWidget(self.expiry_preview)
        days_layout.addStretch()
        
        # Update preview when days change
        self.days_spinbox.valueChanged.connect(self.on_days_changed)
        self.update_expiry_preview()
        
        layout.addLayout(days_layout)
        
        # Generate button
        btn_generate = QPushButton("Generate License Key")
        btn_generate.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 12px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        btn_generate.clicked.connect(self.generate_key)
        layout.addWidget(btn_generate)
        
        # Result display
        result_label = QLabel("Generated License Key:")
        result_label.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 10px;")
        layout.addWidget(result_label)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMinimumHeight(150)
        self.result_text.setStyleSheet("""
            QTextEdit {
                padding: 10px;
                border: 2px solid #ced4da;
                border-radius: 5px;
                font-size: 12px;
                font-family: monospace;
                background-color: #f8f9fa;
            }
        """)
        layout.addWidget(self.result_text)
        
        # Copy button
        btn_copy = QPushButton("Copy License Key")
        btn_copy.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        btn_copy.clicked.connect(self.copy_to_clipboard)
        layout.addWidget(btn_copy)
        
        self.setLayout(layout)
    
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
        self.expiry_preview.setText("🌟 FOREVER LICENSE - Never expires!")
        self.expiry_preview.setStyleSheet("font-size: 11px; color: #ff9800; font-weight: bold; font-style: italic;")
    
    def update_expiry_preview(self):
        """Update the expiry date preview"""
        if self.forever_mode:
            self.expiry_preview.setText("🌟 FOREVER LICENSE - Never expires!")
            self.expiry_preview.setStyleSheet("font-size: 11px; color: #ff9800; font-weight: bold; font-style: italic;")
            return
        
        from datetime import datetime, timedelta
        days = self.days_spinbox.value()
        expiry_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Calculate years/months for display
        years = days // 365
        months = (days % 365) // 30
        
        if years > 0:
            preview_text = f"Expires: {expiry_date} (~{years} year{'s' if years > 1 else ''})"
        elif months > 0:
            preview_text = f"Expires: {expiry_date} (~{months} month{'s' if months > 1 else ''})"
        else:
            preview_text = f"Expires: {expiry_date} ({days} day{'s' if days > 1 else ''})"
        
        self.expiry_preview.setText(preview_text)
        self.expiry_preview.setStyleSheet("font-size: 11px; color: #6c757d; font-style: italic;")
    
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
                result = f"""License Key Generated Successfully!

Hardware ID: {license_data['hardware_id']}
License Key: {license_key}
Type: 🌟 FOREVER LICENSE (Never expires!)

---
Copy the License Key above and send it to your client.
"""
            else:
                result = f"""License Key Generated Successfully!

Hardware ID: {license_data['hardware_id']}
License Key: {license_key}
Valid Until: {license_data['expiry_date']}
Days Valid: {license_data['days_valid']}

---
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

