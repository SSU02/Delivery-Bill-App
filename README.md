# Delivery Bill Generator - Senthil Explosives

A desktop application for generating delivery bills/invoices for Senthil Explosives. The application supports two categories: Detonator and Explosives, with comprehensive customer, location, vehicle, and goods management.

## Features

- **Category Selection**: Choose between Detonator and Explosives
- **Location Management**: Create and manage locations with vehicle numbers specific to each location
- **Customer Management**: Add, edit, and select customers with full details (Name, Address, SF.NO, RC.NO, State, GSTIN)
- **Goods Management**: Create and manage goods with HSN codes, units, and rates
- **Invoice Generation**: Create invoices with:
  - Automatic tax calculations (CGST, SGST, IGST)
  - Multiple items support
  - Freight charges
  - Total amount in words
  - PDF export
- **Data Persistence**: SQLite database for storing all data locally

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Setup

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

## Packaging as Windows Executable (.exe)

To create a standalone Windows executable that can run on any Windows computer without Python installed:

### Using PyInstaller

1. Install PyInstaller:
```bash
pip install pyinstaller
```

2. Create the executable:
```bash
pyinstaller --onefile --windowed --name "DeliveryBillGenerator" --icon=NONE main.py
```

Or with a custom icon (if you have one):
```bash
pyinstaller --onefile --windowed --name "DeliveryBillGenerator" --icon=icon.ico main.py
```

3. The executable will be created in the `dist` folder.

### Alternative: Using cx_Freeze

1. Install cx_Freeze:
```bash
pip install cx_Freeze
```

2. Create a `setup.py` file:
```python
from cx_Freeze import setup, Executable

setup(
    name="DeliveryBillGenerator",
    version="1.0",
    description="Delivery Bill Generator for Senthil Explosives",
    executables=[Executable("main.py", base="Win32GUI")]
)
```

3. Build:
```bash
python setup.py build
```

## Usage

1. **Select Category**: Choose either "Detonator" or "Explosives"
2. **Select/Add Location**: Choose a location or add a new one
3. **Select/Add Vehicle**: Choose a vehicle number for the selected location
4. **Select/Add Customer**: Choose a customer or add a new one with all details
5. **Fill Invoice Details**: Enter invoice number, date, transport mode, etc.
6. **Add Items**: Add goods to the invoice with quantities and rates
7. **Review Totals**: Check freight charges and grand total
8. **Generate PDF**: Click "Generate PDF" to save the invoice

## Database

The application uses SQLite database (`delivery_bill.db`) stored in the same directory as the application. This database contains:
- Customers
- Locations
- Vehicles
- Goods
- Settings (tax rates, etc.)

## Notes

- The application automatically calculates taxes based on the taxable value
- Tax rates can be customized and are saved for future use
- Total amounts are rounded to the nearest integer
- The total amount in words is automatically generated
- All customer and goods data is stored locally in the database

## Troubleshooting

If you encounter issues:
1. Make sure all dependencies are installed: `pip install -r requirements.txt`
2. Check that Python 3.7+ is installed
3. For PDF generation issues, ensure you have write permissions in the save location
4. The database file will be created automatically on first run

## License

This application is created for Senthil Explosives.

