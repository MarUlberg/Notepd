
import socket
import threading

PORT = 56789
SINGLETON_HOST = '127.0.0.1'

def notify_existing_instance():
    try:
        with socket.create_connection((SINGLETON_HOST, PORT), timeout=1) as s:
            s.sendall(b"SHOW")
        return True
    except Exception:
        return False

import json
import os
from tkinterdnd2 import DND_FILES, TkinterDnD
import tkinter as tk
from tkinter import filedialog, font, ttk
from pathlib import Path


### ================= Configuration & Constants ================== ###

APP_NAME = "Notepd"
CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP_NAME)
os.makedirs(CONFIG_DIR, exist_ok=True)
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")


LIGHTGRAY_BG = "#424242"
MIDGRAY_BG = "#333333"
DARKGRAY_BG = "#212121"
LIGHT_TEXT = "#DEDEDE"
BUTTON_ACTIVE = "#393939"

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
        self.root.configure(bg=DARKGRAY_BG, highlightbackground=DARKGRAY_BG, highlightcolor=DARKGRAY_BG, highlightthickness=2)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Vertical.TScrollbar",
                        background=DARKGRAY_BG,
                        troughcolor=LIGHTGRAY_BG,
                        bordercolor=LIGHTGRAY_BG,
                        arrowcolor=LIGHTGRAY_BG,
                        lightcolor=DARKGRAY_BG,
                        darkcolor=DARKGRAY_BG,
                        relief="flat")
        style.configure("Horizontal.TScrollbar",
                        background=DARKGRAY_BG,
                        troughcolor=LIGHTGRAY_BG,
                        bordercolor=LIGHTGRAY_BG,
                        arrowcolor=LIGHTGRAY_BG,
                        lightcolor=DARKGRAY_BG,
                        darkcolor=DARKGRAY_BG,
                        relief="flat")
        style.map("Vertical.TScrollbar",
                  background=[("disabled", DARKGRAY_BG)])
        style.map("Horizontal.TScrollbar",
                  background=[("disabled", DARKGRAY_BG)])

        self.text_font = font.Font(family=self.font_family, size=self.font_size)
        self.wrap_enabled = self.wrap_state

        self.find_bar_visible = self.find_bar_state
        self.find_bar = None
        self.status_label = None
        self.match_case = tk.IntVar()
        self.wrap_around = tk.IntVar(value=1)
        self.search_direction = tk.StringVar(value="down")

        self.create_widgets()
        self.text_area.drop_target_register(DND_FILES)
        self.text_area.dnd_bind('<<Drop>>', self.handle_drop)

        self.root.after(200, self.create_menu)
        self.root.after(200, self.bind_shortcuts)

        if self.find_bar_visible:
            self.toggle_find_bar()

        self.update_cursor_position()
        self.root.protocol("WM_DELETE_WINDOW", self.hide_and_reset)

    def handle_drop(self, event):
        path = event.data.strip('{}')
        if os.path.isfile(path):
            if self.confirm_discard_changes():
                self.filename = path
                with open(path, "r", encoding="utf-8") as file:
                    content = file.read()
                    self.text_area.delete("1.0", tk.END)
                    self.text_area.insert(tk.END, content)
                    self.last_saved_text = content

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


### ====================== UI Construction ======================= ###

    def create_widgets(self):
        self.text_frame = tk.Frame(self.root, bg=LIGHTGRAY_BG)
        self.text_frame.grid(row=0, column=0, sticky="nsew")

        wrap_mode = "word" if self.wrap_enabled else "none"

        self.text_area = tk.Text(
            self.text_frame, wrap=wrap_mode, undo=True, font=self.text_font,
            bg=LIGHTGRAY_BG, fg=LIGHT_TEXT, insertbackground=LIGHT_TEXT,
            padx=10, pady=5, relief="flat"
        )
        self.text_area.grid(row=0, column=0, sticky="nsew")

        self.scroll_y = ttk.Scrollbar(self.text_frame, command=self.text_area.yview, style="Vertical.TScrollbar")
        self.scroll_y.grid(row=0, column=1, sticky="ns")
        self.text_area.configure(yscrollcommand=self.scroll_y.set)

        self.scroll_x = ttk.Scrollbar(self.text_frame, orient="horizontal", command=self.text_area.xview, style="Horizontal.TScrollbar")
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


### ======================= Menu Creation ======================== ###

    def create_menu(self):
        menu_bar = tk.Menu(self.root, bg=LIGHTGRAY_BG, fg=DARKGRAY_BG, activebackground=BUTTON_ACTIVE, activeforeground=LIGHT_TEXT, tearoff=0)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="New", command=self.new_file)
        file_menu.add_command(label="Open...", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Save As...", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Print...", command=self.print_file)
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


### ================== Cursor & Status Updates =================== ###

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


### ====================== File Operations ======================= ###

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


