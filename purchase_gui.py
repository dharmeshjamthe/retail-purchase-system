import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import pyodbc

# ---------- DB CONNECTION ----------
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=localhost\\SQLEXPRESS;'
    'DATABASE=ShopRetail;'
    'Trusted_Connection=yes;'
)
cursor = conn.cursor()

# ---------- LOAD PRODUCTS ----------
def load_products():
    cursor.execute("SELECT ProductID, Brand + ' - ' + ProductName FROM Products")
    data = cursor.fetchall()
    return {row[1]: row[0] for row in data}

product_dict = load_products()
product_list = list(product_dict.keys())

# ---------- GUI ----------
root = tk.Tk()
root.title("Retail Purchase System")
root.geometry("1000x700")

tk.Label(root, text="Purchase Entry", font=("Arial", 18, "bold")).pack(pady=10)

# ---------- HEADER ----------
frame1 = tk.Frame(root)
frame1.pack(pady=10)

tk.Label(frame1, text="Invoice No").grid(row=0, column=0)
invoice_entry = tk.Entry(frame1)
invoice_entry.grid(row=0, column=1)

tk.Label(frame1, text="Date").grid(row=0, column=2)
date_entry = DateEntry(frame1)
date_entry.grid(row=0, column=3)

tk.Label(frame1, text="Supplier").grid(row=0, column=4)
supplier_entry = tk.Entry(frame1)
supplier_entry.grid(row=0, column=5)

# ---------- SEARCH ----------
frame2 = tk.Frame(root)
frame2.pack(pady=10)

search_entry = tk.Entry(frame2, width=40)
search_entry.grid(row=0, column=0)

listbox = tk.Listbox(frame2, width=40, height=5)
listbox.grid(row=1, column=0)

def update_list(event):
    typed = search_entry.get().lower()
    listbox.delete(0, tk.END)
    for item in product_list:
        if typed in item.lower():
            listbox.insert(tk.END, item)

search_entry.bind("<KeyRelease>", update_list)

def select_item(event):
    try:
        selected = listbox.get(listbox.curselection())
        search_entry.delete(0, tk.END)
        search_entry.insert(0, selected)
        listbox.delete(0, tk.END)
    except:
        pass

listbox.bind("<Double-Button-1>", select_item)

# ---------- INPUT ----------
tk.Label(frame2, text="Boxes").grid(row=0, column=1)
qty_entry = tk.Entry(frame2, width=8)
qty_entry.grid(row=0, column=2)

tk.Label(frame2, text="Total Amount").grid(row=0, column=3)
total_entry = tk.Entry(frame2, width=10)
total_entry.grid(row=0, column=4)

tk.Label(frame2, text="Final Rate/Box").grid(row=0, column=5)
rate_label = tk.Label(frame2, text="0")
rate_label.grid(row=0, column=6)

tk.Label(frame2, text="GST Type").grid(row=0, column=7)
gst_combo = ttk.Combobox(frame2, values=["INCLUDED", "EXTRA"], width=10)
gst_combo.grid(row=0, column=8)
gst_combo.set("INCLUDED")

tk.Label(frame2, text="GST %").grid(row=0, column=9)
gst_entry = tk.Entry(frame2, width=5)
gst_entry.grid(row=0, column=10)
gst_entry.insert(0, "5")

# ---------- AUTO CALC ----------
def calculate_rate(event):
    try:
        qty = float(qty_entry.get())
        total = float(total_entry.get())
        gst_type = gst_combo.get()
        gst_percent = float(gst_entry.get())

        if gst_type == "EXTRA":
            final_total = total * (1 + gst_percent / 100)
        else:
            final_total = total

        rate = final_total / qty
        rate_label.config(text=f"{rate:.2f}")
    except:
        rate_label.config(text="0")

qty_entry.bind("<KeyRelease>", calculate_rate)
total_entry.bind("<KeyRelease>", calculate_rate)

# ---------- TABLE ----------
columns = ("Product", "Boxes", "Final Total", "Rate/Box", "GST")
tree = ttk.Treeview(root, columns=columns, show="headings")

for col in columns:
    tree.heading(col, text=col)

tree.pack(pady=20, fill="x")

items = []

def update_total():
    total = sum(item[2] for item in items)
    total_label.config(text=f"Total: {total:.2f}")

total_label = tk.Label(root, text="Total: 0", font=("Arial", 12, "bold"))
total_label.pack()

# ---------- ADD ITEM ----------
def add_item():
    product = search_entry.get()
    qty = float(qty_entry.get())
    total = float(total_entry.get())
    gst_type = gst_combo.get()
    gst_percent = float(gst_entry.get())

    if product not in product_dict:
        messagebox.showerror("Error", "Select valid product")
        return

    if gst_type == "EXTRA":
        final_total = total * (1 + gst_percent / 100)
    else:
        final_total = total

    rate = final_total / qty

    items.append((product, int(qty), final_total))

    tree.insert("", tk.END, values=(
        product,
        int(qty),
        f"{final_total:.2f}",
        f"{rate:.2f}",
        gst_type
    ))

    update_total()

