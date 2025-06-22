import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import json
import os

# --- Core Stats ---
food = 100
energy = 100
balance = 0.0
save_file = "savegame.json"
inventory = {}
injuries = {}
structures = {}  # name: [item1, item2, ...]
structure_buttons = {}

# --- Injury System Config ---
limbs = ["Head", "Upper Torso", "Lower Torso", "Left Arm", "Left Hand", "Right Arm", "Right Hand", "Left Leg", "Left Foot", "Right Leg", "Right Foot"]
injury_severity = {
    "Minor": ["Bruise", "Cut", "Stab", "Scratch", "Sprain", "Burn (1st Degree)", "Bleeding"],
    "Serious": ["Bruise", "Deep Cut", "Stab", "Gunwound", "Burn (2nd Degree)", "Fracture", "Broken Bone", "Eletrical Burn", "Bleeding", "Infection"],
    "Major": ["Gunwound", "Severe Burn", "Shattered Bone", "Impaled", "Crushed", "Amputated", "Plasma Burn", "Bleeding", "Internal Bleeding"]
}
injury_buttons = {}

# --- Custom Bars (NEW) ---
custom_bars = {}  # name: { 'value': int, 'rate': int, 'widget': progressbar, 'label': tk.StringVar(), 'name': str }
pause_all = False

# --- Helper Functions ---
def clamp(val): return max(0, min(100, val))

def get_food_status(val):
    if val <= 0: 
        death_screen()
        return "Dead", ""
    elif val < 55: return "Starving", "Your on the brink of death. You heavily struggle to do basic tasks such as walking and may even pass out."
    elif val < 65: return "Hungry", "You need food. May have intense stomach and gut pain."
    elif val < 75: return "Peckish", "You really need a snack. May have a headache or chest pain."
    return "Normal", "No Penalty"

def get_energy_status(val):
    if val <= 0: 
        death_screen()
        return "Dead", ""
    elif val < 55: return "Exhausted", "Your about to pass out. You struggle to walk and even do daily tasks such as eating."
    elif val < 65: return "Tired", "You need sleep. You faze out alot and struggle to do basic tasks like carrying objects."
    elif val < 75: return "Weary", "You lack energy and need a nap. May have slight struggles with daily tasks and will likley drift of time to time."
    return "Normal", "No Penalty"

def update_ui():
    food_bar['value'] = food
    energy_bar['value'] = energy
    fs, fp = get_food_status(food)
    es, ep = get_energy_status(energy)
    food_status_var.set(f"Hunger Status: {fs} ({fp})")
    energy_status_var.set(f"Stamina Status: {es} ({ep})")

    for bar in custom_bars.values():
        bar['widget']['value'] = bar['value']
        bar['label'].set(f"{bar['name']} - {bar['value']}%")

def decay():
    global food, energy
    if not pause_all:  # ← Add this line to respect the pause state
        if food > 0:
            food = clamp(food - 1)
        if energy > 0:
            energy = clamp(energy - 1)
        update_ui()

    root.after(60000, decay)

def decay_custom_bars():
    global pause_all
    if not pause_all:
        bars_to_delete = []
        for name, bar in list(custom_bars.items()):
            bar['tick'] += 1  # 1 second per call
            if bar['tick'] >= bar['interval']:
                bar['tick'] = 0
                if bar['value'] > 0:
                    bar['value'] = clamp(bar['value'] - 10)
                    if bar['value'] <= 0:
                        bar['widget'].master.destroy()  # Remove from UI
                        bars_to_delete.append(name)

        for name in bars_to_delete:
            del custom_bars[name]

    update_ui()
    root.after(1000, decay_custom_bars)  # now runs every second

# --- Injury Management ---
def open_injury_chooser():
    popup = tk.Toplevel(root)
    popup.title("Add Injury")
    for limb in limbs:
        tk.Button(popup, text=limb, command=lambda l=limb: create_injury_button(l, popup)).pack(pady=2)

def create_injury_button(limb, window=None):
    if limb not in injuries:
        injuries[limb] = []

    if limb not in injury_buttons:
        btn = tk.Button(root, text=limb, width=30, command=lambda: show_injuries(limb))
        btn.pack(pady=2)
        injury_buttons[limb] = btn

    if window:
        window.destroy()