### ======================= Exit Handling ======================== ###

    def confirm_discard_changes(self):
        if not self.is_modified():
            return True
        if not self.text_area.get("1.0", tk.END).strip():
            return True

        dialog = tk.Toplevel(self.root)
        dialog.title("Notepd")
        dialog.configure(bg=DARKGRAY_BG)
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
                 bg=DARKGRAY_BG, fg=LIGHT_TEXT, font=("Segoe UI", 12)
        ).pack(pady=(20, 0), padx=12, anchor="w")

        # Filename on separate line with wrapping
        tk.Label(dialog, text=file_display,
                 bg=DARKGRAY_BG, fg=LIGHT_TEXT, font=("Segoe UI", 14, "bold"),
                 wraplength=440, justify="left", anchor="w"
        ).pack(padx=15, anchor="w")

        result = {"action": None}
        def do(action):
            result["action"] = action
            dialog.destroy()

        btn_frame = tk.Frame(dialog, bg=DARKGRAY_BG)
        btn_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        tk.Frame(btn_frame, width=140, bg=DARKGRAY_BG).pack(side="left")  # spacer
        def styled_btn(txt, act):
            return tk.Button(btn_frame, text=txt, width=10, command=lambda: do(act),
                             bg=LIGHTGRAY_BG, fg=LIGHT_TEXT, relief="flat", padx=10, pady=3)

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

    def hide_and_reset(self):
        if self.confirm_discard_changes():
            self.filename = None
            self.text_area.delete("1.0", tk.END)
            self.last_saved_text = ""
            self.root.withdraw()

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


### ===================== Find/Replace Logic ===================== ###
  
    def toggle_find_bar(self):
        if self.find_bar and self.find_bar.winfo_exists():
            return

        self.find_bar = tk.Frame(self.root, bg=DARKGRAY_BG, bd=2)
        self.find_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

        for i in range(5):
            self.find_bar.grid_columnconfigure(i, weight=1 if i in [0, 2] else 0)
        self.find_bar.grid_columnconfigure(4, minsize=180)

        self.find_entry = tk.Entry(self.find_bar, bg=LIGHTGRAY_BG, fg=LIGHT_TEXT, insertbackground=LIGHT_TEXT)
        self.find_entry.grid(row=0, column=0, padx=5, pady=(0, 0), sticky="ew")

        find_btn = tk.Button(self.find_bar, text="Find Next", command=self.do_find,
                             bg=MIDGRAY_BG, fg=LIGHT_TEXT, activebackground=BUTTON_ACTIVE,
                             relief="flat", width=12, padx=4, pady=0)
        find_btn.grid(row=0, column=1, padx=(3, 8), pady=(2, 2), sticky="ew")

        tk.Radiobutton(self.find_bar, text="Up", variable=self.search_direction, value="up",
                       bg=DARKGRAY_BG, fg=LIGHT_TEXT, selectcolor=DARKGRAY_BG, activebackground=MIDGRAY_BG).grid(row=1, column=1, sticky="w", padx=0)
        tk.Radiobutton(self.find_bar, text="Down", variable=self.search_direction, value="down",
                       bg=DARKGRAY_BG, fg=LIGHT_TEXT, selectcolor=DARKGRAY_BG, activebackground=MIDGRAY_BG).grid(row=1, column=1, sticky="e", padx=(3, 5))

        self.replace_entry = tk.Entry(self.find_bar, bg=LIGHTGRAY_BG, fg=LIGHT_TEXT, insertbackground=LIGHT_TEXT)
        self.replace_entry.grid(row=0, column=2, padx=5, pady=(0, 0), sticky="ew")

        self.find_entry.bind("<Return>", lambda e: self.do_find())
        self.find_entry.bind("<Shift-Return>", lambda e: self.toggle_search_direction_and_find())
        self.replace_entry.bind("<Return>", lambda e: self.do_replace())
        self.replace_entry.bind("<Shift-Return>", lambda e: self.toggle_search_direction_and_find())


        tk.Button(self.find_bar, text="Replace", command=self.do_replace,
                  bg=MIDGRAY_BG, fg=LIGHT_TEXT, activebackground=BUTTON_ACTIVE,
                  relief="flat", width=12, padx=4, pady=0).grid(row=0, column=3, padx=(3, 8), pady=(2, 2), sticky="ew")

        tk.Button(self.find_bar, text="Replace All", command=self.do_replace_all,
                  bg=MIDGRAY_BG, fg=LIGHT_TEXT, activebackground=BUTTON_ACTIVE,
                  relief="flat", width=12, padx=4, pady=0).grid(row=1, column=3, padx=(3, 8), pady=(2, 0), sticky="ew")

        tk.Checkbutton(self.find_bar, text="Wrap around", variable=self.wrap_around,
                       bg=DARKGRAY_BG, fg=LIGHT_TEXT, selectcolor=DARKGRAY_BG, activebackground=MIDGRAY_BG).grid(row=1, column=0, sticky="w", padx=5)
        tk.Checkbutton(self.find_bar, text="Match case", variable=self.match_case,
                       bg=DARKGRAY_BG, fg=LIGHT_TEXT, selectcolor=DARKGRAY_BG, activebackground=MIDGRAY_BG).grid(row=1, column=0, sticky="w", padx=(120, 5))

        self.status_label = tk.Label(self.find_bar, text="", fg=LIGHT_TEXT, bg=DARKGRAY_BG, anchor="e")
        self.status_label.grid(row=1, column=4, padx=10, sticky="e")
        tk.Button(self.find_bar, text="✕", command=self.find_bar.destroy,
          bg=DARKGRAY_BG, fg="#606060", relief="flat", padx=6, pady=2,
          activebackground=BUTTON_ACTIVE).grid(row=0, column=4, sticky="ne", padx=0, pady=0)
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
            self.text_area.tag_config("found", background=DARKGRAY_BG)
            self.text_area.mark_set("insert", idx if backwards else end)
            self.text_area.see(idx)
        elif self.wrap_around.get():
            restart = tk.END if backwards else "1.0"
            idx = self.text_area.search(query, restart, stopindex=start,
                                        nocase=not self.match_case.get(), backwards=backwards)
            if idx:
                end = f"{idx}+{len(query)}c"
                self.text_area.tag_add("found", idx, end)
                self.text_area.tag_config("found", background=DARKGRAY_BG)
                self.text_area.mark_set("insert", idx if backwards else end)
                self.text_area.see(idx)

    def do_replace(self):
        if self.text_area.tag_ranges("found"):
            try:
                replace_pos = self.text_area.index("found.first")
                self.text_area.delete("found.first", "found.last")
                self.text_area.insert(replace_pos, self.replace_entry.get())
            except tk.TclError:
                pass
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

    def insert_datetime(self):
        from datetime import datetime
        self.text_area.insert("insert", datetime.now().strftime("%H:%M %d/%m/%Y"))

    def print_file(self):
        try:
            import win32print
            import win32ui
            from tempfile import NamedTemporaryFile
            win32api = __import__('win32api')

            text = self.text_area.get("1.0", "end-1c")
            if not text.strip():
                return
            with NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
                tmp.write(text)
                tmp_path = tmp.name
            win32api.ShellExecute(0, "print", tmp_path, None, ".", 0)
        except Exception as e:
            print("Print error:", e)

    def search_google(self):
        try:
            from urllib.parse import quote
            import webbrowser
            selected = self.text_area.selection_get()
            if selected.strip():
                webbrowser.open(f"https://www.google.com/search?q={quote(selected)}")
        except tk.TclError:
            pass

    def toggle_search_direction_and_find(self):
        current = self.search_direction.get()
        self.search_direction.set("up" if current == "down" else "down")
        self.do_find()


