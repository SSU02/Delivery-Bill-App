"""
License Management System
Controls access to the application using hardware-based activation
"""
import hashlib
import platform
import os
import json
import base64
from datetime import datetime, timedelta
import sys

# Try to import cryptography, but handle if it's not available
try:
    from cryptography.fernet import Fernet
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    Fernet = None

class LicenseManager:
    """Manages application licensing and activation"""
    
    def __init__(self, license_file="license.dat"):
        self.license_file = license_file
        self.hardware_id = self._get_hardware_id()
        self.encryption_key = self._get_encryption_key()
        
    def _get_hardware_id(self):
        """Generate a unique hardware ID based on machine characteristics"""
        try:
            # Get machine-specific information
            machine_info = {
                'machine': platform.machine(),
                'processor': platform.processor(),
                'platform': platform.platform(),
                'node': platform.node(),  # Computer name
            }
            
            # Try to get MAC address (more reliable)
            try:
                import uuid
                mac = uuid.getnode()
                machine_info['mac'] = str(mac)
            except:
                pass
            
            # Create a hash from machine info
            info_string = ''.join(str(v) for v in machine_info.values())
            hardware_id = hashlib.sha256(info_string.encode()).hexdigest()[:16].upper()
            return hardware_id
        except Exception as e:
            # Fallback to a simple hash
            return hashlib.sha256(str(platform.node()).encode()).hexdigest()[:16].upper()
    
    def _get_encryption_key(self):
        """Generate encryption key based on hardware ID"""
        key_string = self.hardware_id + "DeliveryBillApp2024"
        key = hashlib.sha256(key_string.encode()).digest()
        return base64.urlsafe_b64encode(key)
    
    def _encrypt_data(self, data):
        """Encrypt license data"""
        if CRYPTOGRAPHY_AVAILABLE:
            try:
                f = Fernet(self.encryption_key)
                encrypted = f.encrypt(data.encode())
                return base64.b64encode(encrypted).decode()
            except Exception:
                # Fallback: simple encoding if cryptography fails
                return base64.b64encode(data.encode()).decode()
        else:
            # Fallback: simple encoding if cryptography not available
            return base64.b64encode(data.encode()).decode()
    
    def _decrypt_data(self, encrypted_data):
        """Decrypt license data"""
        if CRYPTOGRAPHY_AVAILABLE:
            try:
                f = Fernet(self.encryption_key)
                decoded = base64.b64decode(encrypted_data.encode())
                decrypted = f.decrypt(decoded)
                return decrypted.decode()
            except Exception:
                # Fallback: simple decoding
                try:
                    return base64.b64decode(encrypted_data.encode()).decode()
                except:
                    return None
        else:
            # Fallback: simple decoding if cryptography not available
            try:
                return base64.b64decode(encrypted_data.encode()).decode()
            except:
                return None
    
    def generate_license_key(self, hardware_id=None, days_valid=365, forever=False):
        """Generate a license key for a specific hardware ID
        
        Args:
            hardware_id: Hardware ID (uses current if None)
            days_valid: Number of days valid (ignored if forever=True)
            forever: If True, creates a license that never expires
        """
        if hardware_id is None:
            hardware_id = self.hardware_id
        
        # Create license data
        if forever:
            expiry_date = "9999-12-31"  # Far future date (effectively forever)
            days_valid = 999999  # Special value for forever
            license_data = {
                'hardware_id': hardware_id,
                'expiry_date': expiry_date,
                'issued_date': datetime.now().strftime("%Y-%m-%d"),
                'days_valid': days_valid,
                'forever': True
            }
            # Use special marker for forever licenses
            key_string = f"{hardware_id}FOREVERDeliveryBillApp2024"
        else:
            expiry_date = (datetime.now() + timedelta(days=days_valid)).strftime("%Y-%m-%d")
            license_data = {
                'hardware_id': hardware_id,
                'expiry_date': expiry_date,
                'issued_date': datetime.now().strftime("%Y-%m-%d"),
                'days_valid': days_valid,
                'forever': False
            }
            key_string = f"{hardware_id}{expiry_date}DeliveryBillApp2024"
        
        license_key = hashlib.sha256(key_string.encode()).hexdigest()[:32].upper()
        
        # Format as XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX
        formatted_key = '-'.join([license_key[i:i+4] for i in range(0, 32, 4)])
        
        return formatted_key, license_data
    
    def validate_license_key(self, license_key):
        """Validate a license key against the current hardware ID"""
        # Remove dashes and convert to uppercase
        clean_key = license_key.replace('-', '').upper()
        
        if len(clean_key) != 32:
            return False, "Invalid license key format"
        
        # First check for forever license
        forever_key_string = f"{self.hardware_id}FOREVERDeliveryBillApp2024"
        expected_forever_key = hashlib.sha256(forever_key_string.encode()).hexdigest()[:32].upper()
        
        if clean_key == expected_forever_key:
            # Forever license found, save it
            license_data = {
                'hardware_id': self.hardware_id,
                'expiry_date': "9999-12-31",
                'activated_date': datetime.now().strftime("%Y-%m-%d"),
                'license_key': license_key,
                'forever': True,
                'days_valid': 999999
            }
            self.save_license(license_data)
            return True, "Forever license activated! License never expires."
        
        # Try different expiry dates (up to 10 years)
        for days in range(30, 3650, 30):  # Check every 30 days up to 10 years
            expiry_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
            key_string = f"{self.hardware_id}{expiry_date}DeliveryBillApp2024"
            expected_key = hashlib.sha256(key_string.encode()).hexdigest()[:32].upper()
            
            if clean_key == expected_key:
                # Valid key found, save it
                license_data = {
                    'hardware_id': self.hardware_id,
                    'expiry_date': expiry_date,
                    'activated_date': datetime.now().strftime("%Y-%m-%d"),
                    'license_key': license_key,
                    'forever': False,
                    'days_valid': days
                }
                self.save_license(license_data)
                return True, f"License activated! Valid until {expiry_date}"
        
        return False, "Invalid license key for this computer"
    
    def save_license(self, license_data):
        """Save license data to file (encrypted)"""
        try:
            data_json = json.dumps(license_data)
            encrypted = self._encrypt_data(data_json)
            
            with open(self.license_file, 'w') as f:
                f.write(encrypted)
            return True
        except Exception as e:
            print(f"Error saving license: {e}")
            return False
    
    def load_license(self):
        """Load and decrypt license data from file"""
        if not os.path.exists(self.license_file):
            return None
        
        try:
            with open(self.license_file, 'r') as f:
                encrypted = f.read()
            
            decrypted = self._decrypt_data(encrypted)
            if decrypted:
                return json.loads(decrypted)
            return None
        except Exception as e:
            print(f"Error loading license: {e}")
            return None
    
    def is_license_valid(self):
        """Check if the current license is valid"""
        license_data = self.load_license()
        
        if not license_data:
            return False, "No license found. Please activate the application."
        
        # Check hardware ID match
        if license_data.get('hardware_id') != self.hardware_id:
            return False, "License is not valid for this computer. Please contact support."
        
        # Check if it's a forever license
        if license_data.get('forever', False):
            return True, "Forever license - Never expires!"
        
        # Check expiry date for regular licenses
        try:
            expiry_date = datetime.strptime(license_data.get('expiry_date', ''), "%Y-%m-%d")
            if datetime.now() > expiry_date:
                return False, f"License expired on {license_data.get('expiry_date')}. Please renew."
        except:
            return False, "Invalid license data. Please reactivate."
        
        return True, f"License valid until {license_data.get('expiry_date')}"
    
    def get_hardware_id(self):
        """Get the current hardware ID (for generating license keys)"""
        return self.hardware_id
    
    def get_license_info(self):
        """Get current license information"""
        license_data = self.load_license()
        if license_data:
            return {
                'hardware_id': license_data.get('hardware_id'),
                'expiry_date': license_data.get('expiry_date'),
                'activated_date': license_data.get('activated_date', 'Unknown')
            }
        return None


