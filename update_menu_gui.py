#!/usr/bin/env python3
"""
Bowl Out Rice and Noodles — Menu Manager GUI (update_menu_gui.py)
Manages js/menu-data.js with:
  - Add, modify, delete, and reorder menu items
  - Category manager (add, rename, delete categories)
  - Unstructured text menu parser & importer
  - Change preview diff before saving
  - Automatic daily backup to js/menu-data_mmddyy.bak
"""

import copy
import datetime
import json
import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

NAVY_BG = "#071b2e"
NAVY_SURFACE = "#0c263f"
NAVY_CARD = "#102f4d"
BORDER_BLUE = "#1c446b"
CREAM = "#fdf0d5"
CREAM_MUTED = "#c8d2dc"
ORANGE = "#f36512"
ORANGE_HOVER = "#d85307"
AMBER = "#f5a012"
CYAN = "#32d9e8"
WHITE = "#ffffff"
DARK_TEXT = "#0f172a"

DEFAULT_CATEGORIES = ["appetizers", "ramens", "rice bowls", "kids meals"]

DEFAULT_MENU_DATA = [
    {"name": "Karaage", "price": "$10", "category": "appetizers", "description": "Marinated fried chicken, spicy hoisin, sriracha aioli, cucumber, lime and togarashi."},
    {"name": "Crab Rangoons (5pc)", "price": "$10", "category": "appetizers", "description": "Cream cheese, imitation crab, green onions. Served with sweet chili sauce."},
    {"name": "Pork Eggroll", "price": "$3", "category": "appetizers", "description": "Served with sweet chili sauce."},
    {"name": "Vegetable Spring Roll (2pc)", "price": "$3", "category": "appetizers", "description": "Served with sweet chili sauce."},
    {"name": "Pork Dumplings (5pc)", "price": "$8", "category": "appetizers", "description": "Served with Soy Vinaigrette."},
    {"name": "Edamame Salad", "price": "$5", "category": "appetizers", "description": ""},
    {"name": "Seaweed Salad", "price": "$5", "category": "appetizers", "description": ""},
    {"name": "*Pork Belly Miso Ramen", "price": "$16", "category": "ramens", "description": "Pork miso broth, menma, shiitake mushroom, soft-boiled egg, and green onion."},
    {"name": "*Lemongrass Chicken Shoyu Ramen", "price": "$15", "category": "ramens", "description": "Savory chicken shoyu broth, shiitake mushroom, soft-boiled egg, fried onion and green onion."},
    {"name": "*Pork & Shrimp Wonton Shoyu Ramen", "price": "$16", "category": "ramens", "description": "Savory chicken shoyu broth, wontons, shiitake mushroom, soft-boiled egg, and green onion."},
    {"name": "*Pork Belly", "price": "$16", "category": "rice bowls", "description": "Pork belly, cucumber, shiitake mushroom, avocado, soft-boiled egg, green onions, sesame seeds and spicy hoisin."},
    {"name": "Chicken Karaage", "price": "$14", "category": "rice bowls", "description": "Marinated fried chicken, seaweed, carrots, green onion, spicy hoisin and garlic sriracha aioli."},
    {"name": "General Tso’s Chicken", "price": "$14", "category": "rice bowls", "description": "Flash fried chicken thigh, broccoli, green onion and sesame seeds."},
    {"name": "Teriyaki Chicken", "price": "$14", "category": "rice bowls", "description": "Broccoli, carrots, mushrooms, sesame seeds and green onion."},
    {"name": "Teriyaki Salmon", "price": "$18", "category": "rice bowls", "description": "Broccoli, carrots, mushrooms, sesame seeds and green onion."},
    {"name": "Poke", "price": "$18", "category": "rice bowls", "description": "Choice of tuna or salmon, edamame pods, seaweed salad, avocado, cucumber and shredded carrots with spicy mayo."},
    {"name": "General Chicken", "price": "$9", "category": "kids meals", "description": "Flash fried chicken thigh, broccoli, green onion and sesame seeds."},
    {"name": "*Chicken Shoyu Ramen", "price": "$9", "category": "kids meals", "description": "Savory chicken shoyu broth, shiitake mushroom, soft-boiled egg, fried onion and green onion."},
    {"name": "Karaage w/ Rice", "price": "$9", "category": "kids meals", "description": "Marinated fried chicken, seaweed, carrots, green onion, spicy hoisin and garlic sriracha aioli."},
]


def normalize_price(raw_price: str) -> str:
    val = (raw_price or "").strip()
    if not val:
        return ""
    if re.match(r"^\d+(\.\d{1,2})?$", val):
        return f"${val}"
    return val