def show_injuries(limb):
    popup = tk.Toplevel(root)
    popup.title(f"Injuries - {limb}")

    tk.Label(popup, text=f"Injuries on {limb}:", font=('Arial', 12, 'bold')).pack()
    listbox = tk.Listbox(popup, width=40, height=10)
    listbox.pack()

    for injury in injuries[limb]:
        listbox.insert(tk.END, injury)

    def add_injury():
        severity = simpledialog.askstring("Severity", "Enter severity (Minor, Serious, Major):")
        if not severity or severity.title() not in injury_severity:
            messagebox.showerror("Error", "Invalid severity.")
            return
        severity = severity.title()
        injury = simpledialog.askstring("Injury", f"Choose injury type:\n{', '.join(injury_severity[severity])}")
        if injury:
            full = f"{severity} {injury}"
            injuries[limb].append(full)
            listbox.insert(tk.END, full)

    def delete_injury():
        selected = listbox.curselection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select an injury to delete.")
            return
        index = selected[0]
        confirm = messagebox.askyesno("Confirm", f"Delete injury '{listbox.get(index)}'?")
        if confirm:
            del injuries[limb][index]
            listbox.delete(index)

    btn_frame = tk.Frame(popup)
    btn_frame.pack(pady=5)

    tk.Button(btn_frame, text="➕ Add Injury", command=add_injury).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="❌ Delete Selected", command=delete_injury).pack(side=tk.LEFT, padx=5)

# --- Inventory ---
inventory_buttons = {}

def open_inventory_chooser():
    popup = tk.Toplevel(root)
    popup.title("Select Inventory")

    container_options = [
        "Left Lower Pocket", "Right Lower Pocket", "Left Upper Pocket", "Right Lower Pocket", "Belt",
        "Small Backpack", "Medium Backpack", "Large Backpack", "Small Sack", "Large Sack",
        "Small Pouch", "Medium Pouch", "Duffel Bag", "Toolbox", "Chest", "Lootcrate",
        "Small Box", "Med Box", "Large Box", "Cooler", "Fridge", "Vehicle",
        "Drawer", "Small Container", "Large Container", "Misc"
    ]

    for name in container_options:
        tk.Button(popup, text=name, command=lambda n=name: create_inventory_button(n, popup)).pack()

    # Separator and custom option
    tk.Label(popup, text="").pack()
    tk.Button(popup, text="➕ Add Custom", fg="blue", command=lambda: add_custom_inventory(popup)).pack(pady=5)

def create_inventory_button(name, window=None):
    if name not in inventory:
        inventory[name] = []

    if name not in inventory_buttons:
        btn = tk.Button(root, text=name, width=30, command=lambda: show_inventory(name))
        btn.pack(pady=2)
        inventory_buttons[name] = btn

    if window:
        window.destroy()

def add_custom_inventory(popup):
    name = simpledialog.askstring("Custom Inventory", "Enter name for custom storage:")
    if name:
        create_inventory_button(name.strip(), popup)

def show_inventory(name):
    popup = tk.Toplevel(root)
    popup.title(name)

    tk.Label(popup, text=f"Contents of {name}:", font=('Arial', 12, 'bold')).pack()
    listbox = tk.Listbox(popup, width=40, height=10)
    listbox.pack()

    for item in inventory[name]:
        listbox.insert(tk.END, item)

    def add_item():
        item = simpledialog.askstring("Add Item", f"Enter item to add to {name}:")
        if item:
            inventory[name].append(item)
            listbox.insert(tk.END, item)

    def delete_item():
        selected = listbox.curselection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select an item to delete.")
            return
        index = selected[0]
        confirm = messagebox.askyesno("Confirm", f"Delete '{listbox.get(index)}'?")
        if confirm:
            del inventory[name][index]
            listbox.delete(index)

    btn_frame = tk.Frame(popup)
    btn_frame.pack(pady=5)

    tk.Button(btn_frame, text="Add Item", command=add_item).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Delete Selected", command=delete_item).pack(side=tk.LEFT, padx=5)

