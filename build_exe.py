"""
Build script for creating Windows executable
Run this script to create a standalone .exe file
"""
import PyInstaller.__main__
import os
import sys

def build_exe():
    """Build the executable using PyInstaller"""
    
    # PyInstaller arguments
    # Note: Python modules are automatically included, so we don't need --add-data for .py files
    args = [
        'main.py',
        '--onefile',  # Create a single executable file
        '--windowed',  # No console window (GUI only)
        '--name=DeliveryBillGenerator',  # Name of the executable
        '--hidden-import=reportlab',  # Ensure reportlab is included
        '--hidden-import=tkcalendar',  # Ensure tkcalendar is included
        '--collect-all=reportlab',  # Collect all reportlab data
        '--clean',  # Clean cache before building
    ]
    
    # Add icon if it exists
    if os.path.exists('icon.ico'):
        args.append('--icon=icon.ico')
    
    print("Building executable...")
    print("This may take a few minutes...")
    
    try:
        PyInstaller.__main__.run(args)
        print("\nBuild complete!")
        print("The executable is in the 'dist' folder.")
    except Exception as e:
        print(f"Error building executable: {e}")
        print("\nMake sure PyInstaller is installed:")
        print("pip install pyinstaller")
        sys.exit(1)

if __name__ == "__main__":
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller is not installed.")
        print("Please install it first:")
        print("pip install pyinstaller")
        sys.exit(1)
    
    build_exe()

