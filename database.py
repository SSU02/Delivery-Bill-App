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
        
        # Locations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                category TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Vehicles table (linked to locations)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id INTEGER NOT NULL,
                vehicle_number TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (location_id) REFERENCES locations(id),
                UNIQUE(location_id, vehicle_number)
            )
        """)
        
        # Goods table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                hsn_code TEXT NOT NULL,
                unit TEXT NOT NULL,
                rate REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
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
        
        conn.commit()
        conn.close()
    
    # Customer operations
    def add_customer(self, name: str, address: str = "", sf_no: str = "", 
                     rc_no: str = "", state: str = "", gstin: str = "") -> int:
        """Add a new customer"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO customers (name, address, sf_no, rc_no, state, gstin)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, address, sf_no, rc_no, state, gstin))
        conn.commit()
        customer_id = cursor.lastrowid
        conn.close()
        return customer_id
    
    def get_customers(self) -> List[Dict]:
        """Get all customers sorted alphabetically"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers ORDER BY name ASC")
        customers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return customers
    
    def get_customer(self, customer_id: int) -> Optional[Dict]:
        """Get customer by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def update_customer(self, customer_id: int, name: str, address: str = "",
                       sf_no: str = "", rc_no: str = "", state: str = "", gstin: str = ""):
        """Update customer details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE customers 
            SET name = ?, address = ?, sf_no = ?, rc_no = ?, state = ?, gstin = ?
            WHERE id = ?
        """, (name, address, sf_no, rc_no, state, gstin, customer_id))
        conn.commit()
        conn.close()
    
    # Location operations
    def add_location(self, name: str, category: str) -> int:
        """Add a new location"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO locations (name, category)
                VALUES (?, ?)
            """, (name, category))
            conn.commit()
            location_id = cursor.lastrowid
            conn.close()
            return location_id
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError(f"Location '{name}' already exists")
    
    def get_locations(self, category: str = None) -> List[Dict]:
        """Get all locations, optionally filtered by category"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if category:
            cursor.execute("SELECT * FROM locations WHERE category = ? ORDER BY name ASC", (category,))
        else:
            cursor.execute("SELECT * FROM locations ORDER BY name ASC")
        locations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return locations
    
    # Vehicle operations
    def add_vehicle(self, location_id: int, vehicle_number: str) -> int:
        """Add a vehicle to a location"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO vehicles (location_id, vehicle_number)
                VALUES (?, ?)
            """, (location_id, vehicle_number))
            conn.commit()
            vehicle_id = cursor.lastrowid
            conn.close()
            return vehicle_id
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError(f"Vehicle '{vehicle_number}' already exists for this location")
    
    def get_vehicles(self, location_id: int) -> List[Dict]:
        """Get all vehicles for a location"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM vehicles 
            WHERE location_id = ? 
            ORDER BY vehicle_number ASC
        """, (location_id,))
        vehicles = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return vehicles
    
    # Goods operations
    def add_good(self, description: str, hsn_code: str, unit: str, rate: float) -> int:
        """Add a new good"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO goods (description, hsn_code, unit, rate)
            VALUES (?, ?, ?, ?)
        """, (description, hsn_code, unit, rate))
        conn.commit()
        good_id = cursor.lastrowid
        conn.close()
        return good_id
    
    def get_goods(self) -> List[Dict]:
        """Get all goods"""
        conn = self.get_connection()
        cursor = conn.cursor()
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
    
    def update_good(self, good_id: int, description: str, hsn_code: str, unit: str, rate: float):
        """Update all good fields"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE goods 
            SET description = ?, hsn_code = ?, unit = ?, rate = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (description, hsn_code, unit, rate, good_id))
        conn.commit()
        conn.close()
    
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