# ---------- DELETE ITEM ----------
def delete_item():
    selected = tree.selection()
    for item in selected:
        index = tree.index(item)
        tree.delete(item)
        items.pop(index)
    update_total()

# ---------- SAVE ----------
def save_all():
    invoice = invoice_entry.get()
    supplier = supplier_entry.get()
    date = date_entry.get_date()

    for item in items:
        product_id = product_dict[item[0]]
        cursor.execute("""
            INSERT INTO Purchases
            (PurchaseDate, ProductID, SupplierName, InvoiceNumber, BoxQuantity, TotalPurchaseAmount)
            VALUES (?, ?, ?, ?, ?, ?)
        """, date, product_id, supplier, invoice, item[1], item[2])

    conn.commit()
    messagebox.showinfo("Success", "Invoice Saved!")

    tree.delete(*tree.get_children())
    items.clear()
    update_total()

# ---------- MULTIPLE PRODUCT ADD ----------
def add_new_product():

    product_items = []

    def add_to_list():
        brand = brand_combo.get()
        name = name_entry.get()

        if not brand or not name:
            messagebox.showerror("Error", "Brand & Product required")
            return

        product_items.append((
            brand,
            name,
            category_entry.get(),
            pack_entry.get(),
            pieces_entry.get(),
            dealer_entry.get(),
            mrp_entry.get()
        ))

        product_tree.insert("", tk.END, values=(
            brand, name, category_entry.get(),
            pack_entry.get(), pieces_entry.get(),
            dealer_entry.get(), mrp_entry.get()
        ))

        name_entry.delete(0, tk.END)

    def save_all_products():
        for item in product_items:
            cursor.execute("""
                INSERT INTO Products
                (Brand, ProductName, Category, PackSize, Pieces_Per_Box, DealerRate_With_GST, MRP_Per_Piece)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            item[0],
            item[1],
            item[2] if item[2] else None,
            item[3] if item[3] else None,
            int(item[4]) if item[4] else None,
            float(item[5]) if item[5] else None,
            float(item[6]) if item[6] else 0
            )

        conn.commit()
        popup.destroy()

        global product_dict, product_list
        product_dict = load_products()
        product_list = list(product_dict.keys())

        messagebox.showinfo("Success", "Products Saved!")

    popup = tk.Toplevel(root)
    popup.title("Add Multiple Products")
    popup.geometry("800x500")

    form = tk.Frame(popup)
    form.pack(pady=10)

    tk.Label(form, text="Brand").grid(row=0, column=0)
    brand_combo = ttk.Combobox(form, values=[
        "Top N Town", "Havmor", "Cadbury", "Lays",
        "ITC", "Marlboro", "Bisleri", "Elite"
    ])
    brand_combo.grid(row=0, column=1)

    tk.Label(form, text="Product Name").grid(row=0, column=2)
    name_entry = tk.Entry(form)
    name_entry.grid(row=0, column=3)

    tk.Label(form, text="Category").grid(row=1, column=0)
    category_entry = tk.Entry(form)
    category_entry.grid(row=1, column=1)

    tk.Label(form, text="Pack Size").grid(row=1, column=2)
    pack_entry = tk.Entry(form)
    pack_entry.grid(row=1, column=3)

    tk.Label(form, text="Pieces").grid(row=2, column=0)
    pieces_entry = tk.Entry(form)
    pieces_entry.grid(row=2, column=1)

    tk.Label(form, text="Dealer Rate").grid(row=2, column=2)
    dealer_entry = tk.Entry(form)
    dealer_entry.grid(row=2, column=3)

    tk.Label(form, text="MRP").grid(row=3, column=0)
    mrp_entry = tk.Entry(form)
    mrp_entry.grid(row=3, column=1)

    tk.Button(form, text="Add To List", command=add_to_list,
              bg="green", fg="white").grid(row=3, column=3)

    columns = ("Brand","Product","Category","Pack","Pieces","Dealer","MRP")
    product_tree = ttk.Treeview(popup, columns=columns, show="headings")

    for col in columns:
        product_tree.heading(col, text=col)

    product_tree.pack(fill="both", expand=True)

    tk.Button(popup, text="Save All Products",
              command=save_all_products,
              bg="blue", fg="white").pack(pady=10)

# ---------- BUTTONS ----------
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="Add Item", command=add_item, bg="green", fg="white").grid(row=0, column=0, padx=10)
tk.Button(btn_frame, text="Delete Item", command=delete_item, bg="red", fg="white").grid(row=0, column=1, padx=10)
tk.Button(btn_frame, text="Save Invoice", command=save_all, bg="blue", fg="white").grid(row=0, column=2, padx=10)
tk.Button(btn_frame, text="➕ Add Product", command=add_new_product, bg="orange").grid(row=0, column=3, padx=10)

root.mainloop()