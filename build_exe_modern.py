"""
Build script for creating Windows executable for main_modern.py
Run this script to create a standalone .exe file that includes everything
"""
import PyInstaller.__main__
import os
import sys

def build_exe():
    """Build the executable using PyInstaller"""
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # PyInstaller arguments
    args = [
        'main_modern.py',  # Main entry point
        '--onefile',  # Create a single executable file
        '--windowed',  # No console window (GUI only)
        '--name=DeliveryBillApp',  # Name of the executable
        '--clean',  # Clean cache before building
        
        # Hidden imports (PyInstaller might miss these)
        '--hidden-import=reportlab',
        '--hidden-import=reportlab.lib',
        '--hidden-import=reportlab.pdfgen',
        '--hidden-import=reportlab.platypus',
        '--hidden-import=reportlab.lib.units',
        '--hidden-import=pypdf',
        '--hidden-import=PyPDF2',
        '--hidden-import=cryptography',
        '--hidden-import=cryptography.fernet',
        
        # Collect all reportlab data files
        '--collect-all=reportlab',
        
        # Include database file (will be created if doesn't exist, but include template)
        # Note: Database will be created at runtime if not present
        
        # Include license manager
        '--hidden-import=license_manager',
        
        # Include all dialogs
        '--hidden-import=dialogs_modern',
        
        # Include other modules
        '--hidden-import=database',
        '--hidden-import=pdf_generator',
        '--hidden-import=number_to_words',
    ]
    
    # Add icon if it exists
    icon_path = os.path.join(script_dir, 'icon.ico')
    if os.path.exists(icon_path):
        args.append(f'--icon={icon_path}')
    
    print("="*60)
    print("Building Delivery Bill App Executable")
    print("="*60)
    print("\nThis will create a standalone .exe file that includes:")
    print("  - Python interpreter")
    print("  - All dependencies (PyQt, ReportLab, etc.)")
    print("  - Your application code")
    print("  - License system")
    print("\nThe client will NOT need:")
    print("  - Python installed")
    print("  - Conda environment")
    print("  - Any dependencies")
    print("\nBuilding... This may take 5-10 minutes...\n")
    
    try:
        PyInstaller.__main__.run(args)
        print("\n" + "="*60)
        print("Build Complete!")
        print("="*60)
        print("\nThe executable is in the 'dist' folder:")
        print("  dist/DeliveryBillApp.exe")
        print("\nYou can now:")
        print("  1. Copy DeliveryBillApp.exe to your client's computer")
        print("  2. Client runs it (no Python/conda needed!)")
        print("  3. Client sees Hardware ID and sends it to you")
        print("  4. You generate license key using: python generate_license.py <hardware_id>")
        print("  5. Client enters license key and app works!")
        print("\nNote: The database (delivery_bill.db) will be created")
        print("      automatically when the app runs for the first time.")
        print("="*60 + "\n")
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
    
    # Check if we're on Windows (recommended for Windows builds)
    if sys.platform != 'win32':
        print("Warning: You're not on Windows.")
        print("PyInstaller can create Windows executables on other platforms,")
        print("but it's recommended to build on Windows for best compatibility.")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    build_exe()