def open_structure_chooser():
    popup = tk.Toplevel(root)
    popup.title("Select Structure")

    # Show structure buttons
    for name in structures.keys():
        tk.Button(popup, text=name, command=lambda n=name: show_structure_inventory(n)).pack()

    tk.Label(popup, text="").pack()

    # Add new structure button
    tk.Button(popup, text="➕ Add New Structure", fg="blue", command=lambda: add_structure(popup)).pack(pady=5)
    
    # Add delete structure button
    tk.Button(popup, text="🗑️ Delete Structure", fg="red", command=lambda: open_delete_structure_popup(popup)).pack(pady=5)

def open_delete_structure_popup(parent_popup=None):
    popup = tk.Toplevel(root)
    popup.title("Delete Structure")

    tk.Label(popup, text="Select structure to delete:", font=('Arial', 12, 'bold')).pack(pady=5)

    listbox = tk.Listbox(popup, width=40, height=10)
    listbox.pack()

    for name in structures.keys():
        listbox.insert(tk.END, name)

    def delete_selected():
        selected = listbox.curselection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select a structure to delete.")
            return
        index = selected[0]
        name = listbox.get(index)
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete structure '{name}'?")
        if confirm:
            # Remove structure data
            del structures[name]

            # Destroy button and remove reference
            if name in structure_buttons:
                structure_buttons[name].destroy()
                del structure_buttons[name]

            # Close delete popup and the main structures chooser popup if open
            popup.destroy()
            if parent_popup:
                parent_popup.destroy()

            status_message.set(f"Structure '{name}' deleted.")
    
    tk.Button(popup, text="Delete Selected", fg="red", command=delete_selected).pack(pady=5)

def add_structure(popup=None):
    name = simpledialog.askstring("New Structure", "Enter structure name:")
    if name:
        name = name.strip()
        if name in structures:
            messagebox.showerror("Error", f"Structure '{name}' already exists.")
            return
        structures[name] = []
        create_structure_button(name)
    if popup: popup.destroy()

def create_structure_button(name):
    if name in structure_buttons:
        return
    btn = tk.Button(root, text=f"🏠 {name}", width=30, command=lambda: show_structure_inventory(name))
    btn.pack(pady=2)
    structure_buttons[name] = btn

def show_structure_inventory(name):
    popup = tk.Toplevel(root)
    popup.title(name)

    tk.Label(popup, text=f"{name} Contents:", font=('Arial', 12, 'bold')).pack()
    listbox = tk.Listbox(popup, width=40, height=10)
    listbox.pack()

    for item in structures[name]:
        listbox.insert(tk.END, item)

    def add_item():
        item = simpledialog.askstring("Add Item", f"Enter item to add to {name}:")
        if item:
            structures[name].append(item)
            listbox.insert(tk.END, item)

    def delete_item():
        selected = listbox.curselection()
        if not selected:
            messagebox.showinfo("No Selection", "Select an item to delete.")
            return
        index = selected[0]
        confirm = messagebox.askyesno("Confirm", f"Delete '{listbox.get(index)}'?")
        if confirm:
            del structures[name][index]
            listbox.delete(index)

    frame = tk.Frame(popup)
    frame.pack(pady=5)
    tk.Button(frame, text="Add Item", command=add_item).pack(side=tk.LEFT, padx=5)
    tk.Button(frame, text="Delete Selected", command=delete_item).pack(side=tk.LEFT, padx=5)

# --- Save/Load ---
def save_game():
    with open(save_file, 'w') as f:
        json.dump({
            'food': food,
            'energy': energy,
            'inventory': inventory,
            'injuries': injuries,
            'balance': balance,
            'structures': structures,
            'custom_bars': {
                k: {'value': v['value'], 'interval': v['interval']}
                for k, v in custom_bars.items() if v['value'] > 0
            }
        }, f)
    status_message.set("Game Saved.")

