# Delivery Bill Generator

A modern, professional desktop application for generating delivery bills/challans. Built with PyQt.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Or using conda
conda env create -f environment.yml
conda activate delivery-bill

# Run application
python main_modern.py
```

## Building Windows Executable

```bash
pip install pyinstaller
python build_exe_modern.py
```

Executable will be in `dist/DeliveryBillApp.exe`

## Licensing

### Generate License Keys

**GUI Tool:**
```bash
python license_key_generator_gui.py
```

**Command Line:**
```bash
python generate_license.py <hardware_id> <days>
# Example: python generate_license.py ABC123XYZ 365
```

### License Periods
- Trial: 30 days
- Monthly: 30 days
- 1 Year: 365 days (most common)
- Forever: Never expires

### Workflow
1. Client runs app → sees Hardware ID
2. Client sends Hardware ID to you
3. You generate license key
4. Client enters key → app activated

## Requirements

- Python 3.8+
- PyQt5/PyQt6
- ReportLab
- pypdf
- cryptography

See `requirements.txt` for complete list.
