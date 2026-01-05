"""
Batch Processing GUI for Delivery Bill Generator
New workflow for processing multiple customers at once
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from database import Database
from pdf_generator import PDFGenerator
from number_to_words import number_to_words
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate
import os
import re


class BatchDeliveryBillApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Batch Delivery Bill Generator - Senthil Explosives")
        self.root.geometry("1400x900")
        
        # Force light theme - set background color to override system theme
        self.root.configure(bg='#ffffff')
        
        # Initialize database
        self.db = Database()
        
        # Initialize PDF generator
        self.pdf_gen = PDFGenerator()
        
        # Current state
        self.current_category = None
        self.current_area_id = None
        self.current_area_name = None
        
        # Selected customers data: {customer_id: {'invoice_no': '', 'e_way_doc_no': '', 'items': [], ...}}
        self.selected_customers = {}
        # Track which customer's details are currently displayed
        self.expanded_customer_id = None
        
        # Auto-increment counters
        self.current_invoice_number = ""
        self.current_e_way_doc_number = ""
        
        # Settings at area level
        self.date_of_supply = ""
        self.selected_vehicle = ""
        self.mode_of_transport = "Road"
        self.is_original = False
        self.is_duplicate = False
        self.is_triplicate = False
        self.e_way_bill_no = "5019 3382 6386"
        
        # Default tax rates
        self.default_cgst_rate = 9.0
        self.default_sgst_rate = 9.0
        
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
    
    def load_tax_rates(self):
        """Load default tax rates from database"""
        self.default_cgst_rate = float(self.db.get_setting('cgst_rate', '9.0'))
        self.default_sgst_rate = float(self.db.get_setting('sgst_rate', '9.0'))
    
    def setup_ui(self):
        """Setup the user interface"""
        # Configure ttk styles for light theme
        style = ttk.Style()
        style.theme_use('clam')  # Use a theme that supports color customization
        style.configure('TFrame', background='#ffffff')
        style.configure('TLabelFrame', background='#ffffff', foreground='#212529')
        style.configure('TLabel', background='#ffffff', foreground='#212529')
        style.configure('TButton', background='#f8f9fa', foreground='#212529')
        style.map('TButton', background=[('active', '#e9ecef')])
        style.configure('TEntry', fieldbackground='#ffffff', foreground='#212529')
        style.configure('TCombobox', fieldbackground='#ffffff', foreground='#212529')
        style.configure('TCanvas', background='#ffffff')
        
        # Create main container
        main_container = tk.Frame(self.root, bg='#ffffff')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top section: Category and Area selection
        top_frame = ttk.LabelFrame(main_container, text="Category & Area Selection", padding="10")
        top_frame.pack(fill=tk.X, pady=5)
        
        # Category selection
        ttk.Label(top_frame, text="Category:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.category_var = tk.StringVar()
        category_frame = ttk.Frame(top_frame)
        category_frame.grid(row=0, column=1, padx=5, sticky=tk.W)
        ttk.Radiobutton(category_frame, text="Detonator", variable=self.category_var,
                       value="Detonator", command=self.on_category_select).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(category_frame, text="Explosives", variable=self.category_var,
                       value="Explosives", command=self.on_category_select).pack(side=tk.LEFT, padx=5)
        
        # Area selection
        ttk.Label(top_frame, text="Area:").grid(row=0, column=2, padx=5, sticky=tk.W)
        self.area_combo = ttk.Combobox(top_frame, width=30, state="readonly")
        self.area_combo.grid(row=0, column=3, padx=5, sticky=tk.W)
        self.area_combo.bind("<<ComboboxSelected>>", self.on_area_select)
        
        ttk.Button(top_frame, text="Add Area", command=self.add_area).grid(row=0, column=4, padx=5)
        ttk.Button(top_frame, text="Manage Areas", command=self.manage_areas).grid(row=0, column=5, padx=5)
        
        # Area-level settings frame
        settings_frame = ttk.LabelFrame(main_container, text="Area Settings", padding="10")
        settings_frame.pack(fill=tk.X, pady=5)
        
        # Date of Supply
        ttk.Label(settings_frame, text="Date of Supply:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.date_entry = ttk.Entry(settings_frame, width=20)
        self.date_entry.grid(row=0, column=1, padx=5)
        self.date_entry.insert(0, datetime.now().strftime("%d-%m-%Y"))
        ttk.Button(settings_frame, text="📅", command=self.select_date).grid(row=0, column=2, padx=5)
        
        # Vehicle selection (common to both categories)
        ttk.Label(settings_frame, text="Vehicle:").grid(row=0, column=3, padx=5, sticky=tk.W)
        self.vehicle_combo = ttk.Combobox(settings_frame, width=30, state="readonly")
        self.vehicle_combo.grid(row=0, column=4, padx=5)
        ttk.Button(settings_frame, text="Add Vehicle", command=self.add_vehicle).grid(row=0, column=5, padx=5)
        ttk.Button(settings_frame, text="Manage Vehicles", command=self.manage_vehicles).grid(row=0, column=6, padx=5)
        
        # Mode of Transport
        ttk.Label(settings_frame, text="Mode of Transport:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.transport_entry = ttk.Entry(settings_frame, width=20)
        self.transport_entry.grid(row=1, column=1, padx=5, pady=5)
        self.transport_entry.insert(0, "Road")
        
        # E WAY BILL NO
        ttk.Label(settings_frame, text="E WAY BILL NO:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.e_way_bill_entry = ttk.Entry(settings_frame, width=30)
        self.e_way_bill_entry.grid(row=1, column=3, padx=5, pady=5)
        self.e_way_bill_entry.insert(0, "5019 3382 6386")
        
        # Original/Duplicate/Triplicate
        checkbox_frame = ttk.Frame(settings_frame)
        checkbox_frame.grid(row=1, column=4, padx=5, pady=5, sticky=tk.W)
        self.original_var = tk.BooleanVar()
        self.duplicate_var = tk.BooleanVar()
        self.triplicate_var = tk.BooleanVar()
        ttk.Checkbutton(checkbox_frame, text="Original", variable=self.original_var).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(checkbox_frame, text="Duplicate", variable=self.duplicate_var).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(checkbox_frame, text="Triplicate", variable=self.triplicate_var).pack(side=tk.LEFT, padx=5)
        
        # Invoice number and E WAY DOCUMENT NO (base numbers, will auto-increment per customer)
        invoice_frame = ttk.LabelFrame(settings_frame, text="Starting Numbers (Auto-increment per customer)", padding="5")
        invoice_frame.grid(row=2, column=0, columnspan=6, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(invoice_frame, text="Starting Invoice No:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.start_invoice_entry = ttk.Entry(invoice_frame, width=20)
        self.start_invoice_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(invoice_frame, text="Starting E WAY DOCUMENT NO:").grid(row=0, column=2, padx=5, sticky=tk.W)
        self.start_e_way_doc_entry = ttk.Entry(invoice_frame, width=20)
        self.start_e_way_doc_entry.grid(row=0, column=3, padx=5)
        
        # Main content area: Left side - Customer list, Right side - Customer details
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Left side: Customer list
        customer_list_frame = ttk.LabelFrame(content_frame, text="Customer List (Select customers)", padding="10")
        customer_list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Customer list buttons
        customer_btn_frame = ttk.Frame(customer_list_frame)
        customer_btn_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(customer_btn_frame, text="Add Customer", command=self.add_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(customer_btn_frame, text="Edit Customer", command=self.edit_selected_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(customer_btn_frame, text="Manage Customers", command=self.manage_customers).pack(side=tk.LEFT, padx=5)
        ttk.Button(customer_btn_frame, text="Manage Blasters", command=self.manage_blasters).pack(side=tk.LEFT, padx=5)
        
        # Scrollable customer list with checkboxes
        list_container = ttk.Frame(customer_list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas and scrollbar for customer list
        list_canvas = tk.Canvas(list_container, bg='#f5f5f5', highlightthickness=0)
        list_scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=list_canvas.yview)
        self.customer_list_frame = ttk.Frame(list_canvas)
        
        def configure_scroll_region(event):
            list_canvas.configure(scrollregion=list_canvas.bbox("all"))
        
        self.customer_list_frame.bind("<Configure>", configure_scroll_region)
        
        list_canvas_window = list_canvas.create_window((0, 0), window=self.customer_list_frame, anchor="nw")
        
        def configure_canvas_width(event):
            canvas_width = event.width
            list_canvas.itemconfig(list_canvas_window, width=canvas_width)
        
        list_canvas.bind('<Configure>', configure_canvas_width)
        list_canvas.configure(yscrollcommand=list_scrollbar.set)
        
        list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mouse wheel
        def on_mousewheel(event):
            list_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        list_canvas.bind("<MouseWheel>", on_mousewheel)
        list_canvas.bind("<Button-4>", lambda e: list_canvas.yview_scroll(-1, "units"))
        list_canvas.bind("<Button-5>", lambda e: list_canvas.yview_scroll(1, "units"))
        
        # Bind mouse wheel to canvas frame as well
        def bind_mousewheel_to_canvas(event):
            list_canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        def unbind_mousewheel_from_canvas(event):
            list_canvas.unbind_all("<MouseWheel>")
        
        list_canvas.bind('<Enter>', bind_mousewheel_to_canvas)
        list_canvas.bind('<Leave>', unbind_mousewheel_from_canvas)
        
        # Right side: Customer details (will be populated when customer is selected)
        self.details_frame = ttk.LabelFrame(content_frame, text="Customer Details", padding="10")
        self.details_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Initially show message
        tk.Label(self.details_frame, text="Click the arrow (▶) next to a customer to view/edit details",
                 font=('Helvetica', 12), bg='#ffffff', fg='#212529').pack(pady=50)
        
        # Bottom: Generate PDFs and Clear Form buttons
        bottom_frame = ttk.Frame(main_container)
        bottom_frame.pack(fill=tk.X, pady=10)
        
        btn_container = ttk.Frame(bottom_frame)
        btn_container.pack()
        
        ttk.Button(btn_container, text="Generate PDFs for Selected Customers", 
                  command=self.generate_pdfs, style='Accent.TButton').pack(side=tk.LEFT, padx=5, pady=10)
        ttk.Button(btn_container, text="Clear Form", 
                  command=self.clear_form).pack(side=tk.LEFT, padx=5, pady=10)
        
        # Load customers
        self.refresh_customer_list()
    
    def on_category_select(self):
        """Handle category selection"""
        self.current_category = self.category_var.get()
        self.current_area_id = None
        self.current_area_name = None
        self.area_combo.set('')
        self.refresh_areas()
        self.refresh_vehicles()
        self.selected_customers = {}
        self.refresh_customer_list()
    
    def refresh_areas(self):
        """Refresh area combobox (common to both categories)"""
        areas = self.db.get_locations()
        area_names = [area['name'] for area in areas]
        self.area_combo['values'] = area_names
    
    def on_area_select(self, event=None):
        """Handle area selection (areas are common to both categories)"""
        area_name = self.area_combo.get()
        if not area_name:
            self.current_area_id = None
            self.current_area_name = None
            self.selected_customers = {}
            self.refresh_customer_list()
            return
        
        areas = self.db.get_locations()
        area = next((a for a in areas if a['name'] == area_name), None)
        
        if area:
            self.current_area_id = area['id']
            self.current_area_name = area['name']
            self.refresh_vehicles()
            # Clear selected customers when area changes (since customers are area-specific)
            self.selected_customers = {}
            self.refresh_customer_list()
            # Update place of supply for all selected customers (use customer address if available)
            for customer_id in self.selected_customers:
                if 'customer' in self.selected_customers[customer_id]:
                    customer = self.selected_customers[customer_id]['customer']
                    self.selected_customers[customer_id]['place_of_supply'] = customer.get('address', '') or area_name
    
    def refresh_vehicles(self):
        """Refresh vehicle combobox (common to all areas and categories)"""
        vehicles = self.db.get_vehicles()
        vehicle_numbers = [v['vehicle_number'] for v in vehicles]
        self.vehicle_combo['values'] = vehicle_numbers
    
    def add_area(self):
        """Add a new area (common to both categories)"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Area")
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()
        self.make_dialog_visible(dialog)
        
        ttk.Label(dialog, text="Area Name:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.grid(row=0, column=1, padx=10, pady=10)
        name_entry.focus()
        
        def save_area():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Area name cannot be empty")
                return
            try:
                self.db.add_location(name)
                messagebox.showinfo("Success", "Area added successfully")
                self.refresh_areas()
                self.area_combo.set(name)
                self.on_area_select()
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        
        ttk.Button(dialog, text="Save", command=save_area).grid(row=1, column=0, columnspan=2, pady=10)
        name_entry.bind('<Return>', lambda e: save_area())
    
    def manage_areas(self):
        """Manage areas (edit/delete) - common to both categories"""
        AreasManager(self.root, self.db, callback=self.refresh_areas)
    
    def add_vehicle(self):
        """Add a new vehicle (common to all areas and categories)"""
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
                self.db.add_vehicle(vehicle_no)
                messagebox.showinfo("Success", "Vehicle added successfully")
                self.refresh_vehicles()
                self.vehicle_combo.set(vehicle_no)
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        
        ttk.Button(dialog, text="Save", command=save_vehicle).grid(row=1, column=0, columnspan=2, pady=10)
        vehicle_entry.bind('<Return>', lambda e: save_vehicle())
    
    def manage_vehicles(self):
        """Manage vehicles (edit/delete) - common to all areas and categories"""
        VehiclesManager(self.root, self.db, callback=self.refresh_vehicles)
    
    def manage_customers(self):
        """Manage customers (add/edit/delete) for the selected area"""
        if not self.current_area_id:
            messagebox.showwarning("Warning", "Please select an area first")
            return
        CustomersManager(self.root, self.db, location_id=self.current_area_id, callback=self.refresh_customer_list)
    
    def manage_blasters(self):
        """Manage blasters (add/edit/delete)"""
        BlastersManager(self.root, self.db, callback=None)
    
    def _quick_add_blaster_in_dialog(self, parent_dialog, blaster_combo):
        """Quick add blaster from within a dialog (for BatchDeliveryBillApp)"""
        dialog = tk.Toplevel(parent_dialog)
        dialog.title("Add Blaster")
        dialog.geometry("500x280")
        dialog.transient(parent_dialog)
        dialog.grab_set()
        self.make_dialog_visible(dialog)
        
        fields = [
            ("Name *", "name"),
            ("Document No", "document_no"),
            ("Address", "address")
        ]
        
        entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(dialog, text=label).grid(row=idx, column=0, padx=10, pady=5, sticky=tk.W)
            if key == 'address':
                entry = tk.Text(dialog, width=40, height=3, wrap=tk.WORD)
                entry.grid(row=idx, column=1, padx=10, pady=5, sticky=(tk.W, tk.E))
            else:
                entry = ttk.Entry(dialog, width=40)
                entry.grid(row=idx, column=1, padx=10, pady=5, sticky=(tk.W, tk.E))
            entries[key] = entry
            dialog.columnconfigure(1, weight=1)
        
        entries['name'].focus()
        
        def save():
            name = entries['name'].get().strip() if isinstance(entries['name'], tk.Text) else entries['name'].get().strip()
            if isinstance(entries['document_no'], tk.Text):
                document_no = entries['document_no'].get("1.0", tk.END).strip()
            else:
                document_no = entries['document_no'].get().strip()
            if isinstance(entries['address'], tk.Text):
                address = entries['address'].get("1.0", tk.END).strip()
            else:
                address = entries['address'].get().strip()
            
            if not name:
                messagebox.showerror("Error", "Blaster name is required")
                return
            try:
                self.db.add_blaster(name, document_no, address)
                messagebox.showinfo("Success", "Blaster added successfully")
                # Refresh the combobox in the parent dialog
                blasters = self.db.get_blasters()
                blaster_names = [b['name'] for b in blasters]
                blaster_combo['values'] = blaster_names
                blaster_combo.set(name)
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add blaster: {str(e)}")
        
        ttk.Button(dialog, text="Save", command=save).grid(row=len(fields), column=0, columnspan=2, pady=20)
        entries['name'].bind('<Return>', lambda e: entries['document_no'].focus())
    
    def select_date(self):
        """Open date picker"""
        try:
            from tkcalendar import Calendar
            
            dialog = tk.Toplevel(self.root)
            dialog.title("Select Date")
            dialog.geometry("350x280")
            dialog.transient(self.root)
            dialog.grab_set()
            self.make_dialog_visible(dialog)
            
            cal = Calendar(dialog, selectmode='day', date_pattern='dd-mm-yyyy',
                          font=('Helvetica', 10), background='white',
                          foreground='black', selectbackground='blue',
                          selectforeground='white')
            cal.pack(padx=10, pady=10)
            
            def set_date():
                try:
                    selected_date = cal.get_date()
                    from datetime import datetime
                    date_obj = datetime.strptime(selected_date, "%d-%m-%Y")
                    self.date_entry.delete(0, tk.END)
                    self.date_entry.insert(0, date_obj.strftime("%d-%m-%Y"))
                    dialog.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Error setting date: {str(e)}")
            
            btn_frame = ttk.Frame(dialog)
            btn_frame.pack(pady=10)
            ttk.Button(btn_frame, text="OK", command=set_date, width=10).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)
            
            cal.focus()
        except ImportError:
            # Fallback to simple entry
            dialog = tk.Toplevel(self.root)
            dialog.title("Enter Date")
            dialog.geometry("400x150")
            dialog.transient(self.root)
            dialog.grab_set()
            self.make_dialog_visible(dialog)
            
            ttk.Label(dialog, text="Enter date (DD-MM-YYYY):", font=('Helvetica', 10)).grid(row=0, column=0, padx=10, pady=15, sticky=tk.W)
            date_entry = ttk.Entry(dialog, width=25, font=('Helvetica', 11))
            date_entry.grid(row=0, column=1, padx=10, pady=15)
            date_entry.insert(0, self.date_entry.get())
            date_entry.focus()
            date_entry.select_range(0, tk.END)
            
            def set_date():
                date_str = date_entry.get().strip()
                try:
                    datetime.strptime(date_str, "%d-%m-%Y")
                    self.date_entry.delete(0, tk.END)
                    self.date_entry.insert(0, date_str)
                    dialog.destroy()
                except ValueError:
                    messagebox.showerror("Error", "Invalid date format. Please use DD-MM-YYYY")
                    date_entry.focus()
            
            btn_frame = ttk.Frame(dialog)
            btn_frame.grid(row=1, column=0, columnspan=2, pady=15)
            ttk.Button(btn_frame, text="OK", command=set_date, width=10).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)
            date_entry.bind('<Return>', lambda e: set_date())
    
    def refresh_customer_list(self):
        """Refresh the customer list display"""
        # Clear existing widgets
        for widget in self.customer_list_frame.winfo_children():
            widget.destroy()
        
        # Renumber customers to ensure sequential IDs
        self.db.renumber_customers()
        
        # Filter customers by selected area (location_id)
        customers = self.db.get_customers(location_id=self.current_area_id) if self.current_area_id else []
        
        if not customers:
            message = "No customers found for this area. Click 'Add Customer' to add one." if self.current_area_id else "Please select an area first."
            tk.Label(self.customer_list_frame, text=message,
                     font=('Helvetica', 10), bg='#ffffff', fg='#212529').pack(pady=20)
            return
        
        # Store customer widgets for reference
        self.customer_widgets = {}
        
        for customer in customers:
            customer_id = customer['id']
            customer_name = customer['name']
            
            # Frame for each customer row with better styling
            customer_row = tk.Frame(self.customer_list_frame, bg='#f8f9fa', relief=tk.FLAT, bd=0)
            customer_row.pack(fill=tk.X, pady=1, padx=2)
            
            # Checkbox (for selection only)
            var = tk.BooleanVar(value=(customer_id in self.selected_customers))
            checkbox = ttk.Checkbutton(customer_row, variable=var,
                                      command=lambda cid=customer_id, v=var: self.on_customer_check(cid, v))
            checkbox.pack(side=tk.LEFT, padx=8, pady=4)
            
            # Customer name
            name_label = tk.Label(customer_row, text=customer_name, font=('Helvetica', 12), 
                                 bg='#f8f9fa', fg='#212529', anchor='w', cursor='arrow')
            name_label.pack(side=tk.LEFT, padx=5, pady=4, fill=tk.X, expand=True)
            
            # Expand/collapse arrow button (after the name)
            arrow_label = tk.Label(customer_row, text="▶", font=('Helvetica', 10, 'bold'), 
                                  cursor="hand2", bg='#f8f9fa', fg='#495057', padx=8)
            arrow_label.pack(side=tk.RIGHT, padx=5, pady=4)
            arrow_label.bind("<Button-1>", lambda e, cid=customer_id: self.toggle_customer_details(cid))
            
            # Hover effect functions
            def on_enter(e):
                customer_row.config(bg='#e3f2fd')
                name_label.config(bg='#e3f2fd')
                arrow_label.config(bg='#e3f2fd', fg='#2196F3')
            
            def on_leave(e):
                customer_row.config(bg='#f8f9fa')
                name_label.config(bg='#f8f9fa')
                arrow_label.config(bg='#f8f9fa', fg='#495057')
            
            customer_row.bind("<Enter>", on_enter)
            customer_row.bind("<Leave>", on_leave)
            name_label.bind("<Enter>", on_enter)
            name_label.bind("<Leave>", on_leave)
            arrow_label.bind("<Enter>", on_enter)
            arrow_label.bind("<Leave>", on_leave)
            
            # Store reference
            self.customer_widgets[customer_id] = {
                'var': var,
                'row': customer_row,
                'customer': customer,
                'arrow_label': arrow_label,
                'name_label': name_label
            }
    
    def on_customer_check(self, customer_id, var):
        """Handle customer checkbox toggle"""
        if var.get():
            # Customer selected - initialize data
            customer = self.db.get_customer(customer_id)
            if customer:
                # Get starting numbers
                start_invoice = self.start_invoice_entry.get().strip()
                start_e_way_doc = self.start_e_way_doc_entry.get().strip()
                
                # Auto-increment: count how many customers are already selected
                selected_count = len([c for c in self.selected_customers.values() if c])
                
                if start_invoice:
                    # Try to extract number and increment
                    try:
                        # Extract numeric part
                        match = re.search(r'(\d+)', start_invoice)
                        if match:
                            base_num = int(match.group(1))
                            new_num = base_num + selected_count
                            # Replace the number in the original string
                            invoice_no = re.sub(r'\d+', str(new_num), start_invoice, count=1)
                        else:
                            invoice_no = f"{start_invoice}_{selected_count + 1}"
                    except:
                        invoice_no = f"{start_invoice}_{selected_count + 1}"
                else:
                    invoice_no = ""
                
                if start_e_way_doc:
                    try:
                        match = re.search(r'(\d+)', start_e_way_doc)
                        if match:
                            matched_num_str = match.group(1)
                            base_num = int(matched_num_str)
                            new_num = base_num + selected_count
                            # Preserve leading zeros by using the same width
                            new_num_str = str(new_num).zfill(len(matched_num_str))
                            e_way_doc_no = re.sub(r'\d+', new_num_str, start_e_way_doc, count=1)
                        else:
                            e_way_doc_no = f"{start_e_way_doc}_{selected_count + 1}"
                    except:
                        e_way_doc_no = f"{start_e_way_doc}_{selected_count + 1}"
                else:
                    e_way_doc_no = ""
                
                self.selected_customers[customer_id] = {
                    'customer': customer,
                    'invoice_no': invoice_no,
                    'e_way_doc_no': e_way_doc_no,
                    'items': [],
                    'place_of_supply': customer.get('address', '') or self.current_area_name or '',
                    'freight_charges': 0.0
                }
                # If this customer is currently expanded, refresh the view
                if self.expanded_customer_id == customer_id:
                    self.show_customer_details_view_only(customer_id)
        else:
            # Customer deselected
            if customer_id in self.selected_customers:
                del self.selected_customers[customer_id]
            # If this was the expanded customer, clear details
            if self.expanded_customer_id == customer_id:
                self.clear_customer_details()
                self.expanded_customer_id = None
                # Update arrow display
                self.update_arrows_display()
            else:
                self.clear_customer_details()
    
    def toggle_customer_details(self, customer_id):
        """Toggle customer details display (expand/collapse) - does NOT select the customer"""
        # If clicking the same customer, collapse
        if self.expanded_customer_id == customer_id:
            self.clear_customer_details()
            self.expanded_customer_id = None
        else:
            # Expand this customer (just view details, don't select)
            self.expanded_customer_id = customer_id
            self.show_customer_details_view_only(customer_id)
        # Update arrow displays
        self.update_arrows_display()
    
    def update_arrows_display(self):
        """Update arrow symbols (▶/▼) based on expanded state"""
        if hasattr(self, 'customer_widgets'):
            for cid, widget_info in self.customer_widgets.items():
                if 'arrow_label' in widget_info:
                    if cid == self.expanded_customer_id:
                        widget_info['arrow_label'].config(text="▼")
                    else:
                        widget_info['arrow_label'].config(text="▶")
    
    def show_customer_details_view_only(self, customer_id):
        """Show customer details in view-only mode (when clicking arrow, not selecting)"""
        # Get customer from database
        customer = self.db.get_customer(customer_id)
        if not customer:
            self.clear_customer_details()
            ttk.Label(self.details_frame, text="Customer not found",
                     font=('Helvetica', 12)).pack(pady=50)
            return
        
        # Check if customer is selected (to show invoice details if selected)
        is_selected = customer_id in self.selected_customers
        customer_data = self.selected_customers[customer_id] if is_selected else None
        
        # Clear details frame
        for widget in self.details_frame.winfo_children():
            widget.destroy()
        
        # Create scrollable frame for details
        canvas = tk.Canvas(self.details_frame, bg='#ffffff', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.details_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#ffffff')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas_window = canvas.create_window((15, 15), window=scrollable_frame, anchor="nw")
        
        def configure_canvas_width(event):
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width - 30)
        
        canvas.bind('<Configure>', configure_canvas_width)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Header with customer name and Edit button
        header_frame = tk.Frame(scrollable_frame, bg='#ffffff')
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        name_label = tk.Label(header_frame, text=customer['name'], 
                               font=('Helvetica', 16, 'bold'), bg='#ffffff', fg='#212529')
        name_label.pack(side=tk.LEFT, anchor=tk.W)
        
        tk.Button(header_frame, text="Edit", command=lambda: self.edit_customer_from_details(customer_id),
                 font=('Helvetica', 10), bg='#2196F3', fg='white', relief=tk.FLAT, padx=12, pady=4,
                 cursor='hand2', activebackground='#0b7dda').pack(side=tk.RIGHT, padx=5)
        
        # Receiver details frame
        receiver_frame = ttk.LabelFrame(scrollable_frame, text="Receiver Details", padding="12")
        receiver_frame.pack(fill=tk.X, pady=(0, 12))
        
        # Receiver details (formatted nicely)
        place_of_supply = customer.get('address', '') if customer.get('address') else (self.current_area_name or '')
        details_fields = [
            ("Address", customer.get('address', '')),
            ("SF.NO", customer.get('sf_no', '')),
            ("RC.NO", customer.get('rc_no', '')),
            ("State", customer.get('state', '')),
            ("GSTIN", customer.get('gstin', '')),
            ("Place of Supply", place_of_supply)
        ]
        
        for label, value in details_fields:
            if value:  # Only show non-empty fields
                row_frame = tk.Frame(receiver_frame, bg='#ffffff')
                row_frame.pack(fill=tk.X, pady=4)
                tk.Label(row_frame, text=f"{label}:", font=('Helvetica', 12, 'bold'), width=18, anchor=tk.W,
                        bg='#ffffff', fg='#212529').pack(side=tk.LEFT)
                tk.Label(row_frame, text=value, font=('Helvetica', 12), bg='#ffffff', fg='#212529').pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Only show invoice details and items if customer is selected
        if is_selected and customer_data:
            # Invoice number and E WAY DOCUMENT NO (editable)
            invoice_frame = ttk.LabelFrame(scrollable_frame, text="Invoice Details", padding="10")
            invoice_frame.pack(fill=tk.X, pady=(0, 12))
            
            ttk.Label(invoice_frame, text="Invoice No:", font=('Helvetica', 12)).grid(row=0, column=0, padx=8, pady=6, sticky=tk.W)
            invoice_entry = ttk.Entry(invoice_frame, width=35, font=('Helvetica', 12))
            invoice_entry.insert(0, customer_data['invoice_no'])
            invoice_entry.grid(row=0, column=1, padx=8, pady=6, sticky=(tk.W, tk.E))
            invoice_entry.bind('<KeyRelease>', lambda e: self.update_customer_invoice_no(customer_id, invoice_entry.get()))
            
            ttk.Label(invoice_frame, text="E WAY DOCUMENT NO:", font=('Helvetica', 12)).grid(row=1, column=0, padx=8, pady=6, sticky=tk.W)
            e_way_doc_entry = ttk.Entry(invoice_frame, width=35, font=('Helvetica', 12))
            e_way_doc_entry.insert(0, customer_data['e_way_doc_no'])
            e_way_doc_entry.grid(row=1, column=1, padx=8, pady=6, sticky=(tk.W, tk.E))
            e_way_doc_entry.bind('<KeyRelease>', lambda e: self.update_customer_e_way_doc(customer_id, e_way_doc_entry.get()))
            
            invoice_frame.columnconfigure(1, weight=1)
            
            # Items section with scrollbar
            items_frame = ttk.LabelFrame(scrollable_frame, text="Goods Selection", padding="10")
            items_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
            
            # Add item button
            tk.Button(items_frame, text="+ Add Good", command=lambda: self.add_good_to_customer(customer_id), 
                     font=('Helvetica', 11, 'bold'), bg='#4CAF50', fg='white', relief=tk.FLAT, padx=15, pady=6,
                     cursor='hand2', activebackground='#45a049').pack(pady=8)
            
            # Items list with scrollbar
            items_container = ttk.Frame(items_frame)
            items_container.pack(fill=tk.BOTH, expand=True)
            
            items_canvas = tk.Canvas(items_container, bg='#fafafa', highlightthickness=0, height=200)
            items_scrollbar = ttk.Scrollbar(items_container, orient="vertical", command=items_canvas.yview)
            items_list_frame = ttk.Frame(items_canvas)
            
            def configure_items_scroll(event):
                items_canvas.configure(scrollregion=items_canvas.bbox("all"))
            
            items_list_frame.bind("<Configure>", configure_items_scroll)
            
            items_canvas_window = items_canvas.create_window((0, 0), window=items_list_frame, anchor="nw")
            
            def configure_items_width(event):
                canvas_width = event.width
                items_canvas.itemconfig(items_canvas_window, width=canvas_width)
            
            items_canvas.bind('<Configure>', configure_items_width)
            items_canvas.configure(yscrollcommand=items_scrollbar.set)
            
            items_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            items_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Bind mouse wheel for items
            def on_items_mousewheel(event):
                items_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            
            items_canvas.bind("<MouseWheel>", on_items_mousewheel)
            items_canvas.bind("<Button-4>", lambda e: items_canvas.yview_scroll(-1, "units"))
            items_canvas.bind("<Button-5>", lambda e: items_canvas.yview_scroll(1, "units"))
            
            self.refresh_customer_items(items_list_frame, customer_id)
            
            # Store references
            customer_data['details_frame'] = scrollable_frame
            customer_data['items_frame'] = items_list_frame
            customer_data['items_canvas'] = items_canvas
        else:
            # Show message that customer needs to be selected
            info_frame = tk.LabelFrame(scrollable_frame, text="Invoice & Items", bg='#ffffff', fg='#212529',
                                      font=('Helvetica', 10, 'bold'), padx=10, pady=10)
            info_frame.pack(fill=tk.X, pady=(0, 5))
            tk.Label(info_frame, text="Select this customer (checkbox) to add invoice details and items",
                     font=('Helvetica', 11), fg='#6c757d', bg='#ffffff').pack(pady=10)
    
    def show_customer_details(self, customer_id):
        """Show customer details in the details frame (when customer is selected)"""
        if customer_id not in self.selected_customers:
            return
        
        # Clear details frame
        for widget in self.details_frame.winfo_children():
            widget.destroy()
        
        customer_data = self.selected_customers[customer_id]
        customer = customer_data['customer']
        
        # Create scrollable frame for details
        canvas = tk.Canvas(self.details_frame, bg='#ffffff', highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.details_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#ffffff')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas_window = canvas.create_window((15, 15), window=scrollable_frame, anchor="nw")
        
        def configure_canvas_width(event):
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width - 30)
        
        canvas.bind('<Configure>', configure_canvas_width)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Header with customer name and Edit button
        header_frame = tk.Frame(scrollable_frame, bg='#ffffff')
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        name_label = tk.Label(header_frame, text=customer['name'], 
                               font=('Helvetica', 16, 'bold'), bg='#ffffff', fg='#212529')
        name_label.pack(side=tk.LEFT, anchor=tk.W)
        
        tk.Button(header_frame, text="Edit", command=lambda: self.edit_customer_from_details(customer_id),
                 font=('Helvetica', 10), bg='#2196F3', fg='white', relief=tk.FLAT, padx=12, pady=4,
                 cursor='hand2', activebackground='#0b7dda').pack(side=tk.RIGHT, padx=5)
        
        # Receiver details frame
        receiver_frame = ttk.LabelFrame(scrollable_frame, text="Receiver Details", padding="12")
        receiver_frame.pack(fill=tk.X, pady=(0, 12))
        
        # Receiver details (formatted nicely)
        details_fields = [
            ("Address", customer.get('address', '')),
            ("SF.NO", customer.get('sf_no', '')),
            ("RC.NO", customer.get('rc_no', '')),
            ("State", customer.get('state', '')),
            ("GSTIN", customer.get('gstin', '')),
            ("Place of Supply", customer_data['place_of_supply'])
        ]
        
        for label, value in details_fields:
            if value:  # Only show non-empty fields
                row_frame = tk.Frame(receiver_frame, bg='#ffffff')
                row_frame.pack(fill=tk.X, pady=4)
                tk.Label(row_frame, text=f"{label}:", font=('Helvetica', 12, 'bold'), width=18, anchor=tk.W,
                        bg='#ffffff', fg='#212529').pack(side=tk.LEFT)
                tk.Label(row_frame, text=value, font=('Helvetica', 12), bg='#ffffff', fg='#212529').pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Invoice number and E WAY DOCUMENT NO (editable)
        invoice_frame = ttk.LabelFrame(scrollable_frame, text="Invoice Details", padding="10")
        invoice_frame.pack(fill=tk.X, pady=(0, 12))
        
        ttk.Label(invoice_frame, text="Invoice No:", font=('Helvetica', 12)).grid(row=0, column=0, padx=8, pady=6, sticky=tk.W)
        invoice_entry = ttk.Entry(invoice_frame, width=35, font=('Helvetica', 12))
        invoice_entry.insert(0, customer_data['invoice_no'])
        invoice_entry.grid(row=0, column=1, padx=8, pady=6, sticky=(tk.W, tk.E))
        invoice_entry.bind('<KeyRelease>', lambda e: self.update_customer_invoice_no(customer_id, invoice_entry.get()))
        
        ttk.Label(invoice_frame, text="E WAY DOCUMENT NO:", font=('Helvetica', 12)).grid(row=1, column=0, padx=8, pady=6, sticky=tk.W)
        e_way_doc_entry = ttk.Entry(invoice_frame, width=35, font=('Helvetica', 12))
        e_way_doc_entry.insert(0, customer_data['e_way_doc_no'])
        e_way_doc_entry.grid(row=1, column=1, padx=8, pady=6, sticky=(tk.W, tk.E))
        e_way_doc_entry.bind('<KeyRelease>', lambda e: self.update_customer_e_way_doc(customer_id, e_way_doc_entry.get()))
        
        invoice_frame.columnconfigure(1, weight=1)
        
        # Items section
        items_frame = ttk.LabelFrame(scrollable_frame, text="Goods Selection", padding="10")
        items_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Add item button
        tk.Button(items_frame, text="+ Add Good", command=lambda: self.add_good_to_customer(customer_id), 
                 font=('Helvetica', 11, 'bold'), bg='#4CAF50', fg='white', relief=tk.FLAT, padx=15, pady=6,
                 cursor='hand2', activebackground='#45a049').pack(pady=8)
        
        # Items list with scrollbar
        items_container = ttk.Frame(items_frame)
        items_container.pack(fill=tk.BOTH, expand=True)
        
        items_canvas = tk.Canvas(items_container, bg='#fafafa', highlightthickness=0, height=200)
        items_scrollbar = ttk.Scrollbar(items_container, orient="vertical", command=items_canvas.yview)
        items_list_frame = ttk.Frame(items_canvas)
        
        def configure_items_scroll(event):
            items_canvas.configure(scrollregion=items_canvas.bbox("all"))
        
        items_list_frame.bind("<Configure>", configure_items_scroll)
        
        items_canvas_window = items_canvas.create_window((0, 0), window=items_list_frame, anchor="nw")
        
        def configure_items_width(event):
            canvas_width = event.width
            items_canvas.itemconfig(items_canvas_window, width=canvas_width)
        
        items_canvas.bind('<Configure>', configure_items_width)
        items_canvas.configure(yscrollcommand=items_scrollbar.set)
        
        items_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        items_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mouse wheel for items
        def on_items_mousewheel(event):
            items_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        items_canvas.bind("<MouseWheel>", on_items_mousewheel)
        items_canvas.bind("<Button-4>", lambda e: items_canvas.yview_scroll(-1, "units"))
        items_canvas.bind("<Button-5>", lambda e: items_canvas.yview_scroll(1, "units"))
        
        self.refresh_customer_items(items_list_frame, customer_id)
        
        # Store references
        customer_data['details_frame'] = scrollable_frame
        customer_data['items_frame'] = items_list_frame
        customer_data['items_canvas'] = items_canvas
    
    def update_customer_invoice_no(self, customer_id, invoice_no):
        """Update invoice number for customer"""
        if customer_id in self.selected_customers:
            self.selected_customers[customer_id]['invoice_no'] = invoice_no
    
    def update_customer_e_way_doc(self, customer_id, e_way_doc_no):
        """Update E WAY DOCUMENT NO for customer"""
        if customer_id in self.selected_customers:
            self.selected_customers[customer_id]['e_way_doc_no'] = e_way_doc_no
    
    def refresh_customer_items(self, parent_frame, customer_id):
        """Refresh items display for a customer"""
        # Clear existing items display
        for widget in parent_frame.winfo_children():
            widget.destroy()
        
        if customer_id not in self.selected_customers:
            return
        
        items = self.selected_customers[customer_id]['items']
        
        if not items:
            ttk.Label(parent_frame, text="No items added. Click 'Add Good' to add items.").pack(pady=10)
            return
        
        # Display items in a nicer format
        for idx, item in enumerate(items):
            item_frame = tk.Frame(parent_frame, bg='white', relief=tk.FLAT, bd=0)
            item_frame.pack(fill=tk.X, pady=3, padx=5)
            
            desc = item.get('description', '')
            qty = item.get('qty', 0)
            rate = item.get('rate', 0)
            unit = item.get('unit', '')
            total = item.get('total_amount', 0)
            
            # Item details
            details_text = f"{desc} - Qty: {qty} {unit} @ ₹{rate:.2f} = ₹{total:.2f}"
            item_label = tk.Label(item_frame, text=details_text, font=('Helvetica', 10), 
                                 bg='white', anchor='w', justify=tk.LEFT)
            item_label.pack(side=tk.LEFT, padx=8, pady=5, fill=tk.X, expand=True)
            
            # Remove button
            remove_btn = tk.Button(item_frame, text="✕", command=lambda i=idx: self.remove_item_from_customer(customer_id, i),
                                  font=('Helvetica', 12, 'bold'), bg='#f44336', fg='white', 
                                  relief=tk.FLAT, width=3, height=1, cursor='hand2',
                                  activebackground='#da190b')
            remove_btn.pack(side=tk.RIGHT, padx=5, pady=3)
    
    def add_good_to_customer(self, customer_id):
        """Add a good to customer's items"""
        if customer_id not in self.selected_customers:
            return
        
        # Simple dialog to select good and quantity
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Good")
        dialog.geometry("500x300")
        dialog.transient(self.root)
        dialog.grab_set()
        self.make_dialog_visible(dialog)
        
        goods = self.db.get_goods()
        
        ttk.Label(dialog, text="Select Good:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        good_combo = ttk.Combobox(dialog, width=40, values=[f"{g['description']} ({g['hsn_code']})" for g in goods], state="readonly")
        good_combo.grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(dialog, text="Quantity:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        qty_entry = ttk.Entry(dialog, width=20)
        qty_entry.grid(row=1, column=1, padx=10, pady=10)
        qty_entry.insert(0, "1")
        
        def add_item():
            selection = good_combo.get()
            if not selection:
                messagebox.showerror("Error", "Please select a good")
                return
            
            # Find the good
            good_desc = selection.split(' (')[0]
            good = next((g for g in goods if g['description'] == good_desc), None)
            if not good:
                return
            
            try:
                qty = float(qty_entry.get())
                if qty <= 0:
                    raise ValueError("Quantity must be greater than 0")
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid quantity: {str(e)}")
                return
            
            # Calculate item data (simplified - using default tax rates)
            rate = good['rate']
            total = qty * rate
            taxable_value = total
            cgst_rate = self.default_cgst_rate
            sgst_rate = self.default_sgst_rate
            cgst_rs = (taxable_value * cgst_rate) / 100
            sgst_rs = (taxable_value * sgst_rate) / 100
            total_amount = total + cgst_rs + sgst_rs
            
            item_data = {
                'description': good['description'],
                'hsn_code': good['hsn_code'],
                'unit': good['unit'],
                'qty': qty,
                'rate': rate,
                'total': total,
                'taxable_value': taxable_value,
                'cgst_rate': cgst_rate,
                'cgst_rs': cgst_rs,
                'sgst_rate': sgst_rate,
                'sgst_rs': sgst_rs,
                'igst_rate': 0,
                'igst_rs': 0,
                'total_amount': total_amount
            }
            
            self.selected_customers[customer_id]['items'].append(item_data)
            
            # Refresh display
            if 'items_frame' in self.selected_customers[customer_id]:
                self.refresh_customer_items(self.selected_customers[customer_id]['items_frame'], customer_id)
            
            dialog.destroy()
        
        ttk.Button(dialog, text="Add", command=add_item).grid(row=2, column=0, columnspan=2, pady=20)
        good_combo.focus()
    
    def remove_item_from_customer(self, customer_id, item_index):
        """Remove an item from customer's items"""
        if customer_id in self.selected_customers:
            items = self.selected_customers[customer_id]['items']
            if 0 <= item_index < len(items):
                items.pop(item_index)
                if 'items_frame' in self.selected_customers[customer_id]:
                    self.refresh_customer_items(self.selected_customers[customer_id]['items_frame'], customer_id)
    
    def clear_customer_details(self):
        """Clear customer details frame"""
        for widget in self.details_frame.winfo_children():
            widget.destroy()
        ttk.Label(self.details_frame, text="Click the arrow (▶) next to a customer to view/edit details",
                 font=('Helvetica', 12)).pack(pady=50)
    
    def edit_customer_from_details(self, customer_id):
        """Edit customer from the details view"""
        customer = self.db.get_customer(customer_id)
        if not customer:
            return
        self.edit_customer_dialog(customer)
        # Refresh the details view after editing
        if customer_id == self.expanded_customer_id:
            # Reload customer data from DB
            updated_customer = self.db.get_customer(customer_id)
            if updated_customer:
                # Update customer in selected_customers if selected
                if customer_id in self.selected_customers:
                    self.selected_customers[customer_id]['customer'] = updated_customer
                # Refresh the view
                self.show_customer_details_view_only(customer_id)
    
    def add_customer(self):
        """Add a new customer"""
        if not self.current_area_id:
            messagebox.showwarning("Warning", "Please select an area first")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Customer")
        dialog.geometry("500x450")
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
            # Set default values
            if key == 'address' and self.current_area_name:
                entry.insert(0, self.current_area_name)
            elif key == 'state':
                entry.insert(0, 'Tamilnadu')
            entry.grid(row=idx, column=1, padx=10, pady=5)
            entries[key] = entry
        
        # Blaster selection
        row_idx = len(fields)
        ttk.Label(dialog, text="Blaster:").grid(row=row_idx, column=0, padx=10, pady=5, sticky=tk.W)
        blaster_combo = ttk.Combobox(dialog, width=37, state="readonly")
        blasters = self.db.get_blasters()
        blaster_names = [b['name'] for b in blasters]
        blaster_combo['values'] = blaster_names
        blaster_combo.grid(row=row_idx, column=1, padx=10, pady=5)
        
        blaster_btn_frame = ttk.Frame(dialog)
        blaster_btn_frame.grid(row=row_idx, column=2, padx=5, pady=5)
        ttk.Button(blaster_btn_frame, text="Add", command=lambda: self._quick_add_blaster_in_dialog(dialog, blaster_combo)).pack(side=tk.LEFT, padx=2)
        
        entries['name'].focus()
        
        def save_customer():
            name = entries['name'].get().strip()
            if not name:
                messagebox.showerror("Error", "Customer name is required")
                return
            
            # Get selected blaster ID
            selected_blaster_name = blaster_combo.get()
            blaster_id = None
            if selected_blaster_name:
                blaster = next((b for b in blasters if b['name'] == selected_blaster_name), None)
                if blaster:
                    blaster_id = blaster['id']
            
            try:
                self.db.add_customer(
                    name,
                    entries['address'].get().strip(),
                    entries['sf_no'].get().strip(),
                    entries['rc_no'].get().strip(),
                    entries['state'].get().strip(),
                    entries['gstin'].get().strip(),
                    blaster_id,
                    location_id=self.current_area_id
                )
                messagebox.showinfo("Success", "Customer added successfully")
                self.refresh_customer_list()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add customer: {str(e)}")
        
        ttk.Button(dialog, text="Save", command=save_customer).grid(row=row_idx+1, column=0, columnspan=2, pady=20)
        entries['name'].bind('<Return>', lambda e: entries['address'].focus())
    
    def edit_selected_customer(self):
        """Edit selected customer (open dialog to select which customer to edit)"""
        if not self.current_area_id:
            messagebox.showwarning("Warning", "Please select an area first")
            return
        
        customers = self.db.get_customers(location_id=self.current_area_id)
        if not customers:
            messagebox.showwarning("Warning", "No customers to edit for this area")
            return
        
        # Simple selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Customer to Edit")
        dialog.geometry("400x400")
        dialog.transient(self.root)
        dialog.grab_set()
        self.make_dialog_visible(dialog)
        
        ttk.Label(dialog, text="Select customer to edit:", font=('Helvetica', 10)).pack(pady=10)
        
        # Listbox
        listbox = tk.Listbox(dialog, height=15)
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for customer in customers:
            listbox.insert(tk.END, customer['name'])
        
        def edit_customer():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a customer")
                return
            
            customer = customers[selection[0]]
            dialog.destroy()
            self.edit_customer_dialog(customer)
        
        ttk.Button(dialog, text="Edit Selected", command=edit_customer).pack(pady=10)
        listbox.bind('<Double-Button-1>', lambda e: edit_customer())
    
    def edit_customer_dialog(self, customer):
        """Edit customer dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Customer")
        dialog.geometry("500x400")
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
            entry.insert(0, customer.get(key, ''))
            entries[key] = entry
        
        # Blaster selection
        row_idx = len(fields)
        ttk.Label(dialog, text="Blaster:").grid(row=row_idx, column=0, padx=10, pady=5, sticky=tk.W)
        blaster_combo = ttk.Combobox(dialog, width=37, state="readonly")
        blasters = self.db.get_blasters()
        blaster_names = [b['name'] for b in blasters]
        blaster_combo['values'] = blaster_names
        # Pre-select current blaster
        current_blaster_name = customer.get('blaster_name', '')
        if current_blaster_name:
            blaster_combo.set(current_blaster_name)
        blaster_combo.grid(row=row_idx, column=1, padx=10, pady=5)
        
        blaster_btn_frame = ttk.Frame(dialog)
        blaster_btn_frame.grid(row=row_idx, column=2, padx=5, pady=5)
        ttk.Button(blaster_btn_frame, text="Add", command=lambda: self._quick_add_blaster_in_dialog(dialog, blaster_combo)).pack(side=tk.LEFT, padx=2)
        
        entries['name'].focus()
        
        def save_customer():
            name = entries['name'].get().strip()
            if not name:
                messagebox.showerror("Error", "Customer name is required")
                return
            
            # Get selected blaster ID
            selected_blaster_name = blaster_combo.get()
            blaster_id = None
            if selected_blaster_name:
                blaster = next((b for b in blasters if b['name'] == selected_blaster_name), None)
                if blaster:
                    blaster_id = blaster['id']
            
            try:
                self.db.update_customer(
                    customer['id'],
                    name,
                    entries['address'].get().strip(),
                    entries['sf_no'].get().strip(),
                    entries['rc_no'].get().strip(),
                    entries['state'].get().strip(),
                    entries['gstin'].get().strip(),
                    blaster_id,
                    location_id=self.current_area_id
                )
                messagebox.showinfo("Success", "Customer updated successfully")
                self.refresh_customer_list()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update customer: {str(e)}")
        
        ttk.Button(dialog, text="Save", command=save_customer).grid(row=row_idx+1, column=0, columnspan=2, pady=20)
        entries['name'].bind('<Return>', lambda e: entries['address'].focus())
    
    def _round_total(self, amount):
        """Round to nearest integer"""
        import math
        return math.floor(amount) if (amount - math.floor(amount)) < 0.5 else math.ceil(amount)
    
    def clear_form(self):
        """Clear the form - reset all selections and data"""
        if messagebox.askyesno("Confirm", "Are you sure you want to clear the form?\n\nThis will:\n- Clear category selection\n- Clear area selection\n- Clear all selected customers\n- Clear date and vehicle selection\n- Clear all customer items"):
            # Clear category
            self.category_var.set('')
            self.current_category = None
            
            # Clear area
            self.current_area_id = None
            self.current_area_name = None
            self.area_combo.set('')
            
            # Clear date
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, datetime.now().strftime("%d-%m-%Y"))
            
            # Clear vehicle
            self.vehicle_combo.set('')
            
            # Clear transport and E-way bill
            self.transport_entry.delete(0, tk.END)
            self.transport_entry.insert(0, "Road")
            self.e_way_bill_entry.delete(0, tk.END)
            self.e_way_bill_entry.insert(0, "5019 3382 6386")
            
            # Clear checkboxes
            self.original_var.set(False)
            self.duplicate_var.set(False)
            self.triplicate_var.set(False)
            
            # Clear starting invoice numbers
            self.start_invoice_entry.delete(0, tk.END)
            self.start_e_way_doc_entry.delete(0, tk.END)
            
            # Clear auto-increment counters
            self.current_invoice_number = ""
            self.current_e_way_doc_number = ""
            
            # Clear selected customers
            self.selected_customers = {}
            self.refresh_customer_list()
            
            # Clear customer details frame
            self.clear_customer_details()
            
            messagebox.showinfo("Success", "Form cleared successfully!")
    
    def generate_pdfs(self):
        """Generate PDFs for all selected customers"""
        if not self.selected_customers:
            messagebox.showwarning("Warning", "Please select at least one customer")
            return
        
        if not self.current_area_id:
            messagebox.showerror("Error", "Please select an area")
            return
        
        # Validate area settings
        date_supply = self.date_entry.get()
        if not date_supply:
            messagebox.showerror("Error", "Please enter Date of Supply")
            return
        
        vehicle_number = self.vehicle_combo.get()
        if not vehicle_number:
            messagebox.showerror("Error", "Please select a vehicle")
            return
        
        # Check that all selected customers have items
        customers_without_items = []
        for customer_id, data in self.selected_customers.items():
            if not data.get('items'):
                customers_without_items.append(data['customer']['name'])
        
        if customers_without_items:
            messagebox.showerror("Error", 
                f"The following customers have no items:\n{', '.join(customers_without_items)}")
            return
        
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"Batch_Delivery_Bills_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        
        if not filename:
            return
        
        try:
            # Generate single PDF with multiple pages
            doc = SimpleDocTemplate(filename, pagesize=A4,
                                    rightMargin=10, leftMargin=10,
                                    topMargin=10, bottomMargin=10)
            
            from reportlab.platypus import PageBreak
            
            # Build story with all customer PDFs
            for customer_id, customer_data in self.selected_customers.items():
                customer = customer_data['customer']
                items = customer_data['items']
                
                # Calculate totals
                total_items_amount = sum(item.get('total_amount', 0) for item in items)
                freight_charges = customer_data.get('freight_charges', 0)
                grand_total = self._round_total(total_items_amount + freight_charges)
                total_in_words = number_to_words(grand_total)
                
                # Prepare invoice data (same structure as single PDF)
                invoice_data = {
                    'invoice_number': customer_data['invoice_no'],
                    'date_of_supply': date_supply,
                    'category': self.current_category,
                    'location_name': self.current_area_name,
                    'vehicle_number': vehicle_number,
                    'customer': customer,
                    'mode_of_transport': self.transport_entry.get() or "Road",
                    'is_original': self.original_var.get(),
                    'is_duplicate': self.duplicate_var.get(),
                    'is_triplicate': self.triplicate_var.get(),
                    'e_way_bill_no': self.e_way_bill_entry.get(),
                    'e_way_document_no': customer_data['e_way_doc_no'],
                    'place_of_supply': customer_data['place_of_supply'],
                    'state_code': '33',  # Default, can be made configurable
                    'gstin_unique_id': '',  # Can be added to customer data if needed
                    'items': items,
                    'freight_charges': freight_charges,
                    'grand_total': grand_total,
                    'total_in_words': total_in_words,
                    'blaster_name': customer.get('blaster_name', ''),
                    'document_no': customer.get('blaster_document_no', ''),
                    'blaster_address': customer.get('blaster_address', '')
                }
                
                # Generate PDF content for this customer
                # We need to use the PDFGenerator's internal method or generate separately
                # For now, let's generate each PDF separately and combine them
                # Actually, ReportLab's SimpleDocTemplate can handle multiple pages
                # We need to modify the PDFGenerator to work with a story list
                
                # For simplicity, let's generate separate PDFs and combine them
                # Or better: modify to use the existing generator but with PageBreak
                pass  # This needs more work - the PDFGenerator creates a complete document
            
            # For now, generate first customer's PDF to test
            # TODO: Implement multi-page PDF generation
            messagebox.showinfo("Info", "Multi-page PDF generation needs to be implemented.\n"
                              "For now, this will generate PDFs separately.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDFs: {str(e)}")
            import traceback
            traceback.print_exc()


class AreasManager:
    """Dialog to manage areas (locations) - common to both categories"""
    def __init__(self, parent, db, callback=None):
        self.db = db
        self.callback = callback
        
        self.window = tk.Toplevel(parent)
        self.window.title("Manage Areas")
        self.window.geometry("600x400")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Make visible on macOS
        self.window.lift()
        self.window.focus_force()
        self.window.attributes('-topmost', True)
        self.window.after(100, lambda: self.window.attributes('-topmost', False))
        
        # Treeview for areas
        columns = ('id', 'name')
        self.tree = ttk.Treeview(self.window, columns=columns, show='headings', height=15)
        self.tree.heading('id', text='ID')
        self.tree.heading('name', text='Area Name')
        self.tree.column('id', width=50)
        self.tree.column('name', width=400)
        
        self.tree.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        
        # Buttons
        btn_frame = ttk.Frame(self.window)
        btn_frame.grid(row=1, column=0, columnspan=3, pady=10)
        
        ttk.Button(btn_frame, text="Add Area", command=self.add_area).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Edit Area", command=self.edit_area).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Area", command=self.delete_area).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=self.window.destroy).pack(side=tk.LEFT, padx=5)
        
        self.refresh_tree()
    
    def refresh_tree(self):
        """Refresh areas tree"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Renumber locations to ensure sequential IDs
        self.db.renumber_locations()
        
        areas = self.db.get_locations()
        for area in areas:
            self.tree.insert('', tk.END, values=(area['id'], area['name']))
    
    def add_area(self):
        """Add new area (common to both categories)"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Add Area")
        dialog.geometry("400x150")
        dialog.transient(self.window)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Area Name:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.grid(row=0, column=1, padx=10, pady=10)
        name_entry.focus()
        
        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Area name cannot be empty")
                return
            try:
                self.db.add_location(name)
                messagebox.showinfo("Success", "Area added successfully")
                self.refresh_tree()
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        
        ttk.Button(dialog, text="Save", command=save).grid(row=1, column=0, columnspan=2, pady=10)
        name_entry.bind('<Return>', lambda e: save())
    
    def edit_area(self):
        """Edit selected area"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an area to edit")
            return
        
        area_id = self.tree.item(selection[0])['values'][0]
        area_name = self.tree.item(selection[0])['values'][1]
        
        dialog = tk.Toplevel(self.window)
        dialog.title("Edit Area")
        dialog.geometry("400x150")
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Make visible on macOS
        dialog.lift()
        dialog.focus_force()
        dialog.attributes('-topmost', True)
        dialog.after(100, lambda: dialog.attributes('-topmost', False))
        
        ttk.Label(dialog, text="Area Name:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.grid(row=0, column=1, padx=10, pady=10)
        name_entry.insert(0, area_name)
        name_entry.focus()
        name_entry.select_range(0, tk.END)
        
        def save():
            new_name = name_entry.get().strip()
            if not new_name:
                messagebox.showerror("Error", "Area name cannot be empty")
                return
            if new_name == area_name:
                dialog.destroy()
                return
            try:
                self.db.update_location(area_id, new_name)
                messagebox.showinfo("Success", "Area updated successfully")
                self.refresh_tree()
                if self.callback:
                    self.callback()
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        
        ttk.Button(dialog, text="Save", command=save).grid(row=1, column=0, columnspan=2, pady=10)
        name_entry.bind('<Return>', lambda e: save())
    
    def delete_area(self):
        """Delete selected area"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an area to delete")
            return
        
        area_id = self.tree.item(selection[0])['values'][0]
        area_name = self.tree.item(selection[0])['values'][1]
        
        if messagebox.askyesno("Confirm", 
                               f"Delete area '{area_name}'?\n\nThis will also delete all vehicles associated with this area."):
            try:
                self.db.delete_location(area_id)
                messagebox.showinfo("Success", "Area deleted successfully")
                self.refresh_tree()
                if self.callback:
                    self.callback()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete area: {str(e)}")


class VehiclesManager:
    """Dialog to manage vehicles - common to all areas and categories"""
    def __init__(self, parent, db, callback=None):
        self.db = db
        self.callback = callback
        
        self.window = tk.Toplevel(parent)
        self.window.title("Manage Vehicles")
        self.window.geometry("600x400")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Make visible on macOS
        self.window.lift()
        self.window.focus_force()
        self.window.attributes('-topmost', True)
        self.window.after(100, lambda: self.window.attributes('-topmost', False))
        
        # Treeview for vehicles
        columns = ('id', 'vehicle_number')
        self.tree = ttk.Treeview(self.window, columns=columns, show='headings', height=15)
        self.tree.heading('id', text='ID')
        self.tree.heading('vehicle_number', text='Vehicle Number')
        self.tree.column('id', width=50)
        self.tree.column('vehicle_number', width=400)
        
        self.tree.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        
        # Buttons
        btn_frame = ttk.Frame(self.window)
        btn_frame.grid(row=1, column=0, columnspan=3, pady=10)
        
        ttk.Button(btn_frame, text="Add Vehicle", command=self.add_vehicle).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Vehicle", command=self.delete_vehicle).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=self.window.destroy).pack(side=tk.LEFT, padx=5)
        
        self.refresh_tree()
    
    def refresh_tree(self):
        """Refresh vehicles tree"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Renumber vehicles to ensure sequential IDs
        self.db.renumber_vehicles()
        
        vehicles = self.db.get_vehicles()
        for vehicle in vehicles:
            self.tree.insert('', tk.END, values=(vehicle['id'], vehicle['vehicle_number']))
    
    def add_vehicle(self):
        """Add new vehicle"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Add Vehicle")
        dialog.geometry("400x150")
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Make visible on macOS
        dialog.lift()
        dialog.focus_force()
        dialog.attributes('-topmost', True)
        dialog.after(100, lambda: dialog.attributes('-topmost', False))
        
        ttk.Label(dialog, text="Vehicle Number:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.grid(row=0, column=1, padx=10, pady=10)
        name_entry.focus()
        
        def save():
            vehicle_number = name_entry.get().strip()
            if not vehicle_number:
                messagebox.showerror("Error", "Vehicle number cannot be empty")
                return
            try:
                self.db.add_vehicle(vehicle_number)
                messagebox.showinfo("Success", "Vehicle added successfully")
                self.refresh_tree()
                if self.callback:
                    self.callback()
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Error", str(e))
        
        ttk.Button(dialog, text="Save", command=save).grid(row=1, column=0, columnspan=2, pady=10)
        name_entry.bind('<Return>', lambda e: save())
    
    def delete_vehicle(self):
        """Delete selected vehicle"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a vehicle to delete")
            return
        
        vehicle_id = self.tree.item(selection[0])['values'][0]
        vehicle_number = self.tree.item(selection[0])['values'][1]
        
        if messagebox.askyesno("Confirm", 
                               f"Delete vehicle '{vehicle_number}'?"):
            try:
                self.db.delete_vehicle(vehicle_id)
                messagebox.showinfo("Success", "Vehicle deleted successfully")
                self.refresh_tree()
                if self.callback:
                    self.callback()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete vehicle: {str(e)}")


class CustomersManager:
    """Dialog to manage customers for a specific area"""
    def __init__(self, parent, db, location_id=None, callback=None):
        self.db = db
        self.location_id = location_id
        self.callback = callback
        
        self.window = tk.Toplevel(parent)
        title = "Manage Customers" if location_id else "Manage Customers (All Areas)"
        self.window.title(title)
        self.window.geometry("900x500")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Make visible on macOS
        self.window.lift()
        self.window.focus_force()
        self.window.attributes('-topmost', True)
        self.window.after(100, lambda: self.window.attributes('-topmost', False))
        
        # Treeview for customers
        columns = ('id', 'name', 'address', 'sf_no', 'rc_no', 'state', 'gstin', 'blaster_name')
        self.tree = ttk.Treeview(self.window, columns=columns, show='headings', height=15)
        self.tree.heading('id', text='ID')
        self.tree.heading('name', text='Name')
        self.tree.heading('address', text='Address')
        self.tree.heading('sf_no', text='SF.NO')
        self.tree.heading('rc_no', text='RC.NO')
        self.tree.heading('state', text='State')
        self.tree.heading('gstin', text='GSTIN')
        self.tree.heading('blaster_name', text='Blaster Name')
        
        self.tree.column('id', width=50)
        self.tree.column('name', width=150)
        self.tree.column('address', width=200)
        self.tree.column('sf_no', width=100)
        self.tree.column('rc_no', width=100)
        self.tree.column('state', width=80)
        self.tree.column('gstin', width=120)
        self.tree.column('blaster_name', width=150)
        
        self.tree.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.window, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=0, column=4, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Buttons
        btn_frame = ttk.Frame(self.window)
        btn_frame.grid(row=1, column=0, columnspan=4, pady=10)
        
        ttk.Button(btn_frame, text="Add Customer", command=self.add_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Edit Customer", command=self.edit_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Customer", command=self.delete_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=self.window.destroy).pack(side=tk.LEFT, padx=5)
        
        self.refresh_tree()
    
    def refresh_tree(self):
        """Refresh customers tree"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Renumber customers to ensure sequential IDs
        self.db.renumber_customers()
        
        customers = self.db.get_customers(location_id=self.location_id) if self.location_id else self.db.get_customers()
        for customer in customers:
            self.tree.insert('', tk.END, values=(
                customer['id'],
                customer.get('name', ''),
                customer.get('address', ''),
                customer.get('sf_no', ''),
                customer.get('rc_no', ''),
                customer.get('state', ''),
                customer.get('gstin', ''),
                customer.get('blaster_name', '')
            ))
    
    def add_customer(self):
        """Add new customer"""
        if not self.location_id:
            messagebox.showwarning("Warning", "This dialog is for area-specific customers. Please select an area first.")
            return
        
        dialog = tk.Toplevel(self.window)
        dialog.title("Add Customer")
        dialog.geometry("500x500")
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Make visible on macOS
        dialog.lift()
        dialog.focus_force()
        dialog.attributes('-topmost', True)
        dialog.after(100, lambda: dialog.attributes('-topmost', False))
        
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
        
        # Blaster selection
        row_idx = len(fields)
        ttk.Label(dialog, text="Blaster:").grid(row=row_idx, column=0, padx=10, pady=5, sticky=tk.W)
        blaster_combo = ttk.Combobox(dialog, width=37, state="readonly")
        blasters = self.db.get_blasters()
        blaster_names = [b['name'] for b in blasters]
        blaster_combo['values'] = blaster_names
        blaster_combo.grid(row=row_idx, column=1, padx=10, pady=5)
        
        blaster_btn_frame = ttk.Frame(dialog)
        blaster_btn_frame.grid(row=row_idx, column=2, padx=5, pady=5)
        ttk.Button(blaster_btn_frame, text="Add", command=lambda: self._quick_add_blaster_in_dialog(dialog, blaster_combo)).pack(side=tk.LEFT, padx=2)
        
        entries['name'].focus()
        
        def save():
            name = entries['name'].get().strip()
            if not name:
                messagebox.showerror("Error", "Customer name is required")
                return
            
            # Get selected blaster ID
            selected_blaster_name = blaster_combo.get()
            blaster_id = None
            if selected_blaster_name:
                blaster = next((b for b in blasters if b['name'] == selected_blaster_name), None)
                if blaster:
                    blaster_id = blaster['id']
            
            try:
                self.db.add_customer(
                    name,
                    entries['address'].get().strip(),
                    entries['sf_no'].get().strip(),
                    entries['rc_no'].get().strip(),
                    entries['state'].get().strip(),
                    entries['gstin'].get().strip(),
                    blaster_id,
                    location_id=self.location_id
                )
                messagebox.showinfo("Success", "Customer added successfully")
                self.refresh_tree()
                if self.callback:
                    self.callback()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add customer: {str(e)}")
        
        ttk.Button(dialog, text="Save", command=save).grid(row=row_idx+1, column=0, columnspan=2, pady=20)
        entries['name'].bind('<Return>', lambda e: entries['address'].focus())
    
    def edit_customer(self):
        """Edit selected customer"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a customer to edit")
            return
        
        customer_id = self.tree.item(selection[0])['values'][0]
        customer = self.db.get_customer(customer_id)
        if not customer:
            messagebox.showerror("Error", "Customer not found")
            return
        
        dialog = tk.Toplevel(self.window)
        dialog.title("Edit Customer")
        dialog.geometry("500x500")
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Make visible on macOS
        dialog.lift()
        dialog.focus_force()
        dialog.attributes('-topmost', True)
        dialog.after(100, lambda: dialog.attributes('-topmost', False))
        
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
            entry.insert(0, customer.get(key, ''))
            entries[key] = entry
        
        # Blaster selection
        row_idx = len(fields)
        ttk.Label(dialog, text="Blaster:").grid(row=row_idx, column=0, padx=10, pady=5, sticky=tk.W)
        blaster_combo = ttk.Combobox(dialog, width=37, state="readonly")
        blasters = self.db.get_blasters()
        blaster_names = [b['name'] for b in blasters]
        blaster_combo['values'] = blaster_names
        # Pre-select current blaster
        current_blaster_name = customer.get('blaster_name', '')
        if current_blaster_name:
            blaster_combo.set(current_blaster_name)
        blaster_combo.grid(row=row_idx, column=1, padx=10, pady=5)
        
        blaster_btn_frame = ttk.Frame(dialog)
        blaster_btn_frame.grid(row=row_idx, column=2, padx=5, pady=5)
        ttk.Button(blaster_btn_frame, text="Add", command=lambda: self._quick_add_blaster_in_dialog(dialog, blaster_combo)).pack(side=tk.LEFT, padx=2)
        
        entries['name'].focus()
        entries['name'].select_range(0, tk.END)
        
        def save():
            name = entries['name'].get().strip()
            if not name:
                messagebox.showerror("Error", "Customer name is required")
                return
            
            # Get selected blaster ID
            selected_blaster_name = blaster_combo.get()
            blaster_id = None
            if selected_blaster_name:
                blaster = next((b for b in blasters if b['name'] == selected_blaster_name), None)
                if blaster:
                    blaster_id = blaster['id']
            
            try:
                self.db.update_customer(
                    customer_id,
                    name,
                    entries['address'].get().strip(),
                    entries['sf_no'].get().strip(),
                    entries['rc_no'].get().strip(),
                    entries['state'].get().strip(),
                    entries['gstin'].get().strip(),
                    blaster_id,
                    location_id=customer.get('location_id') or self.location_id
                )
                messagebox.showinfo("Success", "Customer updated successfully")
                self.refresh_tree()
                if self.callback:
                    self.callback()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update customer: {str(e)}")
        
        ttk.Button(dialog, text="Save", command=save).grid(row=row_idx+1, column=0, columnspan=2, pady=20)
        entries['name'].bind('<Return>', lambda e: entries['address'].focus())
    
    def _quick_add_blaster_in_dialog(self, parent_dialog, blaster_combo):
        """Quick add blaster from within a dialog (for CustomersManager)"""
        dialog = tk.Toplevel(parent_dialog)
        dialog.title("Add Blaster")
        dialog.geometry("500x280")
        dialog.transient(parent_dialog)
        dialog.grab_set()
        
        # Make visible on macOS
        dialog.lift()
        dialog.focus_force()
        dialog.attributes('-topmost', True)
        dialog.after(100, lambda: dialog.attributes('-topmost', False))
        
        fields = [
            ("Name *", "name"),
            ("Document No", "document_no"),
            ("Address", "address")
        ]
        
        entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(dialog, text=label, font=('Helvetica', 10)).grid(row=idx, column=0, padx=15, pady=8, sticky=tk.W)
            if key == 'address':
                entry = tk.Text(dialog, width=40, height=3, wrap=tk.WORD, font=('Helvetica', 10))
                entry.grid(row=idx, column=1, padx=15, pady=8, sticky=(tk.W, tk.E))
            else:
                entry = ttk.Entry(dialog, width=42, font=('Helvetica', 10))
                entry.grid(row=idx, column=1, padx=15, pady=8, sticky=(tk.W, tk.E))
            entries[key] = entry
            dialog.columnconfigure(1, weight=1)
        
        entries['name'].focus()
        
        def save():
            name = entries['name'].get().strip() if isinstance(entries['name'], tk.Text) else entries['name'].get().strip()
            if isinstance(entries['document_no'], tk.Text):
                document_no = entries['document_no'].get("1.0", tk.END).strip()
            else:
                document_no = entries['document_no'].get().strip()
            if isinstance(entries['address'], tk.Text):
                address = entries['address'].get("1.0", tk.END).strip()
            else:
                address = entries['address'].get().strip()
            
            if not name:
                messagebox.showerror("Error", "Blaster name is required")
                return
            try:
                self.db.add_blaster(name, document_no, address)
                messagebox.showinfo("Success", "Blaster added successfully")
                # Refresh the combobox in the parent dialog
                blasters = self.db.get_blasters()
                blaster_names = [b['name'] for b in blasters]
                blaster_combo['values'] = blaster_names
                blaster_combo.set(name)
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add blaster: {str(e)}")
        
        ttk.Button(dialog, text="Save", command=save, width=12).grid(row=len(fields), column=0, columnspan=2, pady=20)
        entries['name'].bind('<Return>', lambda e: entries['document_no'].focus())
    
    def delete_customer(self):
        """Delete selected customer"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a customer to delete")
            return
        
        customer_id = self.tree.item(selection[0])['values'][0]
        customer_name = self.tree.item(selection[0])['values'][1]
        
        if messagebox.askyesno("Confirm", 
                               f"Delete customer '{customer_name}'?\n\nThis action cannot be undone."):
            try:
                self.db.delete_customer(customer_id)
                messagebox.showinfo("Success", "Customer deleted successfully")
                self.refresh_tree()
                if self.callback:
                    self.callback()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete customer: {str(e)}")


class BlastersManager:
    """Dialog to manage blasters"""
    def __init__(self, parent, db, callback=None):
        self.db = db
        self.callback = callback
        
        self.window = tk.Toplevel(parent)
        self.window.title("Manage Blasters")
        self.window.geometry("850x500")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Make visible on macOS
        self.window.lift()
        self.window.focus_force()
        self.window.attributes('-topmost', True)
        self.window.after(100, lambda: self.window.attributes('-topmost', False))
        
        # Treeview for blasters
        columns = ('id', 'name', 'document_no', 'address')
        self.tree = ttk.Treeview(self.window, columns=columns, show='headings', height=15)
        self.tree.heading('id', text='ID')
        self.tree.heading('name', text='Name')
        self.tree.heading('document_no', text='Document No')
        self.tree.heading('address', text='Address')
        
        self.tree.column('id', width=60)
        self.tree.column('name', width=200)
        self.tree.column('document_no', width=150)
        self.tree.column('address', width=350)
        
        self.tree.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=1)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.window, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=0, column=4, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Buttons
        btn_frame = ttk.Frame(self.window)
        btn_frame.grid(row=1, column=0, columnspan=4, pady=10)
        
        ttk.Button(btn_frame, text="Add Blaster", command=self.add_blaster).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Edit Blaster", command=self.edit_blaster).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Blaster", command=self.delete_blaster).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=self.window.destroy).pack(side=tk.LEFT, padx=5)
        
        self.refresh_tree()
    
    def refresh_tree(self):
        """Refresh blasters tree"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Renumber blasters to ensure sequential IDs
        self.db.renumber_blasters()
        
        blasters = self.db.get_blasters()
        for blaster in blasters:
            self.tree.insert('', tk.END, values=(
                blaster['id'],
                blaster.get('name', ''),
                blaster.get('document_no', ''),
                blaster.get('address', '')
            ))
    
    def add_blaster(self):
        """Add new blaster"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Add Blaster")
        dialog.geometry("520x280")
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Make visible on macOS
        dialog.lift()
        dialog.focus_force()
        dialog.attributes('-topmost', True)
        dialog.after(100, lambda: dialog.attributes('-topmost', False))
        
        fields = [
            ("Name *", "name"),
            ("Document No", "document_no"),
            ("Address", "address")
        ]
        
        entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(dialog, text=label, font=('Helvetica', 10)).grid(row=idx, column=0, padx=15, pady=8, sticky=tk.W)
            if key == 'address':
                entry = tk.Text(dialog, width=40, height=3, wrap=tk.WORD, font=('Helvetica', 10))
                entry.grid(row=idx, column=1, padx=15, pady=8, sticky=(tk.W, tk.E))
            else:
                entry = ttk.Entry(dialog, width=42, font=('Helvetica', 10))
                entry.grid(row=idx, column=1, padx=15, pady=8, sticky=(tk.W, tk.E))
            entries[key] = entry
            dialog.columnconfigure(1, weight=1)
        
        entries['name'].focus()
        
        def save():
            name = entries['name'].get().strip() if isinstance(entries['name'], tk.Text) else entries['name'].get().strip()
            if isinstance(entries['document_no'], tk.Text):
                document_no = entries['document_no'].get("1.0", tk.END).strip()
            else:
                document_no = entries['document_no'].get().strip()
            if isinstance(entries['address'], tk.Text):
                address = entries['address'].get("1.0", tk.END).strip()
            else:
                address = entries['address'].get().strip()
            
            if not name:
                messagebox.showerror("Error", "Blaster name is required")
                return
            try:
                self.db.add_blaster(name, document_no, address)
                messagebox.showinfo("Success", "Blaster added successfully")
                self.refresh_tree()
                if self.callback:
                    self.callback()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add blaster: {str(e)}")
        
        ttk.Button(dialog, text="Save", command=save, width=12).grid(row=len(fields), column=0, columnspan=2, pady=20)
        entries['name'].bind('<Return>', lambda e: entries['document_no'].focus())
    
    def edit_blaster(self):
        """Edit selected blaster"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a blaster to edit")
            return
        
        blaster_id = self.tree.item(selection[0])['values'][0]
        blaster = self.db.get_blaster(blaster_id)
        if not blaster:
            messagebox.showerror("Error", "Blaster not found")
            return
        
        dialog = tk.Toplevel(self.window)
        dialog.title("Edit Blaster")
        dialog.geometry("520x280")
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Make visible on macOS
        dialog.lift()
        dialog.focus_force()
        dialog.attributes('-topmost', True)
        dialog.after(100, lambda: dialog.attributes('-topmost', False))
        
        fields = [
            ("Name *", "name"),
            ("Document No", "document_no"),
            ("Address", "address")
        ]
        
        entries = {}
        for idx, (label, key) in enumerate(fields):
            ttk.Label(dialog, text=label, font=('Helvetica', 10)).grid(row=idx, column=0, padx=15, pady=8, sticky=tk.W)
            if key == 'address':
                entry = tk.Text(dialog, width=40, height=3, wrap=tk.WORD, font=('Helvetica', 10))
                entry.insert("1.0", blaster.get(key, ''))
                entry.grid(row=idx, column=1, padx=15, pady=8, sticky=(tk.W, tk.E))
            else:
                entry = ttk.Entry(dialog, width=42, font=('Helvetica', 10))
                entry.insert(0, blaster.get(key, ''))
                entry.grid(row=idx, column=1, padx=15, pady=8, sticky=(tk.W, tk.E))
            entries[key] = entry
            dialog.columnconfigure(1, weight=1)
        
        entries['name'].focus()
        entries['name'].select_range(0, tk.END)
        
        def save():
            name = entries['name'].get().strip() if isinstance(entries['name'], tk.Text) else entries['name'].get().strip()
            if isinstance(entries['document_no'], tk.Text):
                document_no = entries['document_no'].get("1.0", tk.END).strip()
            else:
                document_no = entries['document_no'].get().strip()
            if isinstance(entries['address'], tk.Text):
                address = entries['address'].get("1.0", tk.END).strip()
            else:
                address = entries['address'].get().strip()
            
            if not name:
                messagebox.showerror("Error", "Blaster name is required")
                return
            try:
                self.db.update_blaster(blaster_id, name, document_no, address)
                messagebox.showinfo("Success", "Blaster updated successfully")
                self.refresh_tree()
                if self.callback:
                    self.callback()
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update blaster: {str(e)}")
        
        ttk.Button(dialog, text="Save", command=save, width=12).grid(row=len(fields), column=0, columnspan=2, pady=20)
        entries['name'].bind('<Return>', lambda e: entries['document_no'].focus())
    
    def delete_blaster(self):
        """Delete selected blaster"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a blaster to delete")
            return
        
        blaster_id = self.tree.item(selection[0])['values'][0]
        blaster_name = self.tree.item(selection[0])['values'][1]
        
        if messagebox.askyesno("Confirm", 
                               f"Delete blaster '{blaster_name}'?\n\nCustomers using this blaster will have their blaster reference removed."):
            try:
                self.db.delete_blaster(blaster_id)
                messagebox.showinfo("Success", "Blaster deleted successfully")
                self.refresh_tree()
                if self.callback:
                    self.callback()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete blaster: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = BatchDeliveryBillApp(root)
    root.mainloop()