def load_game():
    global food, energy, inventory, injuries, balance, structures
    if os.path.exists(save_file):
        with open(save_file, 'r') as f:
            data = json.load(f)
            food = clamp(data.get('food', 100))
            energy = clamp(data.get('energy', 100))
            inventory = data.get('inventory', {})
            injuries = data.get('injuries', {})
            balance = str(data.get('balance', "0"))
            structures = data.get('structures', {})

            for btn in structure_buttons.values():
                btn.destroy()
            structure_buttons.clear()
            for name in structures:
                create_structure_button(name)

            # Reset buttons before recreating
            for btn in inventory_buttons.values():
                btn.destroy()
            inventory_buttons.clear()

            for btn in injury_buttons.values():
                btn.destroy()
            injury_buttons.clear()

            # Clear custom bars from UI
            for bar in custom_bars.values():
                bar['widget'].destroy()
            custom_bars.clear()

            # Create buttons from loaded data
            for name in inventory:
                create_inventory_button(name)
            for limb in injuries:
                create_injury_button(limb)

            # Load custom bars (value + interval)
            bars_data = data.get('custom_bars', {})
            for name, bar_data in bars_data.items():
                val = clamp(bar_data.get('value', 100))
                interval = bar_data.get('interval', 10)
                create_custom_bar(name=name, rate=interval, value=val)

            update_ui()
            update_balance_display()
            status_message.set("Game Loaded.")

def delete_save():
    global food, energy, inventory, injuries, balance

    if os.path.exists(save_file):
        os.remove(save_file)

    food = 100
    energy = 100
    balance = 0.0
    inventory.clear()
    injuries.clear()

    # Destroy custom bar widgets
    for bar in custom_bars.values():
        bar['widget'].master.destroy()  # this removes the entire bar_frame
    custom_bars.clear()

    for btn in inventory_buttons.values():
        btn.destroy()
    for btn in injury_buttons.values():
        btn.destroy()
    inventory_buttons.clear()
    injury_buttons.clear()

    for btn in structure_buttons.values():
        btn.destroy()
    structures.clear()
    structure_buttons.clear()

    update_balance_display()
    status_message.set("Save Deleted. All stats reset.")

# --- Food, Drink, Rest ---
def open_food_popup():
    popup = tk.Toplevel(root)
    popup.title("Choose Food")
    tk.Label(popup, text="Low Quality (+15%)", font=('Arial', 10, 'bold')).pack()
    for name in ["Can Of Worms", "Food Paste", "Porridge", "Soup", "Bird Meat", "Insect Meat", "Candy"]:
        tk.Button(popup, text=name, command=lambda n=name: eat(15, popup)).pack()

    tk.Label(popup, text="Medium Quality (+25%)", font=('Arial', 10, 'bold')).pack()
    for name in ["Fish", "Civilian MRE", "Pizza Slice", "Canned Food", "Vegetables", "Animal Meat", "Fries", "Nutrient Bar"]:
        tk.Button(popup, text=name, command=lambda n=name: eat(25, popup)).pack()

    tk.Label(popup, text="High Quality (+50%)", font=('Arial', 10, 'bold')).pack()
    for name in ["Rat Burger", "Shark Soup", "Mac And Cheese", "Military MRE", "Whole Pizza", "Burger", "Kebab"]:
        tk.Button(popup, text=name, command=lambda n=name: eat(50, popup)).pack()

def open_drink_popup():
    popup = tk.Toplevel(root)
    popup.title("Choose Drink")

    # Low Quality Drinks (+10%)
    tk.Label(popup, text="Low Quality (+10%)", font=('Arial', 10, 'bold')).pack()
    for name in ["Dirty Water", "Rainwater", "Stale Juice", "Broth", "Saltwater"]:
        tk.Button(popup, text=name, command=lambda a=10: rest(a, popup)).pack()

    # Medium Quality Drinks (+25%)
    tk.Label(popup, text="Medium Quality (+25%)", font=('Arial', 10, 'bold')).pack()
    for name in ["Water", "Boiled Water", "Canned Drink", "Tea", "Coffee"]:
        tk.Button(popup, text=name, command=lambda a=25: rest(a, popup)).pack()

    # High Quality Drinks (+50%)
    tk.Label(popup, text="High Quality (+50%)", font=('Arial', 10, 'bold')).pack()
    for name in ["Second Sun Soda", "Energy Drink", "Cola", "Lemonade"]:
        tk.Button(popup, text=name, command=lambda a=50: rest(a, popup)).pack()

