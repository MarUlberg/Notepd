# notepd_final_v10.py — visual tweaks, better dialog, border highlight
import json
import os
import tkinter as tk
from tkinter import filedialog, font
from pathlib import Path

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
        self.root.title("Notepd")
        self.filename = None
        self.last_saved_text = ""
        self.load_config()

        self.root.geometry(self.window_size or "900x650")
        self.root.configure(bg=DARK_BG)

        self.text_font = font.Font(family=self.font_family, size=self.font_size)
        self.wrap_enabled = self.wrap_state

        self.find_bar_visible = self.find_bar_state
        self.find_bar = None
        self.status_label = None
        self.match_case = tk.IntVar()
        self.wrap_around = tk.IntVar(value=1)
        self.search_direction = tk.StringVar(value="down")

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
        self.wrap_state = True

        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r") as f:
                    data = json.load(f)
                    self.font_family = data.get("font_family", self.font_family)
                    self.font_size = data.get("font_size", self.font_size)
                    self.window_size = data.get("window_size", self.window_size)
                    self.find_bar_state = data.get("find_bar_visible", False)
                    self.wrap_state = data.get("wrap_enabled", True)
            except Exception:
                pass

    def save_config(self):
        data = {
            "font_family": self.font_family,
            "font_size": self.font_size,
            "window_size": self.root.geometry(),
            "find_bar_visible": bool(self.find_bar and self.find_bar.winfo_exists()),
            "wrap_enabled": self.wrap_enabled
        }
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(data, f)
        except Exception:
            pass

    def create_widgets(self):
        self.text_frame = tk.Frame(self.root, bg=DARK_BG)
        self.text_frame.grid(row=0, column=0, sticky="nsew")

        wrap_mode = "word" if self.wrap_enabled else "none"

        self.text_area = tk.Text(
            self.text_frame, wrap=wrap_mode, undo=True, font=self.text_font,
            bg=DARK_BG, fg=LIGHT_TEXT, insertbackground=LIGHT_TEXT,
            padx=10, pady=5
        )
        self.text_area.grid(row=0, column=0, sticky="nsew")

        self.scroll_y = tk.Scrollbar(self.text_frame, command=self.text_area.yview)
        self.scroll_y.grid(row=0, column=1, sticky="ns")
        self.text_area.configure(yscrollcommand=self.scroll_y.set)

        self.scroll_x = tk.Scrollbar(self.text_frame, orient="horizontal", command=self.text_area.xview)
        self.scroll_x.grid(row=1, column=0, sticky="ew")
        self.text_area.configure(xscrollcommand=self.scroll_x.set)
        self.scroll_x.grid_remove()

        if not self.wrap_enabled:
            self.scroll_x.grid()

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
        file_menu.add_command(label="Save As...", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_app)
        menu_bar.add_cascade(label="File", menu=file_menu)

        font_menu = tk.Menu(menu_bar, tearoff=0)
        self.wrap_var = tk.BooleanVar(value=self.wrap_enabled)
        font_menu.add_checkbutton(label="Wrap text", variable=self.wrap_var, command=self.toggle_wrap)
        font_menu.add_separator()

        self.font_var = tk.StringVar(value=self.font_family)
        for f in FONTS:
            font_menu.add_radiobutton(label=f, variable=self.font_var, value=f, command=lambda fam=f: self.set_font(fam))
        menu_bar.add_cascade(label="Font", menu=font_menu)

        self.root.config(menu=menu_bar)

    def toggle_wrap(self):
        self.wrap_enabled = self.wrap_var.get()
        wrap_mode = "word" if self.wrap_enabled else "none"
        self.text_area.configure(wrap=wrap_mode)
        if self.wrap_enabled:
            self.scroll_x.grid_remove()
        else:
            self.scroll_x.grid()
        self.save_config()

    def update_cursor_position(self):
        self.root.after_idle(self._update_cursor)

    def _update_cursor(self):
        try:
            index = self.text_area.index("insert")
            line, col = map(int, index.split("."))
            count = self.text_area.count("1.0", "insert", "chars")
            pos = count[0] + 1 if count else 1

            # Only update if the label still exists
            if self.status_label and self.status_label.winfo_exists():
                self.status_label.config(text=f"Ln : {line}   Col : {col+1}   Pos : {pos}")

        except Exception as e:
            print("Cursor update failed:", e)


    def is_modified(self):
        current = self.text_area.get("1.0", tk.END).strip()
        return current != self.last_saved_text.strip()

    def new_file(self):
        if self.confirm_discard_changes():
            self.filename = None
            self.text_area.delete(1.0, tk.END)
            self.last_saved_text = ""

    def open_file(self):
        if not self.confirm_discard_changes():
            return
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if path:
            self.filename = path
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()
                self.text_area.delete("1.0", tk.END)
                self.text_area.insert(tk.END, content)
                self.last_saved_text = content

    def save_file(self):
        if self.filename:
            content = self.text_area.get("1.0", tk.END)
            with open(self.filename, "w", encoding="utf-8") as file:
                file.write(content)
            self.last_saved_text = content
        else:
            self.save_file_as()

    def save_file_as(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if path:
            self.filename = path
            content = self.text_area.get("1.0", tk.END)
            with open(path, "w", encoding="utf-8") as file:
                file.write(content)
            self.last_saved_text = content

    def confirm_discard_changes(self):
        if not self.is_modified():
            return True
        if not self.text_area.get("1.0", tk.END).strip():
            return True

        dialog = tk.Toplevel(self.root)
        dialog.title("Notepd")
        dialog.configure(bg=ACCENT_COLOR)
        dialog.resizable(False, False)
        dialog.geometry("480x150")

        # Wait for dialog to compute its size
        dialog.update_idletasks()

        # Get main window geometry
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_w = self.root.winfo_width()
        main_h = self.root.winfo_height()

        # Get dialog dimensions
        dialog_w = dialog.winfo_width()
        dialog_h = dialog.winfo_height()

        # Calculate centered position
        x = main_x + (main_w - dialog_w) // 2
        y = main_y + (main_h - dialog_h) // 2

        # Position dialog
        dialog.geometry(f"+{x}+{y}")


        file_display = Path(self.filename).name if self.filename else "Untitled"

        # Main message
        tk.Label(dialog, text="Do you want to save changes to",
                 bg=ACCENT_COLOR, fg=LIGHT_TEXT, font=("Segoe UI", 12)
        ).pack(pady=(20, 0), padx=12, anchor="w")

        # Filename on separate line with wrapping
        tk.Label(dialog, text=file_display,
                 bg=ACCENT_COLOR, fg=LIGHT_TEXT, font=("Segoe UI", 14, "bold"),
                 wraplength=440, justify="left", anchor="w"
        ).pack(padx=15, anchor="w")

        result = {"action": None}
        def do(action):
            result["action"] = action
            dialog.destroy()

        btn_frame = tk.Frame(dialog, bg=ACCENT_COLOR)
        btn_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        tk.Frame(btn_frame, width=140, bg=ACCENT_COLOR).pack(side="left")  # spacer
        def styled_btn(txt, act):
            return tk.Button(btn_frame, text=txt, width=10, command=lambda: do(act),
                             bg=DARK_BG, fg=LIGHT_TEXT, relief="flat", padx=10, pady=3)

        styled_btn("Save", "save").pack(side="left", padx=5)
        styled_btn("Don't Save", "discard").pack(side="left", padx=5)
        styled_btn("Cancel", "cancel").pack(side="left", padx=5)

        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)

        if result["action"] == "save":
            self.save_file()
            return True
        elif result["action"] == "discard":
            return True
        return False


    def exit_app(self):
        self.save_config()
        if self.confirm_discard_changes():
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

    def toggle_find_bar(self):
        if self.find_bar and self.find_bar.winfo_exists():
            self.find_bar.destroy()
            return

        self.find_bar = tk.Frame(self.root, bg=ACCENT_COLOR, bd=2, highlightbackground=ACCENT_COLOR, highlightthickness=2)
        self.find_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

        for i in range(6):
            self.find_bar.grid_columnconfigure(i, weight=1 if i in [0, 3] else 0)
        self.find_bar.grid_columnconfigure(5, minsize=180)

        self.find_entry = tk.Entry(self.find_bar, bg=DARK_BG, fg=LIGHT_TEXT, insertbackground=LIGHT_TEXT)
        self.find_entry.grid(row=0, column=0, padx=5, pady=(2, 0), sticky="ew")

        find_btn = tk.Button(self.find_bar, text="Find Next", command=self.do_find,
                             bg=BUTTON_BG, fg=LIGHT_TEXT, activebackground=BUTTON_ACTIVE,
                             relief="flat", width=12, padx=4, pady=0)
        find_btn.grid(row=0, column=1, padx=5, pady=(2, 1), sticky="ew")

        tk.Radiobutton(self.find_bar, text="Up", variable=self.search_direction, value="up",
                       bg=ACCENT_COLOR, fg=LIGHT_TEXT, selectcolor=ACCENT_COLOR).grid(row=1, column=1, sticky="w", padx=5)
        tk.Radiobutton(self.find_bar, text="Down", variable=self.search_direction, value="down",
                       bg=ACCENT_COLOR, fg=LIGHT_TEXT, selectcolor=ACCENT_COLOR).grid(row=1, column=1, sticky="e", padx=5)

        self.replace_entry = tk.Entry(self.find_bar, bg=DARK_BG, fg=LIGHT_TEXT, insertbackground=LIGHT_TEXT)
        self.replace_entry.grid(row=0, column=3, padx=5, pady=(2, 0), sticky="ew")

        tk.Button(self.find_bar, text="Replace", command=self.do_replace,
                  bg=BUTTON_BG, fg=LIGHT_TEXT, activebackground=BUTTON_ACTIVE,
                  relief="flat", width=12, padx=4, pady=0).grid(row=0, column=4, padx=5, pady=(2, 1), sticky="ew")

        tk.Button(self.find_bar, text="Replace All", command=self.do_replace_all,
                  bg=BUTTON_BG, fg=LIGHT_TEXT, activebackground=BUTTON_ACTIVE,
                  relief="flat", width=12, padx=4, pady=0).grid(row=1, column=4, padx=5, pady=(2, 2), sticky="ew")

        tk.Checkbutton(self.find_bar, text="Wrap around", variable=self.wrap_around,
                       bg=ACCENT_COLOR, fg=LIGHT_TEXT, selectcolor=ACCENT_COLOR).grid(row=1, column=0, sticky="w", padx=5)
        tk.Checkbutton(self.find_bar, text="Match case", variable=self.match_case,
                       bg=ACCENT_COLOR, fg=LIGHT_TEXT, selectcolor=ACCENT_COLOR).grid(row=1, column=0, sticky="w", padx=(120, 5))

        self.status_label = tk.Label(self.find_bar, text="", fg=LIGHT_TEXT, bg=ACCENT_COLOR, anchor="e")
        self.status_label.grid(row=1, column=5, padx=10, sticky="e")
        self.update_cursor_position()

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
            try:
                self.text_area.delete("found.first", "found.last")
                self.text_area.insert("found.first", self.replace_entry.get())
            except tk.TclError:
                pass  # handle rare case where tag was cleared
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

    def bind_shortcuts(self):
        self.text_area.bind("<Control-MouseWheel>", self.zoom_with_scroll)
        self.root.bind("<Control-f>", lambda e: self.toggle_find_bar())

        # Ctrl+H override on the text widget itself
        def handle_ctrl_h(event):
            self.toggle_find_bar()
            return "break"

        self.text_area.bind("<Control-h>", handle_ctrl_h)  # override text widget's backspace
        self.root.bind("<Control-h>", handle_ctrl_h)       # catch it at root level too

        self.root.bind("<Control-o>", lambda e: (self.open_file(), "break"))
        self.root.bind("<Control-s>", lambda e: (self.save_file(), "break"))



if __name__ == "__main__":
    root = tk.Tk()
    app = Notepad(root)
    root.mainloop()