def generate_license_for_client(hardware_id, days_valid=365, forever=False):
    """
    Standalone function to generate license keys for clients
    Usage: python license_manager.py <hardware_id> [days_valid] [--forever]
    """
    manager = LicenseManager()
    if hardware_id:
        license_key, license_data = manager.generate_license_key(hardware_id, days_valid, forever)
    else:
        license_key, license_data = manager.generate_license_key(days_valid=days_valid, forever=forever)
    
    print("\n" + "="*60)
    print("LICENSE KEY GENERATED")
    print("="*60)
    print(f"Hardware ID: {license_data['hardware_id']}")
    print(f"License Key: {license_key}")
    if license_data.get('forever', False):
        print(f"Type: FOREVER (Never expires)")
    else:
        print(f"Valid Until: {license_data['expiry_date']}")
        print(f"Days Valid: {license_data['days_valid']}")
    print("="*60 + "\n")
    
    return license_key, license_data


if __name__ == "__main__":
    # Command-line tool for generating license keys
    if len(sys.argv) > 1:
        hardware_id = sys.argv[1].upper()
        # Check for --forever flag
        if '--forever' in sys.argv or '-f' in sys.argv:
            generate_license_for_client(hardware_id, forever=True)
        else:
            days_valid = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] not in ['--forever', '-f'] else 365
            generate_license_for_client(hardware_id, days_valid)
    else:
        # Interactive mode
        print("License Key Generator")
        print("="*60)
        hardware_id = input("Enter Hardware ID (or press Enter to use current machine): ").strip().upper()
        if not hardware_id:
            manager = LicenseManager()
            hardware_id = manager.get_hardware_id()
            print(f"Using current machine Hardware ID: {hardware_id}")
        
        forever_input = input("Forever license? (y/n, default n): ").strip().lower()
        if forever_input == 'y':
            generate_license_for_client(hardware_id, forever=True)
        else:
            days_input = input("Enter days valid (default 365): ").strip()
            days_valid = int(days_input) if days_input else 365
            generate_license_for_client(hardware_id, days_valid)