def normalize_category(raw_cat: str) -> str:
    return re.sub(r"\s+", " ", (raw_cat or "").strip().lower())


def parse_menu_js_content(content: str) -> list:
    cleaned = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    cleaned = re.sub(r"//.*", "", cleaned)
    start, end = cleaned.find("["), cleaned.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise ValueError("Could not find a JSON array [...] in menu-data.js.")
    array_text = re.sub(r",\s*([\]}])", r"\1", cleaned[start : end + 1])
    data = json.loads(array_text)
    if not isinstance(data, list):
        raise ValueError("Parsed menu data is not a list.")
    return [
        {
            "name": str(entry.get("name", "")).strip(),
            "price": normalize_price(str(entry.get("price", ""))),
            "category": normalize_category(str(entry.get("category", "appetizers"))),
            "description": str(entry.get("description", "")).strip(),
        }
        for entry in data
        if isinstance(entry, dict)
    ]


def format_menu_js_content(items: list) -> str:
    json_payload = json.dumps(items, indent=2, ensure_ascii=False)
    return (
        "// Bowl Out Rice and Noodles — Menu Data\n"
        "// Updated via update_menu_gui.py\n"
        f"window.menuData = {json_payload};\n"
    )


def parse_unstructured_menu(raw_text: str, known_categories=None) -> list:
    known = {normalize_category(c) for c in (known_categories or DEFAULT_CATEGORIES)}
    known.update({"appetizers", "ramens", "ramen", "rice bowls", "kids meals", "kids", "sides", "drinks", "beverages"})

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    parsed_items = []
    current_category = "appetizers"
    inherited_category_price = ""
    current_item = None
    price_line_re = re.compile(r"^(.*?)\s*(?:[-–—:]\s*)?(\$\d+(?:\.\d{1,2})?)\s*$")

    def flush_item():
        nonlocal current_item
        if current_item and current_item["name"]:
            current_item["description"] = " ".join(current_item["description_parts"]).strip()
            del current_item["description_parts"]
            parsed_items.append(current_item)
        current_item = None

    for line in lines:
        match = price_line_re.match(line)
        if match:
            title_part = match.group(1).strip().rstrip("-–—:").strip()
            price_part = normalize_price(match.group(2))
            title_lower = normalize_category(title_part)
            if title_lower in known or title_lower.endswith("meals"):
                flush_item()
                current_category = "kids meals" if title_lower == "kids" else title_lower
                inherited_category_price = price_part
                continue
            flush_item()
            current_item = {"name": title_part, "price": price_part, "category": current_category, "description_parts": []}
            continue

        line_lower = normalize_category(line.rstrip(":"))
        if line_lower in known:
            flush_item()
            current_category = "ramens" if line_lower == "ramen" else ("kids meals" if line_lower == "kids" else line_lower)
            inherited_category_price = ""
            continue

        if inherited_category_price:
            if len(line) <= 45 and not line.endswith(".") and (line.startswith("*") or line[0].isupper()) and "," not in line:
                flush_item()
                current_item = {"name": line, "price": inherited_category_price, "category": current_category, "description_parts": []}
                continue

        if current_item is not None:
            current_item["description_parts"].append(line)

    flush_item()
    return parsed_items


def compute_menu_diff(original_items: list, updated_items: list) -> dict:
    orig_by_key = {(i["category"], i["name"]): i for i in original_items}
    new_by_key = {(i["category"], i["name"]): i for i in updated_items}
    added, removed, modified = [], [], []

    for key, new_item in new_by_key.items():
        if key not in orig_by_key:
            added.append(new_item)
        else:
            old_item = orig_by_key[key]
            changes = []
            if old_item["price"] != new_item["price"]:
                changes.append(f"Price: {old_item['price']} -> {new_item['price']}")
            if old_item["description"] != new_item["description"]:
                changes.append(f"Description updated:\n      Old: {old_item['description'] or '(none)'}\n      New: {new_item['description'] or '(none)'}")
            if changes:
                modified.append((new_item, changes))

    for key, old_item in orig_by_key.items():
        if key not in new_by_key:
            removed.append(old_item)

    orig_order = [(i["category"], i["name"]) for i in original_items]
    new_order = [(i["category"], i["name"]) for i in updated_items]
    order_changed = not added and not removed and not modified and orig_order != new_order
    return {"added": added, "removed": removed, "modified": modified, "order_changed": order_changed}


class BowlOutMenuGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Bowl Out Rice & Noodles — Menu Manager")
        self.root.geometry("1180x760")
        self.root.minsize(980, 640)
        self.root.configure(bg=NAVY_BG)

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.js_dir = os.path.join(self.base_dir, "js")
        self.menu_file_path = os.path.join(self.js_dir, "menu-data.js")

        self.original_items = []
        self.items = []
        self.categories = list(DEFAULT_CATEGORIES)
        self.selected_index = None

        self._configure_styles()
        self._load_initial_data()
        self._build_ui()
        self._refresh_category_widgets()
        self._refresh_treeview()

    def _configure_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=NAVY_BG)
        style.configure("Surface.TFrame", background=NAVY_SURFACE)
        style.configure("TLabel", background=NAVY_BG, foreground=CREAM, font=("Segoe UI", 10))
        style.configure("Surface.TLabel", background=NAVY_SURFACE, foreground=CREAM, font=("Segoe UI", 10))
        style.configure("Treeview", background=WHITE, foreground=DARK_TEXT, fieldbackground=WHITE, rowheight=28, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=NAVY_CARD, foreground=CREAM, font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", ORANGE)], foreground=[("selected", WHITE)])
        style.configure("TNotebook", background=NAVY_BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=NAVY_SURFACE, foreground=CREAM, padding=(14, 7), font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", ORANGE)], foreground=[("selected", WHITE)])

    def _load_initial_data(self):
        os.makedirs(self.js_dir, exist_ok=True)
        if os.path.exists(self.menu_file_path):
            try:
                with open(self.menu_file_path, "r", encoding="utf-8") as f:
                    self.items = parse_menu_js_content(f.read())
                self.original_items = copy.deepcopy(self.items)
            except Exception as exc:
                messagebox.showerror("Menu File Parse Error", f"Could not parse existing js/menu-data.js:\n{exc}\n\nLoaded default Bowl Out menu in memory.")
                self.items = copy.deepcopy(DEFAULT_MENU_DATA)
                self.original_items = []
        else:
            self.items = copy.deepcopy(DEFAULT_MENU_DATA)
            self.original_items = []
        self._sync_categories_from_items()

    def _sync_categories_from_items(self):
        seen = list(DEFAULT_CATEGORIES)
        for item in self.items:
            cat = normalize_category(item.get("category", ""))
            if cat and cat not in seen:
                seen.append(cat)
        self.categories = seen

    def _make_button(self, parent, text, command, bg=ORANGE, fg=WHITE, bold=False):
        font_spec = ("Segoe UI", 9, "bold") if bold else ("Segoe UI", 9)
        return tk.Button(parent, text=text, command=command, bg=bg, fg=fg, activebackground=ORANGE_HOVER if bg == ORANGE else BORDER_BLUE, activeforeground=WHITE, relief=tk.FLAT, padx=12, pady=6, cursor="hand2", font=font_spec)

    def _build_ui(self):
        header = tk.Frame(self.root, bg=NAVY_SURFACE, bd=0, highlightthickness=1, highlightbackground=BORDER_BLUE)
        header.pack(fill=tk.X, side=tk.TOP)

        title_wrap = tk.Frame(header, bg=NAVY_SURFACE)
        title_wrap.pack(side=tk.LEFT, padx=18, pady=12)
        tk.Label(title_wrap, text="BOWL OUT RICE & NOODLES — MENU MANAGER", bg=NAVY_SURFACE, fg=CREAM, font=("Segoe UI", 15, "bold")).pack(anchor="w")
        self.path_label = tk.Label(title_wrap, text=f"Target File: {self.menu_file_path}", bg=NAVY_SURFACE, fg=CYAN, font=("Segoe UI", 9))
        self.path_label.pack(anchor="w", pady=(2, 0))

        btn_wrap = tk.Frame(header, bg=NAVY_SURFACE)
        btn_wrap.pack(side=tk.RIGHT, padx=18, pady=12)
        self._make_button(btn_wrap, "Reload File", self._reload_from_disk, bg=NAVY_CARD, fg=CREAM).pack(side=tk.LEFT, padx=5)
        self._make_button(btn_wrap, "Manage Categories", self._open_category_manager, bg=NAVY_CARD, fg=AMBER).pack(side=tk.LEFT, padx=5)
        self._make_button(btn_wrap, "Preview & Save Changes", self._open_preview_and_save, bg=ORANGE, fg=WHITE, bold=True).pack(side=tk.LEFT, padx=(8, 0))

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=16, pady=(12, 6))
        self.editor_tab = ttk.Frame(self.notebook)
        self.import_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.editor_tab, text="  Menu Editor (Add / Edit / Delete)  ")
        self.notebook.add(self.import_tab, text="  Import / Parse Text Menu  ")

        self._build_editor_tab()
        self._build_import_tab()

        self.status_var = tk.StringVar(value=f"Loaded {len(self.items)} menu items.")
        tk.Label(self.root, textvariable=self.status_var, bg=NAVY_SURFACE, fg=CREAM_MUTED, anchor="w", padx=16, pady=6, font=("Segoe UI", 9)).pack(fill=tk.X, side=tk.BOTTOM)

    def _build_editor_tab(self):
        container = tk.Frame(self.editor_tab, bg=NAVY_BG)
        container.pack(fill=tk.BOTH, expand=True, pady=8)

        left_pane = tk.Frame(container, bg=NAVY_SURFACE, highlightthickness=1, highlightbackground=BORDER_BLUE)
        left_pane.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        filter_bar = tk.Frame(left_pane, bg=NAVY_SURFACE)
        filter_bar.pack(fill=tk.X, padx=12, pady=10)
        tk.Label(filter_bar, text="Filter Category:", bg=NAVY_SURFACE, fg=CREAM, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)

        self.filter_var = tk.StringVar(value="all")
        self.filter_combo = ttk.Combobox(filter_bar, textvariable=self.filter_var, state="readonly", width=18)
        self.filter_combo.pack(side=tk.LEFT, padx=(6, 14))
        self.filter_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_treeview())

        tk.Label(filter_bar, text="Search:", bg=NAVY_SURFACE, fg=CREAM, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._refresh_treeview())
        tk.Entry(filter_bar, textvariable=self.search_var, bg=WHITE, fg=DARK_TEXT, font=("Segoe UI", 10), width=22).pack(side=tk.LEFT, padx=6, fill=tk.X, expand=True)

        tree_wrap = tk.Frame(left_pane, bg=NAVY_SURFACE)
        tree_wrap.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 8))

        self.tree = ttk.Treeview(tree_wrap, columns=("category", "name", "price", "description"), show="headings", selectmode="browse")
        self.tree.heading("category", text="Category")
        self.tree.heading("name", text="Item Name")
        self.tree.heading("price", text="Price")
        self.tree.heading("description", text="Description")
        self.tree.column("category", width=115, minwidth=95, anchor="w")
        self.tree.column("name", width=210, minwidth=150, anchor="w")
        self.tree.column("price", width=75, minwidth=65, anchor="center")
        self.tree.column("description", width=310, minwidth=180, anchor="w")

        vsb = ttk.Scrollbar(tree_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        list_ctrl = tk.Frame(left_pane, bg=NAVY_SURFACE)
        list_ctrl.pack(fill=tk.X, padx=12, pady=(0, 10))
        self._make_button(list_ctrl, "Move Up", lambda: self._move_selected(-1), bg=NAVY_CARD, fg=CREAM).pack(side=tk.LEFT, padx=(0, 6))
        self._make_button(list_ctrl, "Move Down", lambda: self._move_selected(1), bg=NAVY_CARD, fg=CREAM).pack(side=tk.LEFT, padx=(0, 6))
        self._make_button(list_ctrl, "Delete Selected", self._delete_selected_item, bg="#b91c1c", fg=WHITE).pack(side=tk.RIGHT)

        right_pane = tk.Frame(container, bg=NAVY_SURFACE, width=360, highlightthickness=1, highlightbackground=BORDER_BLUE)
        right_pane.pack(side=tk.RIGHT, fill=tk.Y)
        right_pane.pack_propagate(False)

        form_inner = tk.Frame(right_pane, bg=NAVY_SURFACE)
        form_inner.pack(fill=tk.BOTH, expand=True, padx=16, pady=14)
        tk.Label(form_inner, text="ITEM DETAILS (ADD OR MODIFY)", bg=NAVY_SURFACE, fg=AMBER, font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 12))

        tk.Label(form_inner, text="Category (select or type new):", bg=NAVY_SURFACE, fg=CREAM, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.form_category_var = tk.StringVar(value=self.categories[0] if self.categories else "appetizers")
        self.form_category_combo = ttk.Combobox(form_inner, textvariable=self.form_category_var, font=("Segoe UI", 10))
        self.form_category_combo.pack(fill=tk.X, pady=(4, 12))

        tk.Label(form_inner, text="Item Name (prefix * for consumer advisory):", bg=NAVY_SURFACE, fg=CREAM, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.form_name_var = tk.StringVar()
        tk.Entry(form_inner, textvariable=self.form_name_var, bg=WHITE, fg=DARK_TEXT, font=("Segoe UI", 10)).pack(fill=tk.X, pady=(4, 12))

        tk.Label(form_inner, text="Price (e.g. $10 or 14.50):", bg=NAVY_SURFACE, fg=CREAM, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.form_price_var = tk.StringVar()
        tk.Entry(form_inner, textvariable=self.form_price_var, bg=WHITE, fg=DARK_TEXT, font=("Segoe UI", 10)).pack(fill=tk.X, pady=(4, 12))

        tk.Label(form_inner, text="Description (leave blank if none):", bg=NAVY_SURFACE, fg=CREAM, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.form_desc_text = tk.Text(form_inner, height=6, bg=WHITE, fg=DARK_TEXT, font=("Segoe UI", 10), wrap=tk.WORD)
        self.form_desc_text.pack(fill=tk.X, pady=(4, 14))

        btn_row1 = tk.Frame(form_inner, bg=NAVY_SURFACE)
        btn_row1.pack(fill=tk.X, pady=(0, 8))
        self._make_button(btn_row1, "Add as New Item", self._add_new_item, bg=ORANGE, fg=WHITE, bold=True).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self._make_button(btn_row1, "Update Selected", self._update_selected_item, bg="#0284c7", fg=WHITE, bold=True).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

        btn_row2 = tk.Frame(form_inner, bg=NAVY_SURFACE)
        btn_row2.pack(fill=tk.X)
        self._make_button(btn_row2, "Clear Form", self._clear_form, bg=NAVY_CARD, fg=CREAM).pack(side=tk.LEFT, fill=tk.X, expand=True)

        tip_text = "Tip: Click any row on the left to load it here for editing, or click 'Preview & Save Changes' at the top to review diffs and create a daily .bak backup."
        tk.Label(form_inner, text=tip_text, bg=NAVY_CARD, fg=CREAM_MUTED, wraplength=310, justify="left", padx=10, pady=10, font=("Segoe UI", 9)).pack(fill=tk.X, side=tk.BOTTOM, pady=(14, 0))

    def _build_import_tab(self):
        wrap = tk.Frame(self.import_tab, bg=NAVY_SURFACE, highlightthickness=1, highlightbackground=BORDER_BLUE)
        wrap.pack(fill=tk.BOTH, expand=True, pady=8)

        top_bar = tk.Frame(wrap, bg=NAVY_SURFACE)
        top_bar.pack(fill=tk.X, padx=16, pady=12)
        tk.Label(top_bar, text="PASTE UNSTRUCTURED MENU TEXT OR LOAD FROM .TXT FILE", bg=NAVY_SURFACE, fg=AMBER, font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT)
        self._make_button(top_bar, "Load .txt File...", self._load_text_file_for_import, bg=NAVY_CARD, fg=CREAM).pack(side=tk.RIGHT)

        help_msg = "Supports category headers (Appetizers, Ramens, Rice Bowls, Kids Meals), category-level prices ('Kids Meals $9'), item prices ('Karaage $10'), and multi-line descriptions."
        tk.Label(wrap, text=help_msg, bg=NAVY_SURFACE, fg=CREAM_MUTED, anchor="w", justify="left", font=("Segoe UI", 9)).pack(fill=tk.X, padx=16, pady=(0, 8))

        self.import_text = tk.Text(wrap, bg=WHITE, fg=DARK_TEXT, font=("Consolas", 10), wrap=tk.WORD)
        self.import_text.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 12))

        action_bar = tk.Frame(wrap, bg=NAVY_SURFACE)
        action_bar.pack(fill=tk.X, padx=16, pady=(0, 14))
        self._make_button(action_bar, "Parse & Merge into Current Menu", lambda: self._run_text_import(replace=False), bg="#0284c7", fg=WHITE, bold=True).pack(side=tk.LEFT, padx=(0, 8))
        self._make_button(action_bar, "Parse & Replace Entire Menu", lambda: self._run_text_import(replace=True), bg=ORANGE, fg=WHITE, bold=True).pack(side=tk.LEFT)
        self._make_button(action_bar, "Clear Text", lambda: self.import_text.delete("1.0", tk.END), bg=NAVY_CARD, fg=CREAM).pack(side=tk.RIGHT)

    def _refresh_category_widgets(self):
        self._sync_categories_from_items()
        filter_values = ["all"] + self.categories
        self.filter_combo["values"] = filter_values
        if self.filter_var.get() not in filter_values:
            self.filter_var.set("all")
        self.form_category_combo["values"] = self.categories

    def _refresh_treeview(self):
        for row_id in self.tree.get_children():
            self.tree.delete(row_id)
        selected_cat = self.filter_var.get().lower()
        query = self.search_var.get().strip().lower()
        shown = 0
        for idx, item in enumerate(self.items):
            if selected_cat != "all" and item["category"].lower() != selected_cat:
                continue
            if query and query not in f"{item['category']} {item['name']} {item['price']} {item['description']}".lower():
                continue
            self.tree.insert("", tk.END, iid=str(idx), values=(item["category"], item["name"], item["price"], item["description"]))
            shown += 1
        self.status_var.set(f"Showing {shown} of {len(self.items)} total menu items.")

    def _on_tree_select(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            return
        idx = int(selection[0])
        if 0 <= idx < len(self.items):
            self.selected_index = idx
            item = self.items[idx]
            self.form_category_var.set(item["category"])
            self.form_name_var.set(item["name"])
            self.form_price_var.set(item["price"])
            self.form_desc_text.delete("1.0", tk.END)
            self.form_desc_text.insert("1.0", item["description"])

    def _clear_form(self):
        self.selected_index = None
        for sel in self.tree.selection():
            self.tree.selection_remove(sel)
        self.form_name_var.set("")
        self.form_price_var.set("")
        self.form_desc_text.delete("1.0", tk.END)

    def _read_form_item(self):
        category = normalize_category(self.form_category_var.get())
        name = self.form_name_var.get().strip()
        price = normalize_price(self.form_price_var.get())
        description = self.form_desc_text.get("1.0", tk.END).strip()
        if not category:
            messagebox.showwarning("Missing Category", "Please select or enter a category.")
            return None
        if not name:
            messagebox.showwarning("Missing Item Name", "Please enter an item name.")
            return None
        if not price:
            messagebox.showwarning("Missing Price", "Please enter a price (e.g. $10).")
            return None
        return {"name": name, "price": price, "category": category, "description": description}

    def _add_new_item(self):
        new_item = self._read_form_item()
        if not new_item:
            return
        self.items.append(new_item)
        self._refresh_category_widgets()
        self._refresh_treeview()
        new_idx = len(self.items) - 1
        if self.tree.exists(str(new_idx)):
            self.tree.selection_set(str(new_idx))
            self.tree.see(str(new_idx))
        self.selected_index = new_idx
        self.status_var.set(f"Added '{new_item['name']}' ({new_item['price']}) to {new_item['category']}. Click 'Preview & Save Changes' to save.")

    def _update_selected_item(self):
        if self.selected_index is None or not (0 <= self.selected_index < len(self.items)):
            messagebox.showinfo("No Item Selected", "Select an item in the table first, or click 'Add as New Item'.")
            return
        updated = self._read_form_item()
        if not updated:
            return
        self.items[self.selected_index] = updated
        self._refresh_category_widgets()
        self._refresh_treeview()
        if self.tree.exists(str(self.selected_index)):
            self.tree.selection_set(str(self.selected_index))
            self.tree.see(str(self.selected_index))
        self.status_var.set(f"Updated '{updated['name']}'. Click 'Preview & Save Changes' to save.")

    def _delete_selected_item(self):
        if self.selected_index is None or not (0 <= self.selected_index < len(self.items)):
            messagebox.showinfo("No Item Selected", "Please select an item in the table to delete.")
            return
        target = self.items[self.selected_index]
        if messagebox.askyesno("Confirm Delete", f"Delete '{target['name']}' from {target['category']}?"):
            del self.items[self.selected_index]
            self._clear_form()
            self._refresh_category_widgets()
            self._refresh_treeview()
            self.status_var.set(f"Deleted '{target['name']}'. Click 'Preview & Save Changes' to save.")

    def _move_selected(self, direction: int):
        if self.selected_index is None:
            return
        new_idx = self.selected_index + direction
        if 0 <= new_idx < len(self.items):
            self.items[self.selected_index], self.items[new_idx] = self.items[new_idx], self.items[self.selected_index]
            self.selected_index = new_idx
            self._refresh_treeview()
            if self.tree.exists(str(new_idx)):
                self.tree.selection_set(str(new_idx))
                self.tree.see(str(new_idx))

    def _open_category_manager(self):
        win = tk.Toplevel(self.root)
        win.title("Manage Categories — Bowl Out")
        win.geometry("460x420")
        win.configure(bg=NAVY_BG)
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="CATEGORY MANAGER", bg=NAVY_BG, fg=AMBER, font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=18, pady=(14, 4))
        tk.Label(win, text="Add, rename, or remove categories across your menu.", bg=NAVY_BG, fg=CREAM_MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=18, pady=(0, 12))

        listbox = tk.Listbox(win, bg=WHITE, fg=DARK_TEXT, font=("Segoe UI", 11), selectmode=tk.SINGLE)
        listbox.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 12))

        def reload_cat_list():
            listbox.delete(0, tk.END)
            for cat in self.categories:
                count = sum(1 for i in self.items if i["category"] == cat)
                listbox.insert(tk.END, f"{cat}  ({count} items)")

        reload_cat_list()

        btn_frame = tk.Frame(win, bg=NAVY_BG)
        btn_frame.pack(fill=tk.X, padx=18, pady=(0, 16))

        def add_cat():
            name = simpledialog.askstring("Add Category", "Enter new category name:", parent=win)
            cat = normalize_category(name or "")
            if not cat:
                return
            if cat in self.categories:
                messagebox.showinfo("Exists", f"Category '{cat}' already exists.", parent=win)
                return
            self.categories.append(cat)
            self.form_category_combo["values"] = self.categories
            self.filter_combo["values"] = ["all"] + self.categories
            reload_cat_list()

        def rename_cat():
            sel = listbox.curselection()
            if not sel:
                return
            old_cat = self.categories[sel[0]]
            new_name = simpledialog.askstring("Rename Category", f"Rename '{old_cat}' to:", initialvalue=old_cat, parent=win)
            new_cat = normalize_category(new_name or "")
            if not new_cat or new_cat == old_cat:
                return
            for item in self.items:
                if item["category"] == old_cat:
                    item["category"] = new_cat
            self.categories[sel[0]] = new_cat
            self._refresh_category_widgets()
            self._refresh_treeview()
            reload_cat_list()

        def delete_cat():
            sel = listbox.curselection()
            if not sel:
                return
            target_cat = self.categories[sel[0]]
            affected = [i for i in self.items if i["category"] == target_cat]
            if affected:
                if not messagebox.askyesno("Delete Category & Items?", f"'{target_cat}' has {len(affected)} item(s). Deleting it will also delete those items. Continue?", parent=win):
                    return
                self.items = [i for i in self.items if i["category"] != target_cat]
            if target_cat in self.categories:
                self.categories.remove(target_cat)
            self._clear_form()
            self._refresh_category_widgets()
            self._refresh_treeview()
            reload_cat_list()

        self._make_button(btn_frame, "Add Category", add_cat, bg=ORANGE, fg=WHITE, bold=True).pack(side=tk.LEFT, padx=(0, 6))
        self._make_button(btn_frame, "Rename", rename_cat, bg="#0284c7", fg=WHITE).pack(side=tk.LEFT, padx=(0, 6))
        self._make_button(btn_frame, "Delete", delete_cat, bg="#b91c1c", fg=WHITE).pack(side=tk.LEFT)
        self._make_button(btn_frame, "Close", win.destroy, bg=NAVY_CARD, fg=CREAM).pack(side=tk.RIGHT)

    def _load_text_file_for_import(self):
        path = filedialog.askopenfilename(title="Select Menu Text File", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if not path:
            return
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            self.import_text.delete("1.0", tk.END)
            self.import_text.insert("1.0", f.read())

    def _run_text_import(self, replace: bool):
        raw = self.import_text.get("1.0", tk.END).strip()
        if not raw:
            messagebox.showwarning("No Text", "Paste your menu text into the box first.")
            return
        parsed = parse_unstructured_menu(raw, self.categories)
        if not parsed:
            messagebox.showerror("No Items Detected", "Could not detect any menu items with prices (e.g., 'Karaage $10'). Check formatting and try again.")
            return
        if replace:
            if not messagebox.askyesno("Confirm Replace", f"Parsed {len(parsed)} items. Replace the entire current menu with these items?"):
                return
            self.items = parsed
        else:
            existing_map = {(i["category"], i["name"].lower()): idx for idx, i in enumerate(self.items)}
            added_count = updated_count = 0
            for p_item in parsed:
                key = (p_item["category"], p_item["name"].lower())
                if key in existing_map:
                    self.items[existing_map[key]] = p_item
                    updated_count += 1
                else:
                    self.items.append(p_item)
                    added_count += 1
            messagebox.showinfo("Import Complete", f"Parsed {len(parsed)} items:\n• Added: {added_count}\n• Updated: {updated_count}")
        self._clear_form()
        self._refresh_category_widgets()
        self._refresh_treeview()
        self.notebook.select(self.editor_tab)
        self.status_var.set("Imported menu items into editor. Click 'Preview & Save Changes' to write to disk.")

    def _open_preview_and_save(self):
        diff = compute_menu_diff(self.original_items, self.items)
        js_preview = format_menu_js_content(self.items)

        win = tk.Toplevel(self.root)
        win.title("Preview Changes Before Saving — Bowl Out")
        win.geometry("760x580")
        win.configure(bg=NAVY_BG)
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="REVIEW CHANGES BEFORE SAVING", bg=NAVY_BG, fg=AMBER, font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=18, pady=(14, 4))
        backup_name = f"menu-data_{datetime.datetime.now().strftime('%m%d%y')}.bak"
        tk.Label(win, text=f"Saving will back up the current file to js/{backup_name} and update js/menu-data.js.", bg=NAVY_BG, fg=CYAN, font=("Segoe UI", 9)).pack(anchor="w", padx=18, pady=(0, 10))

        preview_nb = ttk.Notebook(win)
        preview_nb.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 12))
        diff_frame, code_frame = ttk.Frame(preview_nb), ttk.Frame(preview_nb)
        preview_nb.add(diff_frame, text="  Change Summary  ")
        preview_nb.add(code_frame, text="  Generated js/menu-data.js  ")

        diff_text = tk.Text(diff_frame, bg=WHITE, fg=DARK_TEXT, font=("Consolas", 10), wrap=tk.WORD)
        diff_text.pack(fill=tk.BOTH, expand=True)

        lines = [f"Total items to save: {len(self.items)} (Previously: {len(self.original_items)})", "=" * 64]
        if not (diff["added"] or diff["removed"] or diff["modified"] or diff["order_changed"]):
            lines.append("\nNo content changes detected compared to js/menu-data.js.")
        else:
            if diff["added"]:
                lines.append(f"\n[+] ADDED ITEMS ({len(diff['added'])}):")
                for item in diff["added"]:
                    lines.append(f"  • [{item['category']}] {item['name']} — {item['price']}")
                    if item["description"]:
                        lines.append(f"      {item['description']}")
            if diff["modified"]:
                lines.append(f"\n[~] MODIFIED ITEMS ({len(diff['modified'])}):")
                for item, changes in diff["modified"]:
                    lines.append(f"  • [{item['category']}] {item['name']}")
                    for ch in changes:
                        lines.append(f"      {ch}")
            if diff["removed"]:
                lines.append(f"\n[-] REMOVED ITEMS ({len(diff['removed'])}):")
                for item in diff["removed"]:
                    lines.append(f"  • [{item['category']}] {item['name']} — {item['price']}")
            if diff["order_changed"]:
                lines.append("\n[*] Item display order was updated.")

        diff_text.insert("1.0", "\n".join(lines))
        diff_text.configure(state="disabled")

        code_text = tk.Text(code_frame, bg=WHITE, fg=DARK_TEXT, font=("Consolas", 10), wrap=tk.NONE)
        code_text.pack(fill=tk.BOTH, expand=True)
        code_text.insert("1.0", js_preview)
        code_text.configure(state="disabled")

        btn_bar = tk.Frame(win, bg=NAVY_BG)
        btn_bar.pack(fill=tk.X, padx=18, pady=(0, 14))

        def confirm_save():
            self._save_to_disk(js_preview, backup_name)
            win.destroy()

        self._make_button(btn_bar, "Confirm & Save (Create Backup)", confirm_save, bg=ORANGE, fg=WHITE, bold=True).pack(side=tk.RIGHT, padx=(8, 0))
        self._make_button(btn_bar, "Cancel", win.destroy, bg=NAVY_CARD, fg=CREAM).pack(side=tk.RIGHT)

    def _save_to_disk(self, js_content: str, backup_name: str):
        os.makedirs(self.js_dir, exist_ok=True)
        backup_path = os.path.join(self.js_dir, backup_name)
        try:
            if os.path.exists(self.menu_file_path):
                shutil.copy2(self.menu_file_path, backup_path)
            with open(self.menu_file_path, "w", encoding="utf-8") as f:
                f.write(js_content)
            self.original_items = copy.deepcopy(self.items)
            self.status_var.set(f"Saved js/menu-data.js ({len(self.items)} items) • Backup created: js/{backup_name}")
            messagebox.showinfo("Menu Saved", f"Successfully saved {len(self.items)} items to:\n{self.menu_file_path}\n\nBackup saved to:\n{backup_path}")
        except Exception as exc:
            messagebox.showerror("Save Error", f"Failed to save menu-data.js:\n{exc}")

    def _reload_from_disk(self):
        if not os.path.exists(self.menu_file_path):
            messagebox.showinfo("File Not Found", "js/menu-data.js does not exist on disk yet. Save once to create it.")
            return
        if messagebox.askyesno("Reload from Disk", "Discard any unsaved changes and reload js/menu-data.js?"):
            self._load_initial_data()
            self._clear_form()
            self._refresh_category_widgets()
            self._refresh_treeview()
            self.status_var.set("Reloaded js/menu-data.js from disk.")


def main():
    root = tk.Tk()
    BowlOutMenuGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
