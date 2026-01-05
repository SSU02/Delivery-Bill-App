"""
Build script for creating Windows executable for Modern UI version
Run this script to create a standalone .exe file that can be copied to pendrive
"""
import PyInstaller.__main__
import os
import sys

def build_exe():
    """Build the executable using PyInstaller"""
    
    # PyInstaller arguments
    args = [
        'main_modern.py',
        '--onefile',  # Create a single executable file
        '--windowed',  # No console window (GUI only)
        '--name=DeliveryBillGenerator_Modern',  # Name of the executable
        '--hidden-import=reportlab',  # Ensure reportlab is included
        '--hidden-import=PyQt6',  # Ensure PyQt6 is included
        '--hidden-import=PyQt6.QtCore',  # PyQt6 core
        '--hidden-import=PyQt6.QtGui',  # PyQt6 GUI
        '--hidden-import=PyQt6.QtWidgets',  # PyQt6 Widgets
        '--collect-all=reportlab',  # Collect all reportlab data
        '--collect-all=PyQt6',  # Collect all PyQt6 data
        '--clean',  # Clean cache before building
        '--add-data=delivery_bill.db;.' if os.path.exists('delivery_bill.db') else '',  # Include database if exists
    ]
    
    # Remove empty strings
    args = [arg for arg in args if arg]
    
    # Add icon if it exists
    if os.path.exists('icon.ico'):
        args.append('--icon=icon.ico')
    
    print("=" * 60)
    print("Building Modern Delivery Bill Generator Executable")
    print("=" * 60)
    print("This may take a few minutes...")
    print("")
    
    try:
        PyInstaller.__main__.run(args)
        print("\n" + "=" * 60)
        print("Build complete!")
        print("=" * 60)
        print(f"\nThe executable is in the 'dist' folder:")
        print(f"  dist/DeliveryBillGenerator_Modern.exe")
        print("\nYou can copy this .exe file to a pendrive and run it on any Windows computer!")
        print("\nNote: The database file (delivery_bill.db) will be created automatically")
        print("      in the same folder where you run the executable.")
    except Exception as e:
        print(f"\nError building executable: {e}")
        print("\nMake sure PyInstaller is installed:")
        print("  pip install pyinstaller")
        print("\nAlso ensure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        sys.exit(1)

if __name__ == "__main__":
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller is not installed.")
        print("Please install it first:")
        print("  pip install pyinstaller")
        sys.exit(1)
    
    # Check if PyQt6 is installed
    try:
        import PyQt6
    except ImportError:
        print("PyQt6 is not installed.")
        print("Please install it first:")
        print("  pip install PyQt6")
        sys.exit(1)
    
    build_exe()

