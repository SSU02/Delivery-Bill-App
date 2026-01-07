"""
Database module for managing customers, locations, vehicles, goods, and settings
"""
import sqlite3
import os
from typing import List, Dict, Optional, Tuple

class Database:
    def __init__(self, db_path: str = "delivery_bill.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Customers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                sf_no TEXT,
                rc_no TEXT,
                state TEXT,
                gstin TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add location_id column if it doesn't exist (for existing databases)
        try:
            cursor.execute("ALTER TABLE customers ADD COLUMN location_id INTEGER")
        except sqlite3.OperationalError:
            # Column already exists, ignore
            pass
        
        # Locations table (common to both Detonator and Explosives)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Migrate existing locations table - remove category column if it exists
        try:
            cursor.execute("PRAGMA table_info(locations)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'category' in columns:
                # Create new table without category
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS locations_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # Copy data (may have duplicates by name, so use DISTINCT)
                cursor.execute("""
                    INSERT OR IGNORE INTO locations_new (id, name, created_at)
                    SELECT DISTINCT id, name, created_at FROM locations
                    ORDER BY name ASC
                """)
                # Drop old table and rename new one
                cursor.execute("DROP TABLE locations")
                cursor.execute("ALTER TABLE locations_new RENAME TO locations")
                conn.commit()
        except Exception:
            # Migration failed, but that's okay
            pass
        
        # Blasters table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blasters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                document_no TEXT,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Vehicles table (common to all areas and categories)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_number TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Migrate existing vehicles table if it has location_id column
        try:
            cursor.execute("PRAGMA table_info(vehicles)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'location_id' in columns:
                # Create new table without location_id
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vehicles_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        vehicle_number TEXT NOT NULL UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                # Copy data (may have duplicates, so we'll handle that)
                cursor.execute("""
                    INSERT OR IGNORE INTO vehicles_new (id, vehicle_number, created_at)
                    SELECT id, vehicle_number, created_at FROM vehicles
                """)
                # Drop old table and rename new one
                cursor.execute("DROP TABLE vehicles")
                cursor.execute("ALTER TABLE vehicles_new RENAME TO vehicles")
                conn.commit()
        except Exception:
            # Migration failed, but that's okay - table might already be updated
            pass
        
        # Goods table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                hsn_code TEXT NOT NULL,
                unit TEXT NOT NULL,
                rate REAL NOT NULL,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add category column if it doesn't exist (for existing databases)
        try:
            cursor.execute("ALTER TABLE goods ADD COLUMN category TEXT")
        except sqlite3.OperationalError:
            # Column already exists, ignore
            pass
        
        # Settings table (for tax rates, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
        # Initialize default settings
        cursor.execute("""
            INSERT OR IGNORE INTO settings (key, value) VALUES 
            ('cgst_rate', '9.0'),
            ('sgst_rate', '9.0')
        """)
        
        # Migrate blaster data from customers table to blasters table (if old columns exist)
        try:
            cursor.execute("PRAGMA table_info(customers)")
            customer_columns = [row[1] for row in cursor.fetchall()]
            
            # Check if customers table has old blaster columns and migrate if needed
            if 'blaster_name' in customer_columns and 'blaster_id' not in customer_columns:
                # Migrate existing blaster data
                cursor.execute("""
                    SELECT DISTINCT blaster_name, blaster_document_no, blaster_address 
                    FROM customers 
                    WHERE blaster_name IS NOT NULL AND blaster_name != ''
                """)
                blaster_data = cursor.fetchall()
                
                # Add blasters to blasters table (avoid duplicates by name)
                for blaster_name, document_no, address in blaster_data:
                    cursor.execute("""
                        INSERT OR IGNORE INTO blasters (name, document_no, address)
                        VALUES (?, ?, ?)
                    """, (blaster_name or '', document_no or '', address or ''))
                
                conn.commit()
                
                # Add blaster_id column to customers
                try:
                    cursor.execute("ALTER TABLE customers ADD COLUMN blaster_id INTEGER")
                except sqlite3.OperationalError:
                    pass  # Column might already exist
                
                # Update customers to reference blasters
                cursor.execute("""
                    UPDATE customers 
                    SET blaster_id = (
                        SELECT id FROM blasters 
                        WHERE blasters.name = customers.blaster_name 
                        LIMIT 1
                    )
                    WHERE blaster_name IS NOT NULL AND blaster_name != ''
                """)
                conn.commit()
        except Exception as e:
            # Migration failed, but continue
            pass
        
        # Remove old blaster columns from customers table if they exist
        try:
            cursor.execute("PRAGMA table_info(customers)")
            customer_columns = [row[1] for row in cursor.fetchall()]
            
            # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
            if any(col in customer_columns for col in ['blaster_name', 'blaster_document_no', 'blaster_address']):
                # Create new table without the old blaster columns
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS customers_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        address TEXT,
                        sf_no TEXT,
                        rc_no TEXT,
                        state TEXT,
                        gstin TEXT,
                        blaster_id INTEGER,
                        location_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Copy data from old table to new table (excluding old blaster columns)
                cursor.execute("""
                    INSERT INTO customers_new (id, name, address, sf_no, rc_no, state, gstin, blaster_id, location_id, created_at)
                    SELECT id, name, address, sf_no, rc_no, state, gstin, blaster_id, location_id, created_at
                    FROM customers
                """)
                
                # Drop old table and rename new one
                cursor.execute("DROP TABLE customers")
                cursor.execute("ALTER TABLE customers_new RENAME TO customers")
                conn.commit()
        except Exception as e:
            # Migration failed, but continue
            conn.rollback()
            pass
        
        # Add blaster_id column if it doesn't exist (for new databases)
        try:
            cursor.execute("ALTER TABLE customers ADD COLUMN blaster_id INTEGER")
        except sqlite3.OperationalError:
            # Column already exists, ignore
            pass
        
        conn.commit()
        conn.close()
        
        # Migrate existing customer data to uppercase
        self.migrate_customers_to_uppercase()
        
        # Migrate existing location data to uppercase
        self.migrate_locations_to_uppercase()
        
        # Clean up orphaned blaster references
        self.cleanup_orphaned_blaster_references()
    
    def migrate_customers_to_uppercase(self):
        """Migrate all existing customer data to uppercase"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Get all customers
            cursor.execute("SELECT id, name, address, sf_no, rc_no, state, gstin FROM customers")
            customers = cursor.fetchall()
            
            # Update each customer to uppercase
            for customer in customers:
                customer_id = customer[0]
                name = customer[1].upper() if customer[1] else ""
                address = customer[2].upper() if customer[2] else ""
                sf_no = customer[3].upper() if customer[3] else ""
                rc_no = customer[4].upper() if customer[4] else ""
                state = customer[5].upper() if customer[5] else ""
                gstin = customer[6].upper() if customer[6] else ""
                
                cursor.execute("""
                    UPDATE customers 
                    SET name = ?, address = ?, sf_no = ?, rc_no = ?, state = ?, gstin = ?
                    WHERE id = ?
                """, (name, address, sf_no, rc_no, state, gstin, customer_id))
            
            conn.commit()
        except Exception as e:
            # Migration failed, but continue
            conn.rollback()
            pass
        finally:
            conn.close()
    
    def migrate_locations_to_uppercase(self):
        """Migrate all existing location data to uppercase"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Get all locations
            cursor.execute("SELECT id, name FROM locations")
            locations = cursor.fetchall()
            
            # Update each location to uppercase
            for location in locations:
                location_id = location[0]
                name = location[1].upper() if location[1] else ""
                
                cursor.execute("""
                    UPDATE locations 
                    SET name = ?
                    WHERE id = ?
                """, (name, location_id))
            
            conn.commit()
        except Exception as e:
            # Migration failed, but continue
            conn.rollback()
            pass
        finally:
            conn.close()
    
    def cleanup_orphaned_blaster_references(self):
        """Clean up any orphaned blaster_id references in customers table"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Find customers with blaster_id that doesn't exist in blasters table
            cursor.execute("""
                UPDATE customers 
                SET blaster_id = NULL 
                WHERE blaster_id IS NOT NULL 
                AND blaster_id NOT IN (SELECT id FROM blasters)
            """)
            conn.commit()
        except Exception as e:
            # Cleanup failed, but continue
            conn.rollback()
            pass
        finally:
            conn.close()
    
    # Customer operations
    def add_customer(self, name: str, address: str = "", sf_no: str = "", 
                     rc_no: str = "", state: str = "", gstin: str = "", 
                     blaster_id: int = None, location_id: int = None) -> int:
        """Add a new customer - convert all text fields to uppercase"""
        # Convert all text fields to uppercase
        name = name.upper() if name else ""
        address = address.upper() if address else ""
        sf_no = sf_no.upper() if sf_no else ""
        rc_no = rc_no.upper() if rc_no else ""
        state = state.upper() if state else ""
        gstin = gstin.upper() if gstin else ""
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO customers (name, address, sf_no, rc_no, state, gstin, blaster_id, location_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, address, sf_no, rc_no, state, gstin, blaster_id, location_id))
        conn.commit()
        customer_id = cursor.lastrowid
        conn.close()
        return customer_id
    
    def get_customers(self, location_id: int = None) -> List[Dict]:
        """Get customers sorted alphabetically, optionally filtered by location_id.
        Includes blaster data via LEFT JOIN."""
        conn = self.get_connection()
        cursor = conn.cursor()
        if location_id is not None:
            cursor.execute("""
                SELECT c.id, c.name, c.address, c.sf_no, c.rc_no, c.state, c.gstin, 
                       c.blaster_id, c.location_id, c.created_at,
                       b.name as blaster_name, b.document_no as blaster_document_no, b.address as blaster_address
                FROM customers c
                LEFT JOIN blasters b ON c.blaster_id = b.id
                WHERE c.location_id = ?
                ORDER BY c.name ASC
            """, (location_id,))
        else:
            cursor.execute("""
                SELECT c.id, c.name, c.address, c.sf_no, c.rc_no, c.state, c.gstin, 
                       c.blaster_id, c.location_id, c.created_at,
                       b.name as blaster_name, b.document_no as blaster_document_no, b.address as blaster_address
                FROM customers c
                LEFT JOIN blasters b ON c.blaster_id = b.id
                ORDER BY c.name ASC
            """)
        customers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return customers
    
    def get_customer(self, customer_id: int) -> Optional[Dict]:
        """Get customer by ID, includes blaster data via JOIN"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.name, c.address, c.sf_no, c.rc_no, c.state, c.gstin, 
                   c.blaster_id, c.location_id, c.created_at,
                   b.name as blaster_name, b.document_no as blaster_document_no, b.address as blaster_address
            FROM customers c
            LEFT JOIN blasters b ON c.blaster_id = b.id
            WHERE c.id = ?
        """, (customer_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def delete_customer(self, customer_id: int):
        """Delete a customer"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
        conn.commit()
        conn.close()
        # Renumber IDs after deletion
        self.renumber_customers()
    
    def update_customer(self, customer_id: int, name: str, address: str = "",
                       sf_no: str = "", rc_no: str = "", state: str = "", gstin: str = "",
                       blaster_id: int = None, location_id: int = None):
        """Update customer details - convert all text fields to uppercase"""
        # Convert all text fields to uppercase
        name = name.upper() if name else ""
        address = address.upper() if address else ""
        sf_no = sf_no.upper() if sf_no else ""
        rc_no = rc_no.upper() if rc_no else ""
        state = state.upper() if state else ""
        gstin = gstin.upper() if gstin else ""
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE customers 
            SET name = ?, address = ?, sf_no = ?, rc_no = ?, state = ?, gstin = ?, blaster_id = ?, location_id = ?
            WHERE id = ?
        """, (name, address, sf_no, rc_no, state, gstin, blaster_id, location_id, customer_id))
        conn.commit()
        conn.close()
    
    # Location operations (common to both Detonator and Explosives)
    def add_location(self, name: str) -> int:
        """Add a new location (common to both categories) - convert name to uppercase"""
        # Convert name to uppercase
        name = name.upper() if name else ""
        
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO locations (name)
                VALUES (?)
            """, (name,))
            conn.commit()
            location_id = cursor.lastrowid
            conn.close()
            return location_id
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError(f"Location '{name}' already exists")
    
    def get_locations(self) -> List[Dict]:
        """Get all locations (common to both categories)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM locations ORDER BY name ASC")
        locations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return locations
    
    def update_location(self, location_id: int, name: str):
        """Update location name - convert name to uppercase"""
        # Convert name to uppercase
        name = name.upper() if name else ""
        
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE locations 
                SET name = ?
                WHERE id = ?
            """, (name, location_id))
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError(f"Location '{name}' already exists")
    
    def delete_location(self, location_id: int):
        """Delete a location (vehicles are now common, so no need to delete them)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Delete the location (vehicles are no longer linked to locations)
        cursor.execute("DELETE FROM locations WHERE id = ?", (location_id,))
        conn.commit()
        conn.close()
        # Renumber IDs after deletion
        self.renumber_locations()
    
    def renumber_locations(self):
        """Renumber location IDs to be sequential (1, 2, 3...) based on alphabetical order"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get all locations ordered alphabetically by name
            cursor.execute("SELECT id, name, created_at FROM locations ORDER BY name ASC")
            locations = cursor.fetchall()
            
            if not locations:
                conn.close()
                return
            
            # Create temporary table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS locations_temp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert locations in alphabetical order with new IDs (1, 2, 3, ...)
            cursor.execute("DELETE FROM locations_temp")
            for new_id, (old_id, name, created_at) in enumerate(locations, 1):
                cursor.execute("""
                    INSERT INTO locations_temp (id, name, created_at)
                    VALUES (?, ?, ?)
                """, (new_id, name, created_at))
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE locations")
            cursor.execute("ALTER TABLE locations_temp RENAME TO locations")
            
            conn.commit()
            conn.close()
        except Exception as e:
            conn.rollback()
            conn.close()
            # If renumbering fails, that's okay - IDs don't have to be sequential
            pass
    
    def renumber_customers(self):
        """Renumber customer IDs to be sequential (1, 2, 3...) based on alphabetical order"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get all customers ordered alphabetically by name
            cursor.execute("SELECT id, name, address, sf_no, rc_no, state, gstin, blaster_id, location_id, created_at FROM customers ORDER BY name ASC")
            customers = cursor.fetchall()
            
            if not customers:
                conn.close()
                return
            
            # Create temporary table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers_temp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    address TEXT,
                    sf_no TEXT,
                    rc_no TEXT,
                    state TEXT,
                    gstin TEXT,
                    blaster_id INTEGER,
                    location_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert customers in alphabetical order with new IDs (1, 2, 3, ...)
            cursor.execute("DELETE FROM customers_temp")
            for new_id, (old_id, name, address, sf_no, rc_no, state, gstin, blaster_id, location_id, created_at) in enumerate(customers, 1):
                cursor.execute("""
                    INSERT INTO customers_temp (id, name, address, sf_no, rc_no, state, gstin, blaster_id, location_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (new_id, name, address, sf_no, rc_no, state, gstin, blaster_id, location_id, created_at))
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE customers")
            cursor.execute("ALTER TABLE customers_temp RENAME TO customers")
            
            conn.commit()
            conn.close()
        except Exception as e:
            conn.rollback()
            conn.close()
            pass
    
    def renumber_vehicles(self):
        """Renumber vehicle IDs to be sequential (1, 2, 3...) based on alphabetical order"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get all vehicles ordered alphabetically by vehicle_number
            cursor.execute("SELECT id, vehicle_number, created_at FROM vehicles ORDER BY vehicle_number ASC")
            vehicles = cursor.fetchall()
            
            if not vehicles:
                conn.close()
                return
            
            # Create temporary table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vehicles_temp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_number TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert vehicles in alphabetical order with new IDs (1, 2, 3, ...)
            cursor.execute("DELETE FROM vehicles_temp")
            for new_id, (old_id, vehicle_number, created_at) in enumerate(vehicles, 1):
                cursor.execute("""
                    INSERT INTO vehicles_temp (id, vehicle_number, created_at)
                    VALUES (?, ?, ?)
                """, (new_id, vehicle_number, created_at))
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE vehicles")
            cursor.execute("ALTER TABLE vehicles_temp RENAME TO vehicles")
            
            conn.commit()
            conn.close()
        except Exception as e:
            conn.rollback()
            conn.close()
            pass
    
    def renumber_goods(self):
        """Renumber good IDs to be sequential (1, 2, 3...) based on alphabetical order by description"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get all goods ordered alphabetically by description (include category)
            cursor.execute("SELECT id, description, hsn_code, unit, rate, category, created_at, updated_at FROM goods ORDER BY description ASC")
            goods = cursor.fetchall()
            
            if not goods:
                conn.close()
                return
            
            # Create temporary table (include category column)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goods_temp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    hsn_code TEXT NOT NULL,
                    unit TEXT NOT NULL,
                    rate REAL NOT NULL,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert goods in alphabetical order with new IDs (1, 2, 3, ...) (include category)
            cursor.execute("DELETE FROM goods_temp")
            for new_id, (old_id, description, hsn_code, unit, rate, category, created_at, updated_at) in enumerate(goods, 1):
                cursor.execute("""
                    INSERT INTO goods_temp (id, description, hsn_code, unit, rate, category, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (new_id, description, hsn_code, unit, rate, category, created_at, updated_at))
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE goods")
            cursor.execute("ALTER TABLE goods_temp RENAME TO goods")
            
            conn.commit()
            conn.close()
        except Exception as e:
            conn.rollback()
            conn.close()
            pass
    
    # Vehicle operations
    def add_vehicle(self, vehicle_number: str) -> int:
        """Add a vehicle (common to all areas and categories)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO vehicles (vehicle_number)
                VALUES (?)
            """, (vehicle_number,))
            conn.commit()
            vehicle_id = cursor.lastrowid
            conn.close()
            return vehicle_id
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError(f"Vehicle '{vehicle_number}' already exists")
    
    def get_vehicles(self) -> List[Dict]:
        """Get all vehicles (common to all areas and categories)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM vehicles 
            ORDER BY vehicle_number ASC
        """)
        vehicles = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return vehicles
    
    def update_vehicle(self, vehicle_id: int, vehicle_number: str):
        """Update vehicle number"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE vehicles
                SET vehicle_number = ?
                WHERE id = ?
            """, (vehicle_number, vehicle_id))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError(f"Vehicle '{vehicle_number}' already exists")
        conn.close()
    
    def delete_vehicle(self, vehicle_id: int):
        """Delete a vehicle"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
        conn.commit()
        conn.close()
        # Renumber IDs after deletion
        self.renumber_vehicles()
    
    # Blaster operations
    def add_blaster(self, name: str, document_no: str = "", address: str = "") -> int:
        """Add a new blaster"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO blasters (name, document_no, address)
            VALUES (?, ?, ?)
        """, (name, document_no, address))
        conn.commit()
        blaster_id = cursor.lastrowid
        conn.close()
        return blaster_id
    
    def get_blasters(self) -> List[Dict]:
        """Get all blasters sorted alphabetically by name"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM blasters ORDER BY name ASC")
        blasters = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return blasters
    
    def get_blaster(self, blaster_id: int) -> Optional[Dict]:
        """Get blaster by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM blasters WHERE id = ?", (blaster_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def update_blaster(self, blaster_id: int, name: str, document_no: str = "", address: str = ""):
        """Update blaster details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE blasters 
            SET name = ?, document_no = ?, address = ?
            WHERE id = ?
        """, (name, document_no, address, blaster_id))
        conn.commit()
        conn.close()
    
    def delete_blaster(self, blaster_id: int):
        """Delete a blaster (sets customer blaster_id to NULL if they reference it)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Set customers' blaster_id to NULL if they reference this blaster
            cursor.execute("UPDATE customers SET blaster_id = NULL WHERE blaster_id = ?", (blaster_id,))
            # Delete the blaster
            cursor.execute("DELETE FROM blasters WHERE id = ?", (blaster_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
        
        # Renumber IDs after deletion (this will update customer references properly)
        self.renumber_blasters()
    
    def renumber_blasters(self):
        """Renumber blaster IDs to be sequential (1, 2, 3...) based on alphabetical order.
        Properly updates all customer references to maintain data integrity."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get all blasters ordered alphabetically by name
            cursor.execute("SELECT id, name, document_no, address, created_at FROM blasters ORDER BY name ASC")
            blasters = cursor.fetchall()
            
            if not blasters:
                conn.close()
                return
            
            # Create temporary table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blasters_temp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    document_no TEXT,
                    address TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Build mapping of old_id -> new_id
            id_mapping = {}
            cursor.execute("DELETE FROM blasters_temp")
            for new_id, (old_id, name, document_no, address, created_at) in enumerate(blasters, 1):
                id_mapping[old_id] = new_id
                cursor.execute("""
                    INSERT INTO blasters_temp (id, name, document_no, address, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (new_id, name, document_no, address, created_at))
            
            # Update customers table to use new blaster IDs (only if mapping exists)
            for old_id, new_id in id_mapping.items():
                if old_id != new_id:  # Only update if ID actually changed
                    cursor.execute("UPDATE customers SET blaster_id = ? WHERE blaster_id = ?", (new_id, old_id))
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE blasters")
            cursor.execute("ALTER TABLE blasters_temp RENAME TO blasters")
            
            conn.commit()
            
            # Clean up any orphaned references after renumbering
            cursor.execute("""
                UPDATE customers 
                SET blaster_id = NULL 
                WHERE blaster_id IS NOT NULL 
                AND blaster_id NOT IN (SELECT id FROM blasters)
            """)
            conn.commit()
            
            conn.close()
        except Exception as e:
            conn.rollback()
            conn.close()
            # Don't fail silently - log the error
            print(f"Error renumbering blasters: {e}")
            pass
    
    # Goods operations
    def add_good(self, description: str, hsn_code: str, unit: str, rate: float, category: str = None) -> int:
        """Add a new good"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO goods (description, hsn_code, unit, rate, category)
            VALUES (?, ?, ?, ?, ?)
        """, (description, hsn_code, unit, rate, category))
        conn.commit()
        good_id = cursor.lastrowid
        conn.close()
        return good_id
    
    def get_goods(self, category: str = None) -> List[Dict]:
        """Get all goods, optionally filtered by category"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if category:
            cursor.execute(
                "SELECT * FROM goods WHERE category = ? ORDER BY description ASC",
                (category,),
            )
        else:
            cursor.execute("SELECT * FROM goods ORDER BY description ASC")
        goods = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return goods
    
    def get_good(self, good_id: int) -> Optional[Dict]:
        """Get good by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM goods WHERE id = ?", (good_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def update_good_rate(self, good_id: int, rate: float):
        """Update good rate"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE goods 
            SET rate = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (rate, good_id))
        conn.commit()
        conn.close()
    
    def update_good(self, good_id: int, description: str, hsn_code: str, unit: str, rate: float, category: str = None):
        """Update all good fields"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE goods 
            SET description = ?, hsn_code = ?, unit = ?, rate = ?, category = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (description, hsn_code, unit, rate, category, good_id))
        conn.commit()
        conn.close()
    
    def delete_good(self, good_id: int):
        """Delete a good"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM goods WHERE id = ?", (good_id,))
        conn.commit()
        conn.close()
        # Renumber IDs after deletion
        self.renumber_goods()
    
    # Settings operations
    def get_setting(self, key: str, default: str = "") -> str:
        """Get a setting value"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else default
    
    def set_setting(self, key: str, value: str):
        """Set a setting value"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value)
            VALUES (?, ?)
        """, (key, value))
        conn.commit()
        conn.close()

