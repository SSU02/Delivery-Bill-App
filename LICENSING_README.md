# Licensing System Documentation

## Overview

The Delivery Bill App includes a hardware-based licensing system that protects your application from unauthorized use. Each license is tied to a specific computer using a unique Hardware ID.

## How It Works

1. **Hardware ID Generation**: When the app runs, it generates a unique Hardware ID based on the computer's characteristics (MAC address, processor, etc.)

2. **License Activation**: Users must enter a valid license key to activate the application

3. **License Validation**: The app checks the license on startup and validates it against:
   - Hardware ID match
   - Expiry date

4. **License Storage**: License data is encrypted and stored locally in `license.dat`

## For Developers (You)

### Generating License Keys for Clients

#### Method 1: Using the Generator Script

```bash
python generate_license.py <hardware_id> [days_valid]
```

**Example:**
```bash
python generate_license.py A1B2C3D4E5F6G7H8 365
```

This will generate a license key valid for 365 days for the specified Hardware ID.

#### Method 2: Interactive Mode

```bash
python generate_license.py
```

The script will prompt you for:
- Hardware ID (from the client)
- Days valid (default: 365)

#### Method 3: Using Python Directly

```python
from license_manager import generate_license_for_client

hardware_id = "A1B2C3D4E5F6G7H8"  # Client's Hardware ID
days_valid = 365  # License validity period

license_key, license_data = generate_license_for_client(hardware_id, days_valid)
print(f"License Key: {license_key}")
```

### Getting Client Hardware ID

When a client runs the app for the first time (or with an invalid license), they will see an activation dialog that displays their Hardware ID. They should send this Hardware ID to you.

### License Key Format

License keys are formatted as: `XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX`

Example: `A1B2-C3D4-E5F6-G7H8-I9J0-K1L2-M3N4-O5P6`

## For End Users (Clients)

### First-Time Activation

1. Run the application
2. You'll see an activation dialog with your **Hardware ID**
3. Send this Hardware ID to your vendor
4. Receive your **License Key** from the vendor
5. Enter the License Key in the activation dialog
6. Click "Activate"

### License Expiry

- If your license expires, you'll see a message when starting the app
- Contact your vendor to renew your license
- You'll receive a new License Key to activate

### Transferring License

- Licenses are tied to a specific computer (Hardware ID)
- To use on a different computer, you need a new license key for that computer's Hardware ID

## Technical Details

### License File Location

- License data is stored in `license.dat` in the application directory
- The file is encrypted using the Hardware ID as part of the encryption key

### Security Features

- Hardware ID binding (license only works on the registered computer)
- Encrypted license storage
- Expiry date validation
- License key format validation

### License Data Structure

```json
{
    "hardware_id": "A1B2C3D4E5F6G7H8",
    "expiry_date": "2025-12-31",
    "activated_date": "2024-01-01",
    "license_key": "XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX"
}
```

## Troubleshooting

### "License is not valid for this computer"

- The license key was generated for a different Hardware ID
- Solution: Generate a new license key for the current computer's Hardware ID

### "License expired"

- The license has passed its expiry date
- Solution: Generate a new license key with a new expiry date

### "No license found"

- The `license.dat` file is missing or corrupted
- Solution: Re-enter the license key to activate again

### License file corruption

- If the license file gets corrupted, the user can simply re-enter their license key
- The system will validate and recreate the license file

## Distribution Notes

When distributing your app:

1. **Include the license system**: The licensing code is already integrated
2. **No internet required**: The system works offline
3. **Client process**: 
   - Client installs app
   - Client runs app → sees Hardware ID
   - Client sends Hardware ID to you
   - You generate license key
   - Client enters license key → app activated

## Customization

### Changing License Validity Period

In `generate_license.py` or when calling `generate_license_for_client()`, specify the `days_valid` parameter:

```python
# 1 year license
generate_license_for_client(hardware_id, 365)

# 6 months license
generate_license_for_client(hardware_id, 180)

# Lifetime license (10 years)
generate_license_for_client(hardware_id, 3650)
```

### Disabling License Check (Development)

To temporarily disable license checking during development, comment out the license check in `main_modern.py`:

```python
# Comment out these lines in main() function:
# is_valid, message = license_manager.is_license_valid()
# if not is_valid:
#     ...
```

**Note**: Remember to re-enable it before distribution!