def open_rest_popup():
    popup = tk.Toplevel(root)
    popup.title("Rest Options")
    for name, amount in [("Nap (15%)", 15), ("Rest (40%)", 40), ("Sleep (80%)", 80), ("Deep Sleep (100%)", 100)]:
        tk.Button(popup, text=name, command=lambda a=amount: rest(a if a < 100 else 100, popup)).pack(pady=2)

# --- Stat Actions ---
def eat(amount, window=None):
    global food
    food = clamp(food + amount)
    update_ui()
    if window: window.destroy()

def rest(amount, window=None):
    global energy
    energy = clamp(energy + amount)
    update_ui()
    if window: window.destroy()

def open_mod_menu():
    popup = tk.Toplevel(root)
    popup.title("Utility Menu")
    popup.geometry("250x400")  # Increased height to fit new buttons

    tk.Button(popup, text="Set Stamina", command=lambda: set_stat("energy")).pack(pady=5)
    tk.Button(popup, text="Set Hunger", command=lambda: set_stat("food")).pack(pady=5)
    tk.Button(popup, text="Reset Stamina (100)", command=lambda: reset_stat("energy")).pack(pady=5)
    tk.Button(popup, text="Reset Hunger (100)", command=lambda: reset_stat("food")).pack(pady=5)
    tk.Button(popup, text="Delete All Inventories", command=clear_inventory).pack(pady=5)
    tk.Button(popup, text="☠️ Dead", fg="red", command=death_screen).pack(pady=10)

    # --- NEW BUTTONS ---
    tk.Button(popup, text="➕ Create Bar", command=create_custom_bar).pack(pady=10)
    tk.Button(popup, text="⏸️ Pause All Bars", command=toggle_pause_bars).pack(pady=5)

def set_stat(stat):
    global energy, food
    val = simpledialog.askinteger("Set Value", f"Enter new {stat} value (0-100):")
    if val is not None:
        if stat == "energy": energy = clamp(val)
        elif stat == "food": food = clamp(val)
        update_ui()

def reset_stat(stat):
    global energy, food
    if stat == "energy": energy = 100
    elif stat == "food": food = 100
    update_ui()

def clear_inventory():
    global inventory
    for btn in inventory_buttons.values():
        btn.destroy()
    inventory.clear()
    inventory_buttons.clear()
    status_message.set("Inventory Cleared.")

def death_screen():
    root.destroy()
    death = tk.Tk()
    death.title("Death")
    death.geometry("400x200")
    tk.Label(death, text="☠️ Your Character Has Died ☠️", font=('Arial', 16, 'bold'), fg="red").pack(pady=40)
    tk.Label(death, text="Your journey is over.", font=('Arial', 12)).pack(pady=5)
    death.mainloop()

def set_balance():
    global balance
    val = simpledialog.askstring("Set Balance", "Enter balance (e.g. 6.1 = 6ND 1NC):")
    if val:
        try:
            # Store as string so we can keep trailing zeroes
            balance = val.strip()
            update_balance_display()
        except ValueError:
            messagebox.showerror("Error", "Invalid input.")

def update_balance_display():
    try:
        nd_part, _, nc_part = balance.partition(".")
        nd = int(nd_part) if nd_part else 0
        nc = int(nc_part) if nc_part else 0

        text = f"Balance: {nd}ND"
        if nc > 0:
            text += f" {nc}NC"
        balance_var.set(text)
    except Exception:
        balance_var.set("Balance: INVALID")

# --- Custom Bars Functions (NEW) ---

