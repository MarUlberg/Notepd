# notepd_final_v5.py — includes layout fixes for scaling
import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox, font

CONFIG_PATH = "config"

ACCENT_COLOR = "#212121"
LIGHT_TEXT = "#CCCCCC"
DARK_BG = "#424242"
BUTTON_BG = "#333333"
BUTTON_ACTIVE = "#555555"

FONTS = [
    "Arial", "Calibri", "Comic Sans", "Courier New", "Garamond",
    "Georgia", "Helvetica", "Roboto", "Segoe UI", "Times New Roman", "Verdana"
]

class Notepad:
    def __init__(self, root):
        self.root = root
        self.load_config()

        self.root.title("Notepad")
        self.root.geometry(self.window_size or "900x650")
        self.root.configure(bg=DARK_BG)

        self.text_font = font.Font(family=self.font_family, size=self.font_size)

        self.find_bar_visible = self.find_bar_state
        self.find_bar = None
        self.find_entry = None
        self.replace_entry = None
        self.match_case = tk.IntVar()
        self.wrap_around = tk.IntVar(value=1)
        self.search_direction = tk.StringVar(value="down")
        self.status_label = None

        self.create_widgets()
        self.create_menu()
        self.bind_shortcuts()

        if self.find_bar_visible:
            self.toggle_find_bar()

        self.update_cursor_position()

        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

    def load_config(self):
        self.font_family = "Consolas"
        self.font_size = 12
        self.window_size = None
        self.find_bar_state = False

        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r") as f:
                    data = json.load(f)
                    self.font_family = data.get("font_family", self.font_family)
                    self.font_size = data.get("font_size", self.font_size)
                    self.window_size = data.get("window_size", self.window_size)
                    self.find_bar_state = data.get("find_bar_visible", False)
            except Exception:
                pass

    def save_config(self):
        data = {
            "font_family": self.font_family,
            "font_size": self.font_size,
            "window_size": self.root.geometry(),
            "find_bar_visible": bool(self.find_bar and self.find_bar.winfo_exists())
        }
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def create_widgets(self):
        self.text_frame = tk.Frame(self.root, bg=DARK_BG)
        self.text_frame.grid(row=0, column=0, sticky="nsew")

        self.text_area = tk.Text(
            self.text_frame, wrap="word", undo=True, font=self.text_font,
            bg=DARK_BG, fg=LIGHT_TEXT, insertbackground=LIGHT_TEXT,
            padx=10, pady=5
        )
        self.text_area.grid(row=0, column=0, sticky="nsew")

        scroll = tk.Scrollbar(self.text_frame, command=self.text_area.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.text_area.configure(yscrollcommand=scroll.set)

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.text_frame.grid_rowconfigure(0, weight=1)
        self.text_frame.grid_columnconfigure(0, weight=1)

        self.text_area.bind("<KeyRelease>", lambda e: self.update_cursor_position())
        self.text_area.bind("<ButtonRelease>", lambda e: self.update_cursor_position())

    def create_menu(self):
        menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_file)
        file_menu.add_command(label="Open...", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_app)
        menu_bar.add_cascade(label="File", menu=file_menu)

        font_menu = tk.Menu(menu_bar, tearoff=0)
        self.font_var = tk.StringVar(value=self.font_family)
        for f in FONTS:
            font_menu.add_radiobutton(label=f, variable=self.font_var, value=f, command=lambda fam=f: self.set_font(fam))
        menu_bar.add_cascade(label="Font", menu=font_menu)

        self.root.config(menu=menu_bar)

    def toggle_find_bar(self):
        if self.find_bar and self.find_bar.winfo_exists():
            self.find_bar.destroy()
            return

        self.find_bar = tk.Frame(self.root, bg=ACCENT_COLOR, bd=0, highlightthickness=0)
        self.find_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

        # column weights: scale entry columns, not buttons/status
        for i in range(6):
            self.find_bar.grid_columnconfigure(i, weight=1 if i in [0, 3] else 0)

        self.find_entry = tk.Entry(self.find_bar, bg=DARK_BG, fg=LIGHT_TEXT, insertbackground=LIGHT_TEXT)
        self.find_entry.grid(row=0, column=0, padx=5, pady=(2, 0), sticky="ew")

        find_btn = tk.Button(self.find_bar, text="Find Next", command=self.do_find,
                             bg=BUTTON_BG, fg=LIGHT_TEXT, activebackground=BUTTON_ACTIVE,
                             relief="flat", width=12, padx=4, pady=2)
        find_btn.grid(row=0, column=1, padx=5, pady=(2, 1), sticky="ew")

        tk.Radiobutton(self.find_bar, text="Up", variable=self.search_direction, value="up",
                       bg=ACCENT_COLOR, fg=LIGHT_TEXT, selectcolor=ACCENT_COLOR).grid(row=1, column=1, sticky="w", padx=5)
        tk.Radiobutton(self.find_bar, text="Down", variable=self.search_direction, value="down",
                       bg=ACCENT_COLOR, fg=LIGHT_TEXT, selectcolor=ACCENT_COLOR).grid(row=1, column=1, sticky="e", padx=5)

        self.replace_entry = tk.Entry(self.find_bar, bg=DARK_BG, fg=LIGHT_TEXT, insertbackground=LIGHT_TEXT)
        self.replace_entry.grid(row=0, column=3, padx=5, pady=(2, 0), sticky="ew")

        tk.Button(self.find_bar, text="Replace", command=self.do_replace,
                  bg=BUTTON_BG, fg=LIGHT_TEXT, activebackground=BUTTON_ACTIVE,
                  relief="flat", width=12, padx=4, pady=2).grid(row=0, column=4, padx=5, pady=(2, 1), sticky="ew")

        tk.Button(self.find_bar, text="Replace All", command=self.do_replace_all,
                  bg=BUTTON_BG, fg=LIGHT_TEXT, activebackground=BUTTON_ACTIVE,
                  relief="flat", width=12, padx=4, pady=2).grid(row=1, column=4, padx=5, pady=(2, 2), sticky="ew")

        tk.Checkbutton(self.find_bar, text="Wrap around", variable=self.wrap_around,
                       bg=ACCENT_COLOR, fg=LIGHT_TEXT, selectcolor=ACCENT_COLOR).grid(row=1, column=0, sticky="w", padx=5)
        tk.Checkbutton(self.find_bar, text="Match case", variable=self.match_case,
                       bg=ACCENT_COLOR, fg=LIGHT_TEXT, selectcolor=ACCENT_COLOR).grid(row=1, column=0, sticky="w", padx=(120, 5))

        self.status_label = tk.Label(self.find_bar, text="", fg=LIGHT_TEXT, bg=ACCENT_COLOR, anchor="e")
        self.status_label.grid(row=1, column=5, padx=10, sticky="e")

        self.update_cursor_position()

    def update_cursor_position(self):
        try:
            index = self.text_area.index("insert")
            line, col = map(int, index.split("."))
            pos = self.text_area.count("1.0", "insert", "chars")[0]
            if self.status_label:
                self.status_label.config(text=f"Ln : {line}   Col : {col+1}   Pos : {pos}")
        except:
            pass

    def do_find(self):
        self.text_area.tag_remove("found", "1.0", tk.END)
        query = self.find_entry.get()
        if not query:
            return

        direction = self.search_direction.get()
        backwards = direction == "up"
        start = self.text_area.index("insert")
        stop = "1.0" if backwards else tk.END

        idx = self.text_area.search(query, start, stopindex=stop,
                                    nocase=not self.match_case.get(), backwards=backwards)

        if idx:
            end = f"{idx}+{len(query)}c"
            self.text_area.tag_add("found", idx, end)
            self.text_area.tag_config("found", background=ACCENT_COLOR)
            self.text_area.mark_set("insert", idx if backwards else end)
            self.text_area.see(idx)
        elif self.wrap_around.get():
            restart = tk.END if backwards else "1.0"
            idx = self.text_area.search(query, restart, stopindex=start,
                                        nocase=not self.match_case.get(), backwards=backwards)
            if idx:
                end = f"{idx}+{len(query)}c"
                self.text_area.tag_add("found", idx, end)
                self.text_area.tag_config("found", background=ACCENT_COLOR)
                self.text_area.mark_set("insert", idx if backwards else end)
                self.text_area.see(idx)

    def do_replace(self):
        if self.text_area.tag_ranges("found"):
            self.text_area.delete("found.first", "found.last")
            self.text_area.insert("found.first", self.replace_entry.get())
        self.do_find()

    def do_replace_all(self):
        query = self.find_entry.get()
        replace = self.replace_entry.get()
        if not query:
            return
        content = self.text_area.get("1.0", tk.END)
        if self.match_case.get():
            new_content = content.replace(query, replace)
        else:
            import re
            new_content = re.sub(re.escape(query), replace, content, flags=re.IGNORECASE)
        self.text_area.delete("1.0", tk.END)
        self.text_area.insert("1.0", new_content)

    def new_file(self):
        self.text_area.delete(1.0, tk.END)

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if path:
            with open(path, "r", encoding="utf-8") as file:
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert(tk.END, file.read())

    def save_file(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as file:
                file.write(self.text_area.get("1.0", tk.END))

    def exit_app(self):
        self.save_config()
        if messagebox.askokcancel("Quit", "Do you really want to quit?"):
            self.root.destroy()

    def set_font(self, family):
        self.font_family = family
        self.font_var.set(family)
        self.text_font.config(family=family)
        self.save_config()

    def zoom_with_scroll(self, event):
        if event.delta > 0:
            self.font_size += 1
        else:
            self.font_size = max(8, self.font_size - 1)
        self.text_font.configure(size=self.font_size)
        self.save_config()

    def bind_shortcuts(self):
        self.text_area.bind("<Control-MouseWheel>", self.zoom_with_scroll)
        self.root.bind("<Control-f>", lambda e: self.toggle_find_bar())
        self.root.bind("<Control-h>", lambda e: (self.toggle_find_bar(), "break"))

if __name__ == "__main__":
    root = tk.Tk()
    app = Notepad(root)
    root.mainloop()