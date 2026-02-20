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
root.geometry("900x650")

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
qty_entry = tk.Entry(frame2, width=10)
qty_entry.grid(row=0, column=2)

tk.Label(frame2, text="Total Amount").grid(row=0, column=3)
total_entry = tk.Entry(frame2, width=10)
total_entry.grid(row=0, column=4)

tk.Label(frame2, text="Rate").grid(row=0, column=5)
rate_label = tk.Label(frame2, text="0")
rate_label.grid(row=0, column=6)

# ---------- AUTO RATE ----------
def calculate_rate(event):
    try:
        qty = float(qty_entry.get())
        total = float(total_entry.get())
        rate = total / qty
        rate_label.config(text=f"{rate:.2f}")
    except:
        rate_label.config(text="0")

qty_entry.bind("<KeyRelease>", calculate_rate)
total_entry.bind("<KeyRelease>", calculate_rate)

# ---------- TABLE ----------
columns = ("Product", "Boxes", "Total", "Rate")
tree = ttk.Treeview(root, columns=columns, show="headings")

for col in columns:
    tree.heading(col, text=col)

tree.pack(pady=20, fill="x")

items = []

# ---------- ADD ITEM ----------
def add_item():
    product = search_entry.get()
    qty = qty_entry.get()
    total = total_entry.get()
    rate = rate_label.cget("text")

    if not product or not qty or not total:
        messagebox.showerror("Error", "Fill all fields")
        return

    if product not in product_dict:
        messagebox.showerror("Error", "Product not found! Use ➕ Add Product")
        return

    items.append((product, int(qty), float(total)))
    tree.insert("", tk.END, values=(product, qty, total, rate))

    update_total()

    search_entry.delete(0, tk.END)
    qty_entry.delete(0, tk.END)
    total_entry.delete(0, tk.END)
    rate_label.config(text="0")

# ---------- DELETE ITEM ----------
def delete_item():
    selected = tree.selection()
    if not selected:
        return

    for item in selected:
        index = tree.index(item)
        tree.delete(item)
        items.pop(index)

    update_total()

# ---------- TOTAL ----------
total_label = tk.Label(root, text="Total: 0", font=("Arial", 12, "bold"))
total_label.pack()

def update_total():
    total = sum(item[2] for item in items)
    total_label.config(text=f"Total: {total:.2f}")

# ---------- ADD NEW PRODUCT ----------
def add_new_product():

    def save_product():
        brand = brand_entry.get()
        name = name_entry.get()
        category = category_entry.get()
        pack = pack_entry.get()
        pieces = pieces_entry.get()
        dealer = dealer_entry.get()
        mrp = mrp_entry.get()

        if not brand or not name:
            messagebox.showerror("Error", "Brand & Name required")
            return

        try:
            cursor.execute("""
                INSERT INTO Products
                (Brand, ProductName, Category, PackSize, Pieces_Per_Box, DealerRate_With_GST, MRP_Per_Piece)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            brand,
            name,
            category if category else None,
            pack if pack else None,
            int(pieces) if pieces else None,
            float(dealer) if dealer else None,
            float(mrp) if mrp else 0)

            conn.commit()

            messagebox.showinfo("Success", "Product Added!")

            popup.destroy()

            global product_dict, product_list
            product_dict = load_products()
            product_list = list(product_dict.keys())

        except Exception as e:
            messagebox.showerror("Error", str(e))

    popup = tk.Toplevel(root)
    popup.title("Add Product")
    popup.geometry("300x420")

    tk.Label(popup, text="Brand").pack()
    brand_entry = tk.Entry(popup)
    brand_entry.pack()

    tk.Label(popup, text="Product Name").pack()
    name_entry = tk.Entry(popup)
    name_entry.pack()

    tk.Label(popup, text="Category").pack()
    category_entry = tk.Entry(popup)
    category_entry.pack()

    tk.Label(popup, text="Pack Size").pack()
    pack_entry = tk.Entry(popup)
    pack_entry.pack()

    tk.Label(popup, text="Pieces/Box").pack()
    pieces_entry = tk.Entry(popup)
    pieces_entry.pack()

    tk.Label(popup, text="Dealer Rate").pack()
    dealer_entry = tk.Entry(popup)
    dealer_entry.pack()

    tk.Label(popup, text="MRP").pack()
    mrp_entry = tk.Entry(popup)
    mrp_entry.pack()

    tk.Button(popup, text="Save Product", command=save_product, bg="green", fg="white").pack(pady=10)

# ---------- SAVE ----------
def save_all():
    invoice = invoice_entry.get()
    supplier = supplier_entry.get()
    date = date_entry.get_date()

    if not items:
        messagebox.showerror("Error", "Add items first")
        return

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

# ---------- BUTTONS ----------
btn_frame = tk.Frame(root)
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="Add Item", command=add_item, bg="green", fg="white").grid(row=0, column=0, padx=10)
tk.Button(btn_frame, text="Delete Item", command=delete_item, bg="red", fg="white").grid(row=0, column=1, padx=10)
tk.Button(btn_frame, text="Save Invoice", command=save_all, bg="blue", fg="white").grid(row=0, column=2, padx=10)
tk.Button(btn_frame, text="➕ Add Product", command=add_new_product, bg="orange").grid(row=0, column=3, padx=10)

root.mainloop()