def create_custom_bar(name=None, rate=None, value=100):
    """
    If called with no args (from UI button), ask user for inputs.
    If called with args (from load_game), create silently.
    """
    if name is None or rate is None:
        try:
            rate = simpledialog.askinteger("Create Bar", "How many seconds should it take to decay 10%?", minvalue=1)
            if rate is None: return

            name = simpledialog.askstring("Bar Name", "Enter name for the new bar:")
            if not name: return
            name = name.strip()

            if name in custom_bars:
                messagebox.showerror("Error", f"A bar named '{name}' already exists.")
                return
        except Exception as e:
            messagebox.showerror("Error", str(e))
            return

    if name in custom_bars:
        bar = custom_bars[name]
        bar['interval'] = rate
        bar['value'] = value
        bar['tick'] = 0
        update_ui()
        return

    label_var = tk.StringVar()
    bar_frame = tk.Frame(root)
    bar_frame.pack()

    tk.Label(bar_frame, textvariable=label_var).pack()
    bar_widget = ttk.Progressbar(bar_frame, length=300, maximum=100)
    bar_widget.pack(pady=2)

    custom_bars[name] = {
        'name': name,
        'value': value,
        'interval': rate,  # How many seconds per 10% drop
        'tick': 0,         # Internal tick counter
        'label': label_var,
        'widget': bar_widget
    }
    update_ui()

def update_bars():
    if pause_all:
        root.after(1000, update_bars)  # Skip updating, but keep loop going
        return

    for bar in custom_bars.values():
        bar['tick'] += 1
        if bar['tick'] >= bar['interval']:
            bar['value'] = max(0, bar['value'] - 10)
            bar['tick'] = 0
    update_ui()
    root.after(1000, update_bars)

def toggle_pause_bars():
    global pause_all
    pause_all = not pause_all
    status_message.set("Bars Paused" if pause_all else "Bars Resumed")

# --- UI Setup ---
root = tk.Tk()
root.title("Survival Tracker")
root.geometry("450x780")

food_status_var = tk.StringVar()
energy_status_var = tk.StringVar()
status_message = tk.StringVar()

tk.Label(root, text="Hunger").pack()
food_bar = ttk.Progressbar(root, length=300, maximum=100)
food_bar.pack(pady=5)

tk.Label(root, text="Stamina").pack()
energy_bar = ttk.Progressbar(root, length=300, maximum=100)
energy_bar.pack(pady=5)

tk.Label(root, textvariable=food_status_var, font=('Arial', 12)).pack(pady=5)
tk.Label(root, textvariable=energy_status_var, font=('Arial', 12)).pack(pady=5)
balance_var = tk.StringVar(value="Balance: 0ND")

tk.Button(root, text="🍽️ Eat", command=open_food_popup, width=30).pack(pady=2)
tk.Button(root, text="🥤 Drink", command=open_drink_popup, width=30).pack(pady=2)
tk.Button(root, text="🛌 Rest", command=open_rest_popup, width=30).pack(pady=2)
balance_label = tk.Label(root, textvariable=balance_var, anchor='e', font=('Arial', 10, 'bold'))
balance_label.place(relx=0.98, rely=0.975, anchor='se')
balance_note = tk.Label(root, text="Decimal = NC (e.g. 6.1 → 6ND 1NC)", font=('Arial', 8), fg="gray")
balance_note.place(relx=0.98, rely=0.94, anchor='se')
tk.Button(root, text="💰 Balance", command=set_balance, width=30).pack(pady=2)

tk.Button(root, text="➕ Add Inventory", command=open_inventory_chooser, width=30).pack(pady=10)
tk.Button(root, text="🦴 Add Injury", command=open_injury_chooser, width=30).pack(pady=2)
tk.Button(root, text="⚙️ Utility Menu", command=open_mod_menu, width=30).pack(pady=10)
tk.Button(root, text="🏗️ Structures", command=open_structure_chooser, width=30).pack(pady=2)

tk.Button(root, text="💾 Save Game", command=save_game).pack(pady=5)
tk.Button(root, text="📂 Load Game", command=load_game).pack(pady=5)
tk.Button(root, text="🗑️ Delete Save", command=delete_save).pack(pady=5)

tk.Label(root, textvariable=status_message, fg="green").pack(pady=5)

load_game()
update_ui()

root.after(60000, decay)
root.after(10000, decay_custom_bars)  # Start the custom bars decay loop

root.mainloop()