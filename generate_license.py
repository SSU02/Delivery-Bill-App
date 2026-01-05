#!/usr/bin/env python3
"""
License Key Generator Tool
Use this script to generate license keys for your clients

Usage:
    python generate_license.py <hardware_id> [days_valid]
    
Example:
    python generate_license.py A1B2C3D4E5F6G7H8 365
"""
import sys
from license_manager import generate_license_for_client

if __name__ == "__main__":
    print("\n" + "="*60)
    print("DELIVERY BILL APP - LICENSE KEY GENERATOR")
    print("="*60 + "\n")
    
    if len(sys.argv) > 1:
        # Command line mode
        hardware_id = sys.argv[1].upper().strip()
        days_valid = int(sys.argv[2]) if len(sys.argv) > 2 else 365
        generate_license_for_client(hardware_id, days_valid)
    else:
        # Interactive mode
        print("Enter client information to generate a license key:\n")
        
        hardware_id = input("Client Hardware ID: ").strip().upper()
        if not hardware_id:
            print("\nError: Hardware ID is required!")
            print("\nTo get the Hardware ID:")
            print("1. Ask the client to run the app")
            print("2. The Hardware ID will be shown in the activation dialog")
            print("3. Copy that Hardware ID and run this script again\n")
            sys.exit(1)
        
        days_input = input("Days valid (default 365): ").strip()
        days_valid = int(days_input) if days_input else 365
        
        print("\nGenerating license key...\n")
        license_key, license_data = generate_license_for_client(hardware_id, days_valid)
        
        print("\n" + "="*60)
        print("SEND THIS TO YOUR CLIENT:")
        print("="*60)
        print(f"\nLicense Key: {license_key}\n")
        print("="*60 + "\n")

