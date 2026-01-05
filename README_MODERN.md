# Delivery Bill Generator - Modern Professional Edition

A modern, professional desktop application for generating delivery bills/challans with a Tally/ZohoBooks-like interface. Built with PyQt6 for a native, professional look and feel.

## Features

✨ **Modern Professional UI**
- Clean, card-based design
- Professional color scheme
- Intuitive navigation
- Responsive layout

📋 **Batch Processing**
- Process multiple customers at once
- Auto-increment invoice numbers
- Bulk PDF generation

👥 **Customer Management**
- Add, edit, and manage customers
- Customer details with blaster information
- Area-based customer organization

📦 **Goods & Items Management**
- Manage goods catalog
- Quick item addition with tax calculations
- Automatic CGST/SGST/IGST calculations

🚚 **Vehicle & Area Management**
- Manage vehicles
- Organize by areas/locations

📄 **PDF Generation**
- Professional PDF delivery challans
- Batch generation for multiple customers
- Automatic total calculations in words

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Run the modern application:
```bash
python main_modern.py
```

## Building Windows Executable

To create a standalone Windows executable that can be copied to a pendrive and run on any Windows computer:

### Using the Build Script

1. Install PyInstaller:
```bash
pip install pyinstaller
```

2. Run the build script:
```bash
python build_modern.py
```

3. The executable will be created in the `dist` folder:
   - `dist/DeliveryBillGenerator_Modern.exe`

4. **Copy to Pendrive**: Simply copy the `.exe` file to your pendrive and run it on any Windows computer!

### Manual Build

If you prefer to build manually:

```bash
pyinstaller --onefile --windowed --name=DeliveryBillGenerator_Modern --hidden-import=PyQt6 --collect-all=PyQt6 --collect-all=reportlab main_modern.py
```

## Usage

### Basic Workflow

1. **Select Category**: Choose "Detonator" or "Explosives"
2. **Select Area**: Choose or add an area/location
3. **Configure Settings**: Set date, vehicle, and starting invoice numbers
4. **Select Customers**: Check the customers you want to process
5. **Add Items**: Click the arrow (▶) next to a customer to expand and add goods
6. **Generate PDFs**: Click "Generate PDFs for Selected Customers"

### Adding Customers

1. Click "Add Customer" button
2. Fill in customer details (Name is required)
3. Optionally select or add a blaster
4. Click "Save"

### Adding Goods to Customers

1. Expand a customer by clicking the arrow (▶)
2. Click "+ Add Good" button
3. Select a good from the list or create a new one
4. Enter quantity
5. Click "Add to Bill"

### Generating PDFs

1. Ensure all selected customers have items
2. Click "Generate PDFs for Selected Customers"
3. Select the folder where PDFs should be saved
4. PDFs will be generated with names like `Delivery_Bill_[InvoiceNo].pdf`

## Database

The application uses SQLite database (`delivery_bill.db`) stored in the same directory. The database is created automatically on first run and contains:
- Customers
- Locations/Areas
- Vehicles
- Goods
- Blasters
- Settings (tax rates, etc.)

## UI Design Philosophy

The modern UI follows professional accounting software design principles:

- **Card-based Layout**: Information is organized in clean, bordered cards
- **Color Scheme**: Professional blue (#007bff) for primary actions, neutral grays for backgrounds
- **Typography**: Clear, readable fonts with appropriate sizing
- **Spacing**: Generous padding and margins for comfortable viewing
- **Consistency**: Uniform button styles, input fields, and layouts throughout

## Comparison with Old Version

| Feature | Old (Tkinter) | Modern (PyQt6) |
|---------|---------------|----------------|
| UI Framework | Tkinter | PyQt6 |
| Look & Feel | Basic | Professional |
| Native Feel | Limited | Full native |
| Performance | Good | Excellent |
| Distribution | Works | Better packaging |
| Modern Features | Limited | Full support |

## Troubleshooting

### Application won't start
- Ensure Python 3.8+ is installed
- Check all dependencies: `pip install -r requirements.txt`
- Verify PyQt6 is installed: `pip install PyQt6`

### PDF generation fails
- Ensure you have write permissions in the save folder
- Check that all required fields are filled
- Verify customers have items added

### Database issues
- The database is created automatically
- If corrupted, delete `delivery_bill.db` and restart (data will be lost)

## Future Enhancements

- [ ] Area/Vehicle management dialogs
- [ ] Customer management window
- [ ] Settings panel for tax rates
- [ ] Export/Import functionality
- [ ] Report generation
- [ ] Multi-language support

## License

This application is created for professional use.

## Support

For issues or questions, please refer to the main project documentation.

