"""
Main GUI application for Delivery Bill Generator
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from database import Database
from pdf_generator import PDFGenerator
from number_to_words import number_to_words
import os

class DeliveryBillApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Delivery Bill Generator - Senthil Explosives")
        self.root.geometry("1200x900")
        
        # Initialize database
        self.db = Database()
        
        # Initialize PDF generator
        self.pdf_gen = PDFGenerator()
        
        # Current category (Detonator/Explosives)
        self.current_category = None
        
        # Current location
        self.current_location_id = None
        
        # Current customer
        self.current_customer = None
        
        # Items list
        self.items = []
        
        # Setup UI
        self.setup_ui()
        
        # Load default tax rates
        self.load_tax_rates()
    
    @staticmethod
    def make_dialog_visible(dialog):
        """Helper function to make dialogs visible on macOS"""
        dialog.lift()
        dialog.focus_force()
        dialog.attributes('-topmost', True)
        dialog.after(100, lambda: dialog.attributes('-topmost', False))
    
    def setup_ui(self):
        """Setup the user interface"""
        # Create scrollable frame
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add mouse wheel scrolling - improved for macOS trackpad
        def on_mousewheel(event):
            # macOS trackpad - check for num attribute first
            if hasattr(event, 'num'):
                if event.num == 4:
                    canvas.yview_scroll(-1, "units")
                    return
                elif event.num == 5:
                    canvas.yview_scroll(1, "units")
                    return
            # Windows/Linux with mouse wheel
            if hasattr(event, 'delta'):
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        # Bind scroll events to canvas
        canvas.bind("<MouseWheel>", on_mousewheel)
        canvas.bind("<Button-4>", on_mousewheel)
        canvas.bind("<Button-5>", on_mousewheel)
        
        # Also bind to scrollable_frame
        scrollable_frame.bind("<MouseWheel>", on_mousewheel)
        scrollable_frame.bind("<Button-4>", on_mousewheel)
        scrollable_frame.bind("<Button-5>", on_mousewheel)
        
        # Store canvas reference
        self.canvas = canvas
        
        # Store canvas reference
        self.canvas = canvas
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Main container (now inside scrollable frame)
        main_frame = ttk.Frame(scrollable_frame, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollable_frame.columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Delivery Bill Generator", 
                               font=('Helvetica', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Category Selection Frame
        category_frame = ttk.LabelFrame(main_frame, text="Select Category", padding="10")
        category_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.category_var = tk.StringVar()
        ttk.Radiobutton(category_frame, text="Detonator", variable=self.category_var,
                       value="Detonator", command=self.on_category_select).grid(row=0, column=0, padx=10)
        ttk.Radiobutton(category_frame, text="Explosives", variable=self.category_var,
                       value="Explosives", command=self.on_category_select).grid(row=0, column=1, padx=10)
        
        # Location Frame
        self.location_frame = ttk.LabelFrame(main_frame, text="Location of Interest", padding="10")
        self.location_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(self.location_frame, text="Location:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.location_combo = ttk.Combobox(self.location_frame, width=30, state="readonly")
        self.location_combo.grid(row=0, column=1, padx=5)
        self.location_combo.bind("<<ComboboxSelected>>", self.on_location_select)
        
        ttk.Button(self.location_frame, text="Add New Location", 
                  command=self.add_location).grid(row=0, column=2, padx=5)
        
        ttk.Label(self.location_frame, text="Vehicle No:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.vehicle_combo = ttk.Combobox(self.location_frame, width=30, state="readonly")
        self.vehicle_combo.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Button(self.location_frame, text="Add Vehicle", 
                  command=self.add_vehicle).grid(row=1, column=2, padx=5, pady=5)
        
        # Customer Frame
        customer_frame = ttk.LabelFrame(main_frame, text="Receiver Details", padding="10")
        customer_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(customer_frame, text="Customer:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.customer_combo = ttk.Combobox(customer_frame, width=40, state="readonly")
        self.customer_combo.grid(row=0, column=1, padx=5, pady=5)
        self.customer_combo.bind("<<ComboboxSelected>>", self.on_customer_select)
        
        ttk.Button(customer_frame, text="Add New Customer", 
                  command=self.add_customer).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(customer_frame, text="Edit Customer", 
                  command=self.edit_customer).grid(row=0, column=3, padx=5, pady=5)
        
        # Customer details fields
        self.customer_fields = {}
        fields = [
            ("Name", "name", 1), ("Address", "address", 2),
            ("SF.NO", "sf_no", 3), ("RC.NO", "rc_no", 4),
            ("State", "state", 5), ("GSTIN", "gstin", 6)
        ]
        
        for label, key, row in fields:
            ttk.Label(customer_frame, text=f"{label}:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
            entry = ttk.Entry(customer_frame, width=50)
            entry.grid(row=row, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=2)
            self.customer_fields[key] = entry
        
        # Invoice Details Frame
        invoice_frame = ttk.LabelFrame(main_frame, text="Invoice Details", padding="10")
        invoice_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(invoice_frame, text="Invoice No:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.invoice_no_entry = ttk.Entry(invoice_frame, width=30)
        self.invoice_no_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(invoice_frame, text="Date of Supply:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.date_entry = ttk.Entry(invoice_frame, width=20)
        self.date_entry.grid(row=0, column=3, padx=5, pady=5)
        self.date_entry.insert(0, datetime.now().strftime("%d-%m-%Y"))
        ttk.Button(invoice_frame, text="📅", command=self.select_date).grid(row=0, column=4, padx=5)
        
        ttk.Label(invoice_frame, text="E WAY BILL NO:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.e_way_bill_no_entry = ttk.Entry(invoice_frame, width=30)
        self.e_way_bill_no_entry.insert(0, "5019 3382 6386")
        self.e_way_bill_no_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(invoice_frame, text="Mode of Transport:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.transport_entry = ttk.Entry(invoice_frame, width=30)
        self.transport_entry.insert(0, "Road")
        self.transport_entry.grid(row=1, column=3, padx=5, pady=5)
        
        self.original_var = tk.BooleanVar()
        ttk.Checkbutton(invoice_frame, text="Original", variable=self.original_var).grid(row=1, column=4, padx=5, pady=5)
        
        ttk.Label(invoice_frame, text="E WAY DOCUMENT NO:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.e_way_document_no_entry = ttk.Entry(invoice_frame, width=30)
        self.e_way_document_no_entry.grid(row=2, column=1, padx=5, pady=5)
        
        self.duplicate_var = tk.BooleanVar()
        ttk.Checkbutton(invoice_frame, text="Duplicate", variable=self.duplicate_var).grid(row=2, column=4, padx=5, pady=5)
        
        self.triplicate_var = tk.BooleanVar()
        ttk.Checkbutton(invoice_frame, text="Triplicate", variable=self.triplicate_var).grid(row=3, column=4, padx=5, pady=5)
        
        ttk.Label(invoice_frame, text="Place of Supply:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.place_of_supply_entry = ttk.Entry(invoice_frame, width=30)
        self.place_of_supply_entry.grid(row=4, column=1, padx=5, pady=5)
        
        ttk.Label(invoice_frame, text="State Code:").grid(row=4, column=2, sticky=tk.W, padx=5, pady=5)
        self.state_code_entry = ttk.Entry(invoice_frame, width=15)
        self.state_code_entry.insert(0, "33")
        self.state_code_entry.grid(row=4, column=3, padx=5, pady=5)
        
        ttk.Label(invoice_frame, text="GSTIN/Unique ID:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.gstin_unique_entry = ttk.Entry(invoice_frame, width=30)
        self.gstin_unique_entry.grid(row=5, column=1, padx=5, pady=5)
        
        # Items Frame
        items_frame = ttk.LabelFrame(main_frame, text="Description of Goods", padding="10")
        items_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(5, weight=1)
        
        # Items treeview
        columns = ('sno', 'description', 'hsn', 'unit', 'qty', 'rate', 'total', 
                  'taxable', 'cgst_rate', 'cgst_rs', 'sgst_rate', 'sgst_rs', 
                  'igst_rate', 'igst_rs', 'total_amount')
        self.items_tree = ttk.Treeview(items_frame, columns=columns, show='headings', height=8)
        
        column_widths = {
            'sno': 40, 'description': 150, 'hsn': 80, 'unit': 60, 'qty': 60,
            'rate': 80, 'total': 80, 'taxable': 80, 'cgst_rate': 60, 'cgst_rs': 70,
            'sgst_rate': 60, 'sgst_rs': 70, 'igst_rate': 60, 'igst_rs': 70, 'total_amount': 90
        }
        
        headers = {
            'sno': 'S.No', 'description': 'Description', 'hsn': 'HSN', 'unit': 'Unit',
            'qty': 'Qty', 'rate': 'Rate', 'total': 'Total', 'taxable': 'Taxable Value',
            'cgst_rate': 'CGST %', 'cgst_rs': 'CGST Rs', 'sgst_rate': 'SGST %',
            'sgst_rs': 'SGST Rs', 'igst_rate': 'IGST %', 'igst_rs': 'IGST Rs', 'total_amount': 'Total Amount'
        }
        
        for col in columns:
            self.items_tree.heading(col, text=headers[col])
            self.items_tree.column(col, width=column_widths[col], anchor='center')
        
        scrollbar = ttk.Scrollbar(items_frame, orient=tk.VERTICAL, command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=scrollbar.set)
        self.items_tree.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=4, sticky=(tk.N, tk.S))
        items_frame.columnconfigure(0, weight=1)
        items_frame.rowconfigure(0, weight=1)
        
        # Item buttons
        item_btn_frame = ttk.Frame(items_frame)
        item_btn_frame.grid(row=1, column=0, columnspan=4, pady=5)
        
        ttk.Button(item_btn_frame, text="➕ Add Good", command=self.add_good_direct, 
                  style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(item_btn_frame, text="Add Item", command=self.add_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(item_btn_frame, text="Edit Item", command=self.edit_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(item_btn_frame, text="Delete Item", command=self.delete_item).pack(side=tk.LEFT, padx=5)
        
        # Totals Frame
        totals_frame = ttk.Frame(main_frame)
        totals_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(totals_frame, text="Freight Charges:").grid(row=0, column=0, padx=5)
        self.freight_entry = ttk.Entry(totals_frame, width=20)
        self.freight_entry.insert(0, "0")
        self.freight_entry.grid(row=0, column=1, padx=5)
        self.freight_entry.bind('<KeyRelease>', self.calculate_totals)
        
        ttk.Label(totals_frame, text="Grand Total:").grid(row=0, column=2, padx=5)
        self.grand_total_label = ttk.Label(totals_frame, text="0.00", font=('Helvetica', 12, 'bold'))
        self.grand_total_label.grid(row=0, column=3, padx=5)
        
        ttk.Label(totals_frame, text="Total in Words:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.total_words_entry = ttk.Entry(totals_frame, width=60)
        self.total_words_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        # Blaster Details Frame
        blaster_frame = ttk.LabelFrame(main_frame, text="Blaster Details", padding="10")
        blaster_frame.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(blaster_frame, text="Name of shot fire / Blaster:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.blaster_name_entry = ttk.Entry(blaster_frame, width=40)
        self.blaster_name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(blaster_frame, text="Document No:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.document_no_entry = ttk.Entry(blaster_frame, width=40)
        self.document_no_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(blaster_frame, text="Address:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.blaster_address_entry = ttk.Entry(blaster_frame, width=40)
        self.blaster_address_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # Action Buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=8, column=0, columnspan=2, pady=20)
        
        ttk.Button(action_frame, text="Generate PDF", command=self.generate_pdf, 
                  style='Accent.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(action_frame, text="Clear Form", command=self.clear_form).pack(side=tk.LEFT, padx=10)
        ttk.Button(action_frame, text="Add Good", command=self.add_good_direct).pack(side=tk.LEFT, padx=10)
        ttk.Button(action_frame, text="Manage Goods", command=self.manage_goods).pack(side=tk.LEFT, padx=10)
    
    def load_tax_rates(self):
        """Load default tax rates from database"""
        self.default_cgst_rate = float(self.db.get_setting('cgst_rate', '9.0'))
        self.default_sgst_rate = float(self.db.get_setting('sgst_rate', '9.0'))
    
    def on_category_select(self):
        """Handle category selection"""
        self.current_category = self.category_var.get()
        self.refresh_locations()
        self.location_combo.set('')
        self.vehicle_combo.set('')
        self.current_location_id = None
    
    def refresh_locations(self):
        """Refresh location combobox"""
        if not self.current_category:
            return
        locations = self.db.get_locations(self.current_category)
        location_names = [loc['name'] for loc in locations]
        self.location_combo['values'] = location_names
    
    def on_location_select(self, event=None):
        """Handle location selection"""
        location_name = self.location_combo.get()
        if not location_name or not self.current_category:
            return
        
        locations = self.db.get_locations(self.current_category)
        location = next((loc for loc in locations if loc['name'] == location_name), None)
        
        if location:
            self.current_location_id = location['id']
            self.refresh_vehicles()
    
    def refresh_vehicles(self):
        """Refresh vehicle combobox"""
        if not self.current_location_id:
            return
        vehicles = self.db.get_vehicles(self.current_location_id)
        vehicle_numbers = [v['vehicle_number'] for v in vehicles]
        self.vehicle_combo['values'] = vehicle_numbers
    
    def add_location(self):
        """Add a new location"""
        if not self.current_category:
            messagebox.showwarning("Warning", "Please select a category first")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Location")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()
        self.make_dialog_visible(dialog)
        
        ttk.Label(dialog, text="Location Name:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.grid(row=0, column=1, padx=10, pady=10)
        name_entry.focus()
        
        def save_location():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Location name cannot be empty")
                return
            try:
                self.db.add_location(name, self.current_category)
                messagebox.showinfo("Success", "Location added successfully")
                self.refresh_locations()
                self.location_combo.set(name)
                self.on_location_select()
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        
        ttk.Button(dialog, text="Save", command=save_location).grid(row=1, column=0, columnspan=2, pady=10)
        name_entry.bind('<Return>', lambda e: save_location())
    
    def add_vehicle(self):
        """Add a new vehicle"""
        if not self.current_location_id:
            messagebox.showwarning("Warning", "Please select a location first")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Vehicle")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()
        self.make_dialog_visible(dialog)
        
        ttk.Label(dialog, text="Vehicle Number:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        vehicle_entry = ttk.Entry(dialog, width=30)
        vehicle_entry.grid(row=0, column=1, padx=10, pady=10)
        vehicle_entry.focus()
        
        def save_vehicle():
            vehicle_no = vehicle_entry.get().strip()
            if not vehicle_no:
                messagebox.showerror("Error", "Vehicle number cannot be empty")
                return
            try:
                self.db.add_vehicle(self.current_location_id, vehicle_no)
                messagebox.showinfo("Success", "Vehicle added successfully")
                self.refresh_vehicles()
                self.vehicle_combo.set(vehicle_no)
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        
        ttk.Button(dialog, text="Save", command=save_vehicle).grid(row=1, column=0, columnspan=2, pady=10)
        vehicle_entry.bind('<Return>', lambda e: save_vehicle())
    
    def refresh_customers(self):
        """Refresh customer combobox"""
        customers = self.db.get_customers()
        customer_names = [c['name'] for c in customers]
        self.customer_combo['values'] = customer_names
    
    def on_customer_select(self, event=None):
        """Handle customer selection"""
        customer_name = self.customer_combo.get()
        if not customer_name:
            return
        
        customers = self.db.get_customers()
        customer = next((c for c in customers if c['name'] == customer_name), None)
        
        if customer:
            self.current_customer = customer
            self.customer_fields['name'].delete(0, tk.END)
            self.customer_fields['name'].insert(0, customer.get('name', ''))
            self.customer_fields['address'].delete(0, tk.END)
            self.customer_fields['address'].insert(0, customer.get('address', ''))
            self.customer_fields['sf_no'].delete(0, tk.END)
            self.customer_fields['sf_no'].insert(0, customer.get('sf_no', ''))
            self.customer_fields['rc_no'].delete(0, tk.END)
            self.customer_fields['rc_no'].insert(0, customer.get('rc_no', ''))
            self.customer_fields['state'].delete(0, tk.END)
            self.customer_fields['state'].insert(0, customer.get('state', ''))
            self.customer_fields['gstin'].delete(0, tk.END)
            self.customer_fields['gstin'].insert(0, customer.get('gstin', ''))
            
            # Auto-fill place of supply
            self.place_of_supply_entry.delete(0, tk.END)
            self.place_of_supply_entry.insert(0, customer.get('address', ''))
    
    def add_customer(self):
        """Add a new customer"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Customer")
        dialog.geometry("500x350")
        dialog.transient(self.root)
        dialog.grab_set()
        self.make_dialog_visible(dialog)
        
        fields = [
            ("Name *", "name"), ("Address", "address"),
            ("SF.NO", "sf_no"), ("RC.NO", "rc_no"),
            ("State", "state"), ("GSTIN", "gstin")
        ]
        
        entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(dialog, text=label).grid(row=idx, column=0, padx=10, pady=5, sticky=tk.W)
            entry = ttk.Entry(dialog, width=40)
            entry.grid(row=idx, column=1, padx=10, pady=5)
            entries[key] = entry
        
        entries['name'].focus()
        
        def save_customer():
            name = entries['name'].get().strip()
            if not name:
                messagebox.showerror("Error", "Customer name is required")
                return
            
            try:
                self.db.add_customer(
                    name,
                    entries['address'].get().strip(),
                    entries['sf_no'].get().strip(),
                    entries['rc_no'].get().strip(),
                    entries['state'].get().strip(),
                    entries['gstin'].get().strip()
                )
                messagebox.showinfo("Success", "Customer added successfully")
                self.refresh_customers()
                self.customer_combo.set(name)
                self.on_customer_select()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add customer: {str(e)}")
        
        ttk.Button(dialog, text="Save", command=save_customer).grid(row=len(fields), column=0, columnspan=2, pady=20)
        entries['name'].bind('<Return>', lambda e: entries['address'].focus())
    
    def edit_customer(self):
        """Edit selected customer"""
        if not self.current_customer:
            messagebox.showwarning("Warning", "Please select a customer to edit")
            return
        
        customer = self.current_customer
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Customer")
        dialog.geometry("500x350")
        dialog.transient(self.root)
        dialog.grab_set()
        self.make_dialog_visible(dialog)
        
        fields = [
            ("Name *", "name"), ("Address", "address"),
            ("SF.NO", "sf_no"), ("RC.NO", "rc_no"),
            ("State", "state"), ("GSTIN", "gstin")
        ]
        
        entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(dialog, text=label).grid(row=idx, column=0, padx=10, pady=5, sticky=tk.W)
            entry = ttk.Entry(dialog, width=40)
            entry.grid(row=idx, column=1, padx=10, pady=5)
            # Pre-fill with current values
            entry.insert(0, customer.get(key, ''))
            entries[key] = entry
        
        entries['name'].focus()
        
        def save_customer():
            name = entries['name'].get().strip()
            if not name:
                messagebox.showerror("Error", "Customer name is required")
                return
            
            try:
                self.db.update_customer(
                    customer['id'],
                    name,
                    entries['address'].get().strip(),
                    entries['sf_no'].get().strip(),
                    entries['rc_no'].get().strip(),
                    entries['state'].get().strip(),
                    entries['gstin'].get().strip()
                )
                messagebox.showinfo("Success", "Customer updated successfully")
                self.refresh_customers()
                self.customer_combo.set(name)
                self.on_customer_select()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update customer: {str(e)}")
        
        ttk.Button(dialog, text="Save", command=save_customer).grid(row=len(fields), column=0, columnspan=2, pady=20)
        entries['name'].bind('<Return>', lambda e: entries['address'].focus())
    
    def select_date(self):
        """Open date picker"""
        try:
            from tkcalendar import Calendar
            
            dialog = tk.Toplevel(self.root)
            dialog.title("Select Date")
            dialog.geometry("350x280")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # macOS-specific: Force dialog to front
            dialog.lift()
            dialog.focus_force()
            dialog.attributes('-topmost', True)
            dialog.after(100, lambda: dialog.attributes('-topmost', False))
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
            y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
            dialog.geometry(f"+{x}+{y}")
            
            # Make calendar bigger and more visible
            cal_frame = ttk.Frame(dialog)
            cal_frame.grid(row=0, column=0, padx=20, pady=20)
            
            # Use Calendar widget for better date selection
            cal = Calendar(cal_frame, selectmode='day', date_pattern='dd-mm-yyyy',
                          font=('Helvetica', 10), background='white',
                          foreground='black', selectbackground='blue',
                          selectforeground='white')
            cal.pack(padx=10, pady=10)
            
            def set_date():
                try:
                    selected_date = cal.get_date()
                    # Parse the date string
                    from datetime import datetime
                    date_obj = datetime.strptime(selected_date, "%d-%m-%Y")
                    self.date_entry.delete(0, tk.END)
                    self.date_entry.insert(0, date_obj.strftime("%d-%m-%Y"))
                    dialog.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Error setting date: {str(e)}")
            
            btn_frame = ttk.Frame(dialog)
            btn_frame.grid(row=1, column=0, pady=10)
            ttk.Button(btn_frame, text="OK", command=set_date, width=10).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)
            
            cal.focus()
        except ImportError:
            # Fallback to a simple date entry dialog
            dialog = tk.Toplevel(self.root)
            dialog.title("Enter Date")
            dialog.geometry("400x150")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # macOS-specific: Force dialog to front
            dialog.lift()
            dialog.focus_force()
            dialog.attributes('-topmost', True)
            dialog.after(100, lambda: dialog.attributes('-topmost', False))
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
            y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
            dialog.geometry(f"+{x}+{y}")
            
            ttk.Label(dialog, text="Enter date (DD-MM-YYYY):", font=('Helvetica', 10)).grid(row=0, column=0, padx=10, pady=15, sticky=tk.W)
            date_entry = ttk.Entry(dialog, width=25, font=('Helvetica', 11))
            date_entry.grid(row=0, column=1, padx=10, pady=15)
            date_entry.insert(0, self.date_entry.get())
            date_entry.focus()
            date_entry.select_range(0, tk.END)
            
            ttk.Label(dialog, text="Example: 25-12-2024", font=('Helvetica', 9), foreground='gray').grid(row=1, column=0, columnspan=2, pady=5)
            
            def set_date():
                date_str = date_entry.get().strip()
                # Basic validation
                try:
                    datetime.strptime(date_str, "%d-%m-%Y")
                    self.date_entry.delete(0, tk.END)
                    self.date_entry.insert(0, date_str)
                    dialog.destroy()
                except ValueError:
                    messagebox.showerror("Error", "Invalid date format. Please use DD-MM-YYYY (e.g., 25-12-2024)")
                    date_entry.focus()
            
            btn_frame = ttk.Frame(dialog)
            btn_frame.grid(row=2, column=0, columnspan=2, pady=15)
            ttk.Button(btn_frame, text="OK", command=set_date, width=10).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)
            
            date_entry.bind('<Return>', lambda e: set_date())
        except Exception as e:
            messagebox.showerror("Error", f"Error opening date picker: {str(e)}")
    
    def add_item(self):
        """Add a new item"""
        ItemDialog(self.root, self.db, self.default_cgst_rate, self.default_sgst_rate, 
                  callback=self.on_item_added)
    
    def on_item_added(self, item_data):
        """Handle item addition"""
        self.items.append(item_data)
        self.refresh_items_tree()
        self.calculate_totals()
    
    def edit_item(self):
        """Edit selected item"""
        selection = self.items_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to edit")
            return
        
        item_idx = self.items_tree.index(selection[0])
        if item_idx >= len(self.items):
            return
        
        item_data = self.items[item_idx].copy()
        ItemDialog(self.root, self.db, self.default_cgst_rate, self.default_sgst_rate,
                  item_data=item_data, callback=lambda new_data: self.on_item_edited(item_idx, new_data))
    
    def on_item_edited(self, idx, item_data):
        """Handle item edit"""
        self.items[idx] = item_data
        self.refresh_items_tree()
        self.calculate_totals()
    
    def delete_item(self):
        """Delete selected item"""
        selection = self.items_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to delete")
            return
        
        item_idx = self.items_tree.index(selection[0])
        if item_idx < len(self.items):
            self.items.pop(item_idx)
            self.refresh_items_tree()
            self.calculate_totals()
    
    def refresh_items_tree(self):
        """Refresh items treeview"""
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)
        
        for idx, item in enumerate(self.items, 1):
            values = (
                str(idx),
                item.get('description', ''),
                item.get('hsn_code', ''),
                item.get('unit', ''),
                str(item.get('qty', 0)),
                f"{item.get('rate', 0):.2f}",
                f"{item.get('total', 0):.2f}",
                f"{item.get('taxable_value', 0):.2f}",
                f"{item.get('cgst_rate', 0):.1f}%",
                f"{item.get('cgst_rs', 0):.2f}",
                f"{item.get('sgst_rate', 0):.1f}%",
                f"{item.get('sgst_rs', 0):.2f}",
                f"{item.get('igst_rate', 0):.1f}%" if item.get('igst_rate', 0) > 0 else "",
                f"{item.get('igst_rs', 0):.2f}" if item.get('igst_rs', 0) > 0 else "",
                f"{item.get('total_amount', 0):.2f}"
            )
            self.items_tree.insert('', tk.END, values=values)
    
    def _round_total(self, amount):
        """Round to nearest integer (if decimal < 0.5 round down, if >= 0.5 round up)"""
        import math
        return math.floor(amount) if (amount - math.floor(amount)) < 0.5 else math.ceil(amount)
    
    def calculate_totals(self, event=None):
        """Calculate grand total"""
        total = sum(item.get('total_amount', 0) for item in self.items)
        
        try:
            freight = float(self.freight_entry.get() or 0)
        except ValueError:
            freight = 0
        
        grand_total = total + freight
        
        # Round to nearest integer
        rounded_total = self._round_total(grand_total)
        
        self.grand_total_label.config(text=f"{rounded_total:.2f}")
        
        # Update total in words
        words = number_to_words(rounded_total)
        self.total_words_entry.delete(0, tk.END)
        self.total_words_entry.insert(0, words)
    
    def add_good_direct(self):
        """Add a good directly from main window"""
        print("DEBUG: add_good_direct() called")
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Good - Enter Product Details")
        dialog.geometry("500x320")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # macOS-specific: Force dialog to front
        dialog.lift()
        dialog.focus_force()
        dialog.attributes('-topmost', True)
        dialog.after(200, lambda: dialog.attributes('-topmost', False))
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        print(f"DEBUG: Add Good dialog created at position {x}, {y}")
        
        # Add a title label to make it more visible
        title_label = ttk.Label(dialog, text="ADD NEW GOOD", font=('Helvetica', 12, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=15, padx=10)
        
        ttk.Label(dialog, text="Description *:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        desc_entry = ttk.Entry(dialog, width=35)
        desc_entry.grid(row=1, column=1, padx=10, pady=10, sticky=(tk.W, tk.E))
        desc_entry.focus()
        
        ttk.Label(dialog, text="HSN Code *:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        hsn_entry = ttk.Entry(dialog, width=35)
        hsn_entry.grid(row=2, column=1, padx=10, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(dialog, text="Unit *:").grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        unit_combo = ttk.Combobox(dialog, width=32, values=['NOS', 'KG'], state="readonly")
        unit_combo.grid(row=3, column=1, padx=10, pady=10, sticky=tk.W)
        unit_combo.set('NOS')
        
        ttk.Label(dialog, text="Rate *:").grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)
        rate_entry = ttk.Entry(dialog, width=35)
        rate_entry.grid(row=4, column=1, padx=10, pady=10, sticky=(tk.W, tk.E))
        
        dialog.columnconfigure(1, weight=1)
        
        def save_good():
            description = desc_entry.get().strip()
            hsn_code = hsn_entry.get().strip()
            unit = unit_combo.get()
            
            if not description:
                messagebox.showerror("Error", "Description is required")
                desc_entry.focus()
                return
            
            if not hsn_code:
                messagebox.showerror("Error", "HSN Code is required")
                hsn_entry.focus()
                return
            
            try:
                rate = float(rate_entry.get())
                if rate <= 0:
                    raise ValueError("Rate must be greater than 0")
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid rate: {str(e)}\nPlease enter a valid number.")
                rate_entry.focus()
                return
            
            try:
                good_id = self.db.add_good(description, hsn_code, unit, rate)
                messagebox.showinfo("Success", f"Good added successfully!\nID: {good_id}")
                dialog.destroy()
            except Exception as e:
                error_msg = f"Failed to add good: {str(e)}\n\nPlease check:\n- All required fields are filled\n- Rate is a valid number\n- Database is accessible"
                messagebox.showerror("Error", error_msg)
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Save", command=save_good).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key to navigate/save
        desc_entry.bind('<Return>', lambda e: hsn_entry.focus())
        hsn_entry.bind('<Return>', lambda e: rate_entry.focus())
        rate_entry.bind('<Return>', lambda e: save_good())
    
    def manage_goods(self):
        """Open goods management window"""
        print("DEBUG: manage_goods() called")  # Debug print
        goods_manager = GoodsManager(self.root, self.db)
        print("DEBUG: GoodsManager window created")  # Debug print
    
    def generate_pdf(self):
        """Generate PDF invoice"""
        # Validate required fields
        if not self.current_category:
            messagebox.showerror("Error", "Please select a category")
            return
        
        if not self.current_location_id:
            messagebox.showerror("Error", "Please select a location")
            return
        
        if not self.customer_combo.get():
            messagebox.showerror("Error", "Please select a customer")
            return
        
        if not self.items:
            messagebox.showerror("Error", "Please add at least one item")
            return
        
        # Get customer details
        customer = {
            'name': self.customer_fields['name'].get(),
            'address': self.customer_fields['address'].get(),
            'sf_no': self.customer_fields['sf_no'].get(),
            'rc_no': self.customer_fields['rc_no'].get(),
            'state': self.customer_fields['state'].get(),
            'gstin': self.customer_fields['gstin'].get()
        }
        
        # Prepare invoice data
        invoice_data = {
            'invoice_number': self.invoice_no_entry.get(),
            'date_of_supply': self.date_entry.get(),
            'category': self.current_category,
            'location_name': self.location_combo.get(),
            'vehicle_number': self.vehicle_combo.get(),
            'customer': customer,
            'mode_of_transport': self.transport_entry.get(),
            'is_original': self.original_var.get(),
            'is_duplicate': self.duplicate_var.get(),
            'is_triplicate': self.triplicate_var.get(),
            'e_way_bill_no': self.e_way_bill_no_entry.get(),
            'e_way_document_no': self.e_way_document_no_entry.get(),
            'place_of_supply': self.place_of_supply_entry.get(),
            'state_code': self.state_code_entry.get(),
            'gstin_unique_id': self.gstin_unique_entry.get(),
            'items': self.items,
            'freight_charges': float(self.freight_entry.get() or 0),
            'grand_total': self._round_total(sum(item.get('total_amount', 0) for item in self.items) + float(self.freight_entry.get() or 0)),
            'total_in_words': self.total_words_entry.get(),
            'blaster_name': self.blaster_name_entry.get(),
            'document_no': self.document_no_entry.get(),
            'blaster_address': self.blaster_address_entry.get()
        }
        
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"Delivery_Bill_{invoice_data['invoice_number'] or 'Invoice'}.pdf"
        )
        
        if filename:
            try:
                self.pdf_gen.generate_pdf(invoice_data, filename)
                messagebox.showinfo("Success", f"PDF generated successfully!\nSaved to: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to generate PDF: {str(e)}")
    
    def clear_form(self):
        """Clear the form"""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear the form?"):
            self.category_var.set('')
            self.current_category = None
            self.location_combo.set('')
            self.vehicle_combo.set('')
            self.current_location_id = None
            self.customer_combo.set('')
            self.current_customer = None
            
            for field in self.customer_fields.values():
                field.delete(0, tk.END)
            
            self.invoice_no_entry.delete(0, tk.END)
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, datetime.now().strftime("%d-%m-%Y"))
            self.transport_entry.delete(0, tk.END)
            self.transport_entry.insert(0, "Road")
            self.original_var.set(False)
            self.duplicate_var.set(False)
            self.triplicate_var.set(False)
            self.e_way_bill_no_entry.delete(0, tk.END)
            self.e_way_bill_no_entry.insert(0, "5019 3382 6386")
            self.e_way_document_no_entry.delete(0, tk.END)
            self.place_of_supply_entry.delete(0, tk.END)
            self.state_code_entry.delete(0, tk.END)
            self.state_code_entry.insert(0, "33")
            self.gstin_unique_entry.delete(0, tk.END)
            
            self.items = []
            self.refresh_items_tree()
            
            self.freight_entry.delete(0, tk.END)
            self.freight_entry.insert(0, "0")
            self.grand_total_label.config(text="0.00")
            self.total_words_entry.delete(0, tk.END)
            
            self.blaster_name_entry.delete(0, tk.END)
            self.document_no_entry.delete(0, tk.END)
            self.blaster_address_entry.delete(0, tk.END)


class ItemDialog:
    """Dialog for adding/editing items"""
    def __init__(self, parent, db, default_cgst_rate, default_sgst_rate, item_data=None, callback=None):
        self.db = db
        self.default_cgst_rate = default_cgst_rate
        self.default_sgst_rate = default_sgst_rate
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add/Edit Item" if not item_data else "Edit Item")
        self.dialog.geometry("650x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        # macOS-specific: Force dialog to front
        self.dialog.lift()
        self.dialog.focus_force()
        self.dialog.attributes('-topmost', True)
        self.dialog.after(100, lambda: self.dialog.attributes('-topmost', False))
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Create scrollable frame for the dialog
        dialog_canvas = tk.Canvas(self.dialog)
        dialog_scrollbar = ttk.Scrollbar(self.dialog, orient="vertical", command=dialog_canvas.yview)
        dialog_scrollable = ttk.Frame(dialog_canvas)
        
        dialog_scrollable.bind(
            "<Configure>",
            lambda e: dialog_canvas.configure(scrollregion=dialog_canvas.bbox("all"))
        )
        
        dialog_canvas.create_window((0, 0), window=dialog_scrollable, anchor="nw")
        dialog_canvas.configure(yscrollcommand=dialog_scrollbar.set)
        
        # Add mouse wheel scrolling to dialog
        def dialog_scroll(event):
            if hasattr(event, 'delta'):
                dialog_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif hasattr(event, 'num'):
                if event.num == 4:
                    dialog_canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    dialog_canvas.yview_scroll(1, "units")
        
        dialog_canvas.bind("<MouseWheel>", dialog_scroll)
        dialog_canvas.bind("<Button-4>", dialog_scroll)
        dialog_canvas.bind("<Button-5>", dialog_scroll)
        dialog_scrollable.bind("<MouseWheel>", dialog_scroll)
        dialog_scrollable.bind("<Button-4>", dialog_scroll)
        dialog_scrollable.bind("<Button-5>", dialog_scroll)
        
        dialog_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        dialog_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        dialog_scrollable.columnconfigure(1, weight=1)
        
        # Good selection
        ttk.Label(dialog_scrollable, text="Select Good:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.good_combo = ttk.Combobox(dialog_scrollable, width=40, state="readonly")
        self.good_combo.grid(row=0, column=1, padx=10, pady=10)
        self.good_combo.bind("<<ComboboxSelected>>", self.on_good_select)
        self.refresh_goods()
        
        ttk.Button(dialog_scrollable, text="New Good", command=self.add_good).grid(row=0, column=2, padx=10)
        
        # Store reference to scrollable frame
        self.dialog_scrollable = dialog_scrollable
        
        # Item fields
        self.fields = {}
        field_configs = [
            ("Description *", "description", 1),
            ("HSN Code *", "hsn_code", 2),
            ("Unit *", "unit", 3),
            ("Qty *", "qty", 4),
            ("Rate *", "rate", 5),
            ("Total", "total", 6),
            ("Taxable Value", "taxable_value", 7),
            ("CGST Rate %", "cgst_rate", 8),
            ("CGST Rs", "cgst_rs", 9),
            ("SGST Rate %", "sgst_rate", 10),
            ("SGST Rs", "sgst_rs", 11),
            ("IGST Rate %", "igst_rate", 12),
            ("IGST Rs", "igst_rs", 13),
            ("Total Amount", "total_amount", 14)
        ]
        
        for label, key, row in field_configs:
            ttk.Label(dialog_scrollable, text=label).grid(row=row, column=0, padx=10, pady=5, sticky=tk.W)
            
            if key == 'unit':
                entry = ttk.Combobox(dialog_scrollable, width=30, values=['NOS', 'KG'], state="readonly")
            else:
                entry = ttk.Entry(dialog_scrollable, width=30)
            
            entry.grid(row=row, column=1, padx=10, pady=5)
            self.fields[key] = entry
            
            if key in ['qty', 'rate', 'taxable_value', 'cgst_rate', 'sgst_rate', 'igst_rate']:
                entry.bind('<KeyRelease>', self.calculate_item)
        
        # Pre-fill if editing
        if item_data:
            self.fields['description'].insert(0, item_data.get('description', ''))
            self.fields['hsn_code'].insert(0, item_data.get('hsn_code', ''))
            self.fields['unit'].set(item_data.get('unit', 'NOS'))
            self.fields['qty'].insert(0, str(item_data.get('qty', 0)))
            self.fields['rate'].insert(0, str(item_data.get('rate', 0)))
            self.fields['taxable_value'].insert(0, str(item_data.get('taxable_value', 0)))
            self.fields['cgst_rate'].insert(0, str(item_data.get('cgst_rate', default_cgst_rate)))
            self.fields['sgst_rate'].insert(0, str(item_data.get('sgst_rate', default_sgst_rate)))
            self.fields['igst_rate'].insert(0, str(item_data.get('igst_rate', 0)))
            self.calculate_item()
        else:
            self.fields['cgst_rate'].insert(0, str(default_cgst_rate))
            self.fields['sgst_rate'].insert(0, str(default_sgst_rate))
            self.fields['igst_rate'].insert(0, "0")
            # Trigger initial calculation after fields are set
            self.dialog.after(100, self.calculate_item)
        
        # Add separator line
        separator = ttk.Separator(dialog_scrollable, orient='horizontal')
        separator.grid(row=15, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        
        # Buttons - make them more visible and prominent
        btn_frame = ttk.Frame(dialog_scrollable)
        btn_frame.grid(row=16, column=0, columnspan=3, pady=25, sticky=(tk.W, tk.E))
        
        # Make Save button prominent
        save_btn = ttk.Button(btn_frame, text="✅ Save & Add to Bill", command=self.save_item)
        save_btn.pack(side=tk.LEFT, padx=15, ipadx=15, ipady=8)
        ttk.Button(btn_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.LEFT, padx=10, ipadx=10, ipady=5)
        
        # Make dialog scrollable if needed
        self.dialog.update_idletasks()
    
    def refresh_goods(self):
        """Refresh goods combobox"""
        goods = self.db.get_goods()
        good_names = [f"{g['description']} ({g['hsn_code']})" for g in goods]
        self.good_combo['values'] = good_names
    
    def on_good_select(self, event=None):
        """Handle good selection"""
        selection = self.good_combo.get()
        if not selection:
            return
        
        # Extract description from selection
        description = selection.split(' (')[0]
        goods = self.db.get_goods()
        good = next((g for g in goods if g['description'] == description), None)
        
        if good:
            self.fields['description'].delete(0, tk.END)
            self.fields['description'].insert(0, good['description'])
            self.fields['hsn_code'].delete(0, tk.END)
            self.fields['hsn_code'].insert(0, good['hsn_code'])
            self.fields['unit'].set(good['unit'])
            self.fields['rate'].delete(0, tk.END)
            self.fields['rate'].insert(0, str(good['rate']))
            # Set taxable value to match total (will be calculated)
            # Trigger calculation after a brief delay to ensure fields are set
            self.dialog.after(100, self.calculate_item)
    
    def add_good(self):
        """Add a new good"""
        dialog = tk.Toplevel(self.dialog)
        dialog.title("Add Good")
        dialog.geometry("450x280")
        dialog.transient(self.dialog)
        dialog.grab_set()
        
        # macOS-specific: Force dialog to front
        dialog.lift()
        dialog.focus_force()
        dialog.attributes('-topmost', True)
        dialog.after(100, lambda: dialog.attributes('-topmost', False))
        dialog.update_idletasks()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        ttk.Label(dialog, text="Description *:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        desc_entry = ttk.Entry(dialog, width=35)
        desc_entry.grid(row=0, column=1, padx=10, pady=10, sticky=(tk.W, tk.E))
        desc_entry.focus()
        
        ttk.Label(dialog, text="HSN Code *:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        hsn_entry = ttk.Entry(dialog, width=35)
        hsn_entry.grid(row=1, column=1, padx=10, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(dialog, text="Unit *:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        unit_combo = ttk.Combobox(dialog, width=32, values=['NOS', 'KG'], state="readonly")
        unit_combo.grid(row=2, column=1, padx=10, pady=10, sticky=tk.W)
        unit_combo.set('NOS')
        
        ttk.Label(dialog, text="Rate *:").grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        rate_entry = ttk.Entry(dialog, width=35)
        rate_entry.grid(row=3, column=1, padx=10, pady=10, sticky=(tk.W, tk.E))
        
        dialog.columnconfigure(1, weight=1)
        
        def save_good():
            description = desc_entry.get().strip()
            hsn_code = hsn_entry.get().strip()
            unit = unit_combo.get()
            
            if not description:
                messagebox.showerror("Error", "Description is required")
                desc_entry.focus()
                return
            
            if not hsn_code:
                messagebox.showerror("Error", "HSN Code is required")
                hsn_entry.focus()
                return
            
            try:
                rate = float(rate_entry.get())
                if rate <= 0:
                    raise ValueError("Rate must be greater than 0")
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid rate: {str(e)}\nPlease enter a valid number.")
                rate_entry.focus()
                return
            
            try:
                good_id = self.db.add_good(description, hsn_code, unit, rate)
                messagebox.showinfo("Success", f"Good added successfully!\nID: {good_id}")
                # Refresh goods list
                self.refresh_goods()
                # Set the combo to the new good and trigger selection
                good_display = f"{description} ({hsn_code})"
                self.good_combo.set(good_display)
                # Trigger the selection event to auto-fill fields
                self.on_good_select()
                dialog.destroy()
            except Exception as e:
                error_msg = f"Failed to add good: {str(e)}\n\nPlease check:\n- All required fields are filled\n- Rate is a valid number\n- Database is accessible"
                messagebox.showerror("Error", error_msg)
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Save", command=save_good).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key to save
        desc_entry.bind('<Return>', lambda e: hsn_entry.focus())
        hsn_entry.bind('<Return>', lambda e: unit_combo.focus())
        rate_entry.bind('<Return>', lambda e: save_good())
    
    def calculate_item(self, event=None):
        """Calculate item totals"""
        try:
            qty = float(self.fields['qty'].get() or 0)
            rate = float(self.fields['rate'].get() or 0)
            total = qty * rate
            
            self.fields['total'].delete(0, tk.END)
            self.fields['total'].insert(0, f"{total:.2f}")
            
            # Taxable value - always copy from total when total changes, but keep editable
            # Only auto-update if the field is empty or matches the old total
            taxable_value_str = self.fields['taxable_value'].get().strip()
            old_total_str = getattr(self, '_last_total', '0')
            
            # If taxable value is empty or matches old total, update it to new total
            if not taxable_value_str or taxable_value_str == old_total_str:
                taxable_value = total
                self.fields['taxable_value'].delete(0, tk.END)
                self.fields['taxable_value'].insert(0, f"{total:.2f}")
            else:
                # User has manually edited it, keep their value
                try:
                    taxable_value = float(taxable_value_str)
                except ValueError:
                    taxable_value = total
                    self.fields['taxable_value'].delete(0, tk.END)
                    self.fields['taxable_value'].insert(0, f"{total:.2f}")
            
            # Store current total for next calculation
            self._last_total = f"{total:.2f}"
            
            # CGST
            cgst_rate_str = self.fields['cgst_rate'].get().strip()
            cgst_rate = float(cgst_rate_str) if cgst_rate_str else 0
            cgst_rs = (taxable_value * cgst_rate) / 100 if cgst_rate > 0 else 0
            
            self.fields['cgst_rs'].delete(0, tk.END)
            self.fields['cgst_rs'].insert(0, f"{cgst_rs:.2f}")
            
            # SGST
            sgst_rate_str = self.fields['sgst_rate'].get().strip()
            sgst_rate = float(sgst_rate_str) if sgst_rate_str else 0
            sgst_rs = (taxable_value * sgst_rate) / 100 if sgst_rate > 0 else 0
            
            self.fields['sgst_rs'].delete(0, tk.END)
            self.fields['sgst_rs'].insert(0, f"{sgst_rs:.2f}")
            
            # IGST
            igst_rate_str = self.fields['igst_rate'].get().strip()
            igst_rate = float(igst_rate_str) if igst_rate_str else 0
            igst_rs = (taxable_value * igst_rate) / 100 if igst_rate > 0 else 0
            
            self.fields['igst_rs'].delete(0, tk.END)
            if igst_rs > 0:
                self.fields['igst_rs'].insert(0, f"{igst_rs:.2f}")
            
            # Total Amount
            total_amount = total + cgst_rs + sgst_rs + igst_rs
            
            self.fields['total_amount'].delete(0, tk.END)
            self.fields['total_amount'].insert(0, f"{total_amount:.2f}")
        except ValueError:
            pass
    
    def save_item(self):
        """Save item"""
        try:
            description = self.fields['description'].get().strip()
            hsn_code = self.fields['hsn_code'].get().strip()
            unit = self.fields['unit'].get()
            qty = float(self.fields['qty'].get() or 0)
            rate = float(self.fields['rate'].get() or 0)
            taxable_value = float(self.fields['taxable_value'].get() or 0)
            cgst_rate = float(self.fields['cgst_rate'].get() or 0)
            cgst_rs = float(self.fields['cgst_rs'].get() or 0)
            sgst_rate = float(self.fields['sgst_rate'].get() or 0)
            sgst_rs = float(self.fields['sgst_rs'].get() or 0)
            igst_rate = float(self.fields['igst_rate'].get() or 0)
            igst_rs = float(self.fields['igst_rs'].get() or 0)
            total_amount = float(self.fields['total_amount'].get() or 0)
            
            if not description or not hsn_code or qty <= 0 or rate <= 0:
                messagebox.showerror("Error", "Please fill all required fields")
                return
            
            # Update default tax rates if changed
            if cgst_rate != self.default_cgst_rate:
                self.db.set_setting('cgst_rate', str(cgst_rate))
                self.default_cgst_rate = cgst_rate
            
            if sgst_rate != self.default_sgst_rate:
                self.db.set_setting('sgst_rate', str(sgst_rate))
                self.default_sgst_rate = sgst_rate
            
            item_data = {
                'description': description,
                'hsn_code': hsn_code,
                'unit': unit,
                'qty': qty,
                'rate': rate,
                'total': qty * rate,
                'taxable_value': taxable_value,
                'cgst_rate': cgst_rate,
                'cgst_rs': cgst_rs,
                'sgst_rate': sgst_rate,
                'sgst_rs': sgst_rs,
                'igst_rate': igst_rate,
                'igst_rs': igst_rs,
                'total_amount': total_amount
            }
            
            if self.callback:
                self.callback(item_data)
            
            self.dialog.destroy()
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")


class GoodsManager:
    """Window for managing goods"""
    def __init__(self, parent, db):
        self.db = db
        
        self.window = tk.Toplevel(parent)
        self.window.title("Manage Goods")
        self.window.geometry("800x500")
        self.window.transient(parent)
        
        # macOS-specific: Force window to front
        self.window.lift()
        self.window.focus_force()
        self.window.attributes('-topmost', True)
        self.window.after(100, lambda: self.window.attributes('-topmost', False))
        
        # Treeview
        columns = ('id', 'description', 'hsn_code', 'unit', 'rate')
        self.tree = ttk.Treeview(self.window, columns=columns, show='headings', height=15)
        
        self.tree.heading('id', text='ID')
        self.tree.heading('description', text='Description')
        self.tree.heading('hsn_code', text='HSN Code')
        self.tree.heading('unit', text='Unit')
        self.tree.heading('rate', text='Rate')
        
        self.tree.column('id', width=50)
        self.tree.column('description', width=300)
        self.tree.column('hsn_code', width=150)
        self.tree.column('unit', width=100)
        self.tree.column('rate', width=100)
        
        self.tree.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        
        # Buttons
        btn_frame = ttk.Frame(self.window)
        btn_frame.grid(row=1, column=0, columnspan=3, pady=10)
        
        ttk.Button(btn_frame, text="Add Good", command=self.add_good).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Edit Good", command=self.edit_good).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Good", command=self.delete_good).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_tree).pack(side=tk.LEFT, padx=5)
        
        self.refresh_tree()
    
    def refresh_tree(self):
        """Refresh goods tree"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        goods = self.db.get_goods()
        for good in goods:
            self.tree.insert('', tk.END, values=(
                good['id'],
                good['description'],
                good['hsn_code'],
                good['unit'],
                f"{good['rate']:.2f}"
            ))
    
    def add_good(self):
        """Add a new good"""
        print("DEBUG: add_good() called")  # Debug print
        dialog = tk.Toplevel(self.window)
        dialog.title("Add Good - Enter Product Details")
        dialog.geometry("500x320")
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Make dialog very visible on macOS
        dialog.lift()
        dialog.focus_force()
        dialog.attributes('-topmost', True)
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Remove topmost after a moment but keep it visible
        dialog.after(200, lambda: dialog.attributes('-topmost', False))
        
        print(f"DEBUG: Dialog created at position {x}, {y}")  # Debug print
        print(f"DEBUG: Dialog size: {dialog.winfo_width()}x{dialog.winfo_height()}")  # Debug print
        
        # Add a title label to make it more visible
        title_label = ttk.Label(dialog, text="ADD NEW GOOD", font=('Helvetica', 12, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=15, padx=10)
        
        ttk.Label(dialog, text="Description *:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        desc_entry = ttk.Entry(dialog, width=35)
        desc_entry.grid(row=1, column=1, padx=10, pady=10, sticky=(tk.W, tk.E))
        desc_entry.focus()
        
        ttk.Label(dialog, text="HSN Code *:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        hsn_entry = ttk.Entry(dialog, width=35)
        hsn_entry.grid(row=2, column=1, padx=10, pady=10, sticky=(tk.W, tk.E))
        
        ttk.Label(dialog, text="Unit *:").grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        unit_combo = ttk.Combobox(dialog, width=32, values=['NOS', 'KG'], state="readonly")
        unit_combo.grid(row=3, column=1, padx=10, pady=10, sticky=tk.W)
        unit_combo.set('NOS')
        
        ttk.Label(dialog, text="Rate *:").grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)
        rate_entry = ttk.Entry(dialog, width=35)
        rate_entry.grid(row=4, column=1, padx=10, pady=10, sticky=(tk.W, tk.E))
        
        dialog.columnconfigure(1, weight=1)
        
        def save_good():
            description = desc_entry.get().strip()
            hsn_code = hsn_entry.get().strip()
            unit = unit_combo.get()
            
            if not description:
                messagebox.showerror("Error", "Description is required")
                desc_entry.focus()
                return
            
            if not hsn_code:
                messagebox.showerror("Error", "HSN Code is required")
                hsn_entry.focus()
                return
            
            try:
                rate = float(rate_entry.get())
                if rate <= 0:
                    raise ValueError("Rate must be greater than 0")
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid rate: {str(e)}\nPlease enter a valid number.")
                rate_entry.focus()
                return
            
            try:
                good_id = self.db.add_good(description, hsn_code, unit, rate)
                messagebox.showinfo("Success", f"Good added successfully!\nID: {good_id}")
                self.refresh_tree()
                dialog.destroy()
            except Exception as e:
                error_msg = f"Failed to add good: {str(e)}\n\nPlease check:\n- All required fields are filled\n- Rate is a valid number\n- Database is accessible"
                messagebox.showerror("Error", error_msg)
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Save", command=save_good).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key to navigate/save
        desc_entry.bind('<Return>', lambda e: hsn_entry.focus())
        hsn_entry.bind('<Return>', lambda e: rate_entry.focus())
        rate_entry.bind('<Return>', lambda e: save_good())
    
    def edit_good(self, good_id=None):
        """Edit a good"""
        if good_id is None:
            selection = self.tree.selection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a good to edit")
                return
            good_id = self.tree.item(selection[0])['values'][0]
        
        good = self.db.get_good(good_id)
        
        dialog = tk.Toplevel(self.window)
        dialog.title("Edit Good" if good else "Add Good")
        dialog.geometry("400x250")
        dialog.transient(self.window)
        dialog.grab_set()
        # macOS-specific: Force dialog to front
        dialog.lift()
        dialog.focus_force()
        dialog.attributes('-topmost', True)
        dialog.after(100, lambda: dialog.attributes('-topmost', False))
        
        ttk.Label(dialog, text="Description *:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        desc_entry = ttk.Entry(dialog, width=30)
        desc_entry.grid(row=0, column=1, padx=10, pady=10)
        if good:
            desc_entry.insert(0, good['description'])
        desc_entry.focus()
        
        ttk.Label(dialog, text="HSN Code *:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        hsn_entry = ttk.Entry(dialog, width=30)
        hsn_entry.grid(row=1, column=1, padx=10, pady=10)
        if good:
            hsn_entry.insert(0, good['hsn_code'])
        
        ttk.Label(dialog, text="Unit *:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        unit_combo = ttk.Combobox(dialog, width=27, values=['NOS', 'KG'], state="readonly")
        unit_combo.grid(row=2, column=1, padx=10, pady=10)
        if good:
            unit_combo.set(good['unit'])
        else:
            unit_combo.set('NOS')
        
        ttk.Label(dialog, text="Rate *:").grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        rate_entry = ttk.Entry(dialog, width=30)
        rate_entry.grid(row=3, column=1, padx=10, pady=10)
        if good:
            rate_entry.insert(0, str(good['rate']))
        
        def save_good():
            description = desc_entry.get().strip()
            hsn_code = hsn_entry.get().strip()
            unit = unit_combo.get()
            try:
                rate = float(rate_entry.get())
            except ValueError:
                messagebox.showerror("Error", "Invalid rate")
                return
            
            if not description or not hsn_code:
                messagebox.showerror("Error", "Description and HSN code are required")
                return
            
            try:
                if good:
                    # Update existing good - update all fields
                    self.db.update_good(good_id, description, hsn_code, unit, rate)
                    messagebox.showinfo("Success", "Good updated successfully")
                else:
                    # Add new good
                    self.db.add_good(description, hsn_code, unit, rate)
                    messagebox.showinfo("Success", "Good added successfully")
                self.refresh_tree()
                dialog.destroy()
            except Exception as e:
                error_msg = f"Failed to save good: {str(e)}\n\nPlease check:\n- All fields are filled\n- Rate is a valid number\n- Database is accessible"
                messagebox.showerror("Error", error_msg)
        
        ttk.Button(dialog, text="Save", command=save_good).grid(row=4, column=0, columnspan=2, pady=20)
    
    def delete_good(self):
        """Delete a good"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a good to delete")
            return
        
        good_id = self.tree.item(selection[0])['values'][0]
        good_desc = self.tree.item(selection[0])['values'][1]
        
        if messagebox.askyesno("Confirm", f"Delete good '{good_desc}'?"):
            # Note: In a real app, you'd want to check if the good is used in any invoices
            # For now, we'll just delete it
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM goods WHERE id = ?", (good_id,))
            conn.commit()
            conn.close()
            self.refresh_tree()


if __name__ == "__main__":
    root = tk.Tk()
    app = DeliveryBillApp(root)
    
    # Refresh customers on startup
    app.refresh_customers()
    
    root.mainloop()

