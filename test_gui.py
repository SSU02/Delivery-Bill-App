"""
Test script to debug GUI issues on macOS
"""
import tkinter as tk
from tkinter import ttk, messagebox
from database import Database

def test_add_good_dialog():
    """Test if the add good dialog appears"""
    root = tk.Tk()
    root.title("Test - Add Good Dialog")
    root.geometry("400x200")
    
    db = Database()
    
    def show_dialog():
        dialog = tk.Toplevel(root)
        dialog.title("Add Good - Test")
        dialog.geometry("450x280")
        dialog.transient(root)
        dialog.grab_set()
        dialog.lift()  # Bring to front
        dialog.focus_force()  # Force focus on macOS
        
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
        unit_combo = ttk.Combobox(dialog, width=32, values=['NOS', 'Kilograms'], state="readonly")
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
                return
            
            if not hsn_code:
                messagebox.showerror("Error", "HSN Code is required")
                return
            
            try:
                rate = float(rate_entry.get())
                if rate <= 0:
                    raise ValueError("Rate must be greater than 0")
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid rate: {str(e)}")
                return
            
            try:
                good_id = db.add_good(description, hsn_code, unit, rate)
                messagebox.showinfo("Success", f"Good added successfully!\nID: {good_id}")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add good: {str(e)}")
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Save", command=save_good).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Make sure dialog is on top (macOS specific)
        dialog.attributes('-topmost', True)
        dialog.after(100, lambda: dialog.attributes('-topmost', False))
    
    ttk.Label(root, text="Click button to test Add Good dialog:").pack(pady=20)
    ttk.Button(root, text="Test Add Good Dialog", command=show_dialog).pack(pady=10)
    ttk.Button(root, text="Exit", command=root.quit).pack(pady=10)
    
    root.mainloop()

if __name__ == "__main__":
    test_add_good_dialog()