### ======================== Key Bindings ======================== ###

    def singleton_server(self):
        def listen():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((SINGLETON_HOST, PORT))
                s.listen(1)
                while True:
                    conn, _ = s.accept()
                    with conn:
                        msg = conn.recv(1024).decode()
                        if msg == "SHOW":
                            self.root.after(0, lambda: self.root.deiconify())
        threading.Thread(target=listen, daemon=True).start()

    def bind_shortcuts(self):
        self.text_area.bind("<Control-MouseWheel>", self.zoom_with_scroll)
        def handle_ctrl_f(event):
            try:
                selection = self.text_area.selection_get()
                if selection.strip():
                    self.toggle_find_bar()
                    self.find_entry.delete(0, tk.END)
                    self.find_entry.insert(0, selection)
                    return "break"
            except tk.TclError:
                pass
            self.toggle_find_bar()
            return "break"

        self.root.bind("<Control-f>", handle_ctrl_f)

        # Ctrl+H override on the text widget itself
        def handle_ctrl_h(event):
            try:
                selection = self.text_area.selection_get()
                if selection.strip():
                    self.toggle_find_bar()
                    self.find_entry.delete(0, tk.END)
                    self.find_entry.insert(0, selection)
                    return "break"
            except tk.TclError:
                pass
            self.toggle_find_bar()
            return "break"

        self.text_area.bind("<Control-h>", handle_ctrl_h)
        self.root.bind("<Control-h>", handle_ctrl_h)


        self.text_area.bind("<Control-h>", handle_ctrl_h)  # override text widget's backspace
        self.root.bind("<Control-h>", handle_ctrl_h)       # catch it at root level too

        self.root.bind("<Control-o>", lambda e: (self.open_file(), "break"))
        self.root.bind("<Control-s>", lambda e: (self.save_file(), "break"))
        self.root.bind("<F5>", lambda e: self.insert_datetime())
        self.root.bind("<Control-p>", lambda e: self.print_file())
        self.root.bind("<Control-e>", lambda e: self.search_google())


### ================== Application Entry Point =================== ###

if __name__ == "__main__":
    if notify_existing_instance():
        sys.exit()

    root = TkinterDnD.Tk()
    try:
        root.tk.eval('package require tkdnd')
    except tk.TclError as e:
        print("Failed to load tkdnd package:", e)
    app = Notepad(root)
    app.singleton_server()
    root.mainloop()

