"""
config_gui.py - 4x2 key mapping window with drag-and-drop support.
"""

import json
import os
import tkinter as tk
from tkinter import messagebox

from key_mapper import F_KEYS, MEDIA_ACTION_NAMES


CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

ACTION_ICONS = {
    "mute": "M",
    "volume_down": "-",
    "volume_up": "+",
    "next_track": ">>",
    "prev_track": "<<",
    "stop": "[]",
    "play_pause": "||>",
    "launch_media": "MP",
}

ACTION_SHORT_NAMES = {
    "mute": "Sessiz",
    "volume_down": "Ses -",
    "volume_up": "Ses +",
    "next_track": "Sonraki",
    "prev_track": "Onceki",
    "stop": "Durdur",
    "play_pause": "Oynat",
    "launch_media": "Medya",
}

BUTTON_COLORS = [
    {"bg": "#f38ba8", "hover": "#f5a0b8"},
    {"bg": "#fab387", "hover": "#fbc4a0"},
    {"bg": "#f9e2af", "hover": "#fae8c0"},
    {"bg": "#a6e3a1", "hover": "#b8e8b4"},
    {"bg": "#89b4fa", "hover": "#a0c4fb"},
    {"bg": "#89dceb", "hover": "#a0e4ef"},
    {"bg": "#cba6f7", "hover": "#d6b8f9"},
    {"bg": "#f5c2e7", "hover": "#f7d0ec"},
]

BG_COLOR = "#11111b"
TEXT_COLOR = "#cdd6f4"
SUBTLE_COLOR = "#6c7086"
BORDER_COLOR = "#313244"

DEFAULT_CONFIG = {
    "mappings": {
        "f1": "mute",
        "f2": "volume_down",
        "f3": "volume_up",
        "f4": "prev_track",
        "f5": "play_pause",
        "f6": "next_track",
        "f7": "stop",
        "f8": "launch_media",
    },
    "autostart": True,
}


def load_config() -> dict:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "mappings": dict(DEFAULT_CONFIG["mappings"]),
            "autostart": DEFAULT_CONFIG["autostart"],
        }


def save_config(config: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=4, ensure_ascii=False)


def rounded_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    r = radius
    canvas.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, style="pieslice", **kwargs)
    canvas.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, style="pieslice", **kwargs)
    canvas.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, style="pieslice", **kwargs)
    canvas.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, style="pieslice", **kwargs)
    canvas.create_rectangle(x1 + r, y1, x2 - r, y2, **kwargs)
    canvas.create_rectangle(x1, y1 + r, x1 + r, y2 - r, **kwargs)
    canvas.create_rectangle(x2 - r, y1 + r, x2, y2 - r, **kwargs)


class DeckButton:
    SIZE = 130
    RADIUS = 18

    def __init__(self, parent, index, f_key, action, color, grid_row, grid_col, on_drag_start, on_drag_end):
        self.index = index
        self.f_key = f_key
        self.action = action
        self.color = color
        self.on_drag_start = on_drag_start
        self.on_drag_end = on_drag_end
        self._dragging = False
        self._hovered = False
        self._bounds = None

        size = self.SIZE
        self.canvas = tk.Canvas(parent, width=size, height=size, bg=BG_COLOR, highlightthickness=0)
        self.canvas.grid(row=grid_row, column=grid_col, padx=6, pady=6)

        self._draw(self.color["bg"])
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

    def _draw(self, fill_color):
        self.canvas.delete("all")
        size = self.SIZE
        radius = self.RADIUS
        rounded_rect(self.canvas, 3, 3, size - 1, size - 1, radius, fill="#0a0a12", outline="")
        rounded_rect(self.canvas, 0, 0, size - 4, size - 4, radius, fill=fill_color, outline="")

        fg = "#1e1e2e"
        self.canvas.create_text(14, 12, text=self.f_key.upper(), font=("Segoe UI", 9, "bold"), fill=fg, anchor="nw")
        self.canvas.create_text(
            (size - 4) // 2,
            (size - 4) // 2 - 4,
            text=ACTION_ICONS.get(self.action, "?"),
            font=("Consolas", 22, "bold"),
            fill=fg,
            anchor="center",
        )
        self.canvas.create_text(
            (size - 4) // 2,
            size - 22,
            text=ACTION_SHORT_NAMES.get(self.action, "?"),
            font=("Segoe UI", 10, "bold"),
            fill=fg,
            anchor="center",
        )

    def _on_enter(self, _event):
        if not self._dragging and not self._hovered:
            self._hovered = True
            self._draw(self.color["hover"])

    def _on_leave(self, _event):
        if not self._dragging and self._hovered:
            self._hovered = False
            self._draw(self.color["bg"])

    def _on_press(self, event):
        self._dragging = True
        self.on_drag_start(self)

    def _on_motion(self, _event):
        return

    def _on_release(self, event):
        self._dragging = False
        self._draw(self.color["bg"])
        self.on_drag_end(self, event.x_root, event.y_root)

    def update_action(self, new_action):
        self.action = new_action
        self._draw(self.color["bg"])

    def highlight(self, on=True):
        if on:
            self.canvas.delete("all")
            size = self.SIZE
            radius = self.RADIUS
            rounded_rect(self.canvas, 0, 0, size - 4, size - 4, radius, fill=self.color["hover"], outline="#cdd6f4")
            fg = "#1e1e2e"
            self.canvas.create_text((size - 4) // 2, (size - 4) // 2 - 4, text="<->", font=("Consolas", 22, "bold"), fill=fg)
            self.canvas.create_text((size - 4) // 2, size - 22, text="Birak", font=("Segoe UI", 10, "bold"), fill=fg)
        else:
            self._draw(self.color["bg"])

    def update_bounds(self):
        self._bounds = (
            self.canvas.winfo_rootx(),
            self.canvas.winfo_rooty(),
            self.canvas.winfo_width(),
            self.canvas.winfo_height(),
        )

    def contains_screen_point(self, x_root, y_root):
        if self._bounds is None:
            self.update_bounds()

        x, y, width, height = self._bounds
        return x <= x_root <= x + width and y <= y_root <= y + height


class ConfigWindow:
    def __init__(self, on_save_callback=None):
        self.on_save_callback = on_save_callback
        self.root = None
        self.deck_buttons = {}
        self._button_list = []
        self._drag_source = None
        self._last_highlight_target = None

    def show(self):
        if self.root is not None:
            try:
                self.root.lift()
                self.root.focus_force()
                return
            except tk.TclError:
                self.root = None

        config = load_config()
        mappings = config.get("mappings", {})

        self.root = tk.Tk()
        self.root.title("MiniKeyCtrl")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_COLOR)
        self.root.attributes("-alpha", 0.97)

        header = tk.Frame(self.root, bg=BG_COLOR)
        header.pack(fill="x", padx=24, pady=(18, 0))
        tk.Label(header, text="MiniKeyCtrl", font=("Segoe UI", 18, "bold"), bg=BG_COLOR, fg=TEXT_COLOR).pack(side="left")
        tk.Label(header, text="Surukle ve birak", font=("Segoe UI", 10), bg=BG_COLOR, fg=SUBTLE_COLOR).pack(side="right", pady=(8, 0))

        tk.Frame(self.root, bg=BORDER_COLOR, height=1).pack(fill="x", padx=24, pady=(12, 0))

        info_bar = tk.Frame(self.root, bg=BG_COLOR)
        info_bar.pack(fill="x", padx=24, pady=(10, 0))
        tk.Label(
            info_bar,
            text="Tuslari surukleyerek yer degistir veya sag tikla islev sec",
            font=("Segoe UI", 9),
            bg=BG_COLOR,
            fg=SUBTLE_COLOR,
        ).pack(side="left")

        grid_frame = tk.Frame(self.root, bg=BG_COLOR)
        grid_frame.pack(padx=20, pady=(12, 12))

        self.deck_buttons = {}
        for index, f_key in enumerate(F_KEYS):
            action = mappings.get(f_key, "mute")
            button = DeckButton(
                grid_frame,
                index=index,
                f_key=f_key,
                action=action,
                color=BUTTON_COLORS[index],
                grid_row=index // 4,
                grid_col=index % 4,
                on_drag_start=self._drag_start,
                on_drag_end=self._drag_end,
            )
            button.canvas.bind("<Button-3>", lambda event, db=button: self._show_menu(event, db))
            self.deck_buttons[f_key] = button

        self._refresh_button_bounds()

        tk.Frame(self.root, bg=BORDER_COLOR, height=1).pack(fill="x", padx=24, pady=(2, 0))

        bottom = tk.Frame(self.root, bg=BG_COLOR)
        bottom.pack(fill="x", padx=24, pady=(12, 18))
        self.status_label = tk.Label(bottom, text="Hazir", font=("Segoe UI", 9), bg=BG_COLOR, fg=SUBTLE_COLOR)
        self.status_label.pack(side="left")

        save_btn = tk.Canvas(bottom, width=120, height=38, bg=BG_COLOR, highlightthickness=0)
        save_btn.pack(side="right")
        self._draw_save_button(save_btn, "#a6e3a1")
        save_btn.bind("<Button-1>", lambda _event: self._save())
        save_btn.bind("<Enter>", lambda _event: self._draw_save_button(save_btn, "#94e2d5"))
        save_btn.bind("<Leave>", lambda _event: self._draw_save_button(save_btn, "#a6e3a1"))
        save_btn.configure(cursor="hand2")

        total_w = (DeckButton.SIZE * 4) + (6 * 8) + 52
        total_h = (DeckButton.SIZE * 2) + (6 * 2) + 190
        self.root.geometry(f"{total_w}x{total_h}")
        self.root.update_idletasks()
        self._refresh_button_bounds()
        x = (self.root.winfo_screenwidth() // 2) - (total_w // 2)
        y = (self.root.winfo_screenheight() // 2) - (total_h // 2)
        self.root.geometry(f"+{x}+{y}")

        self.root.bind("<B1-Motion>", self._drag_motion)
        self.root.bind("<Configure>", self._on_configure)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _draw_save_button(self, canvas, fill_color):
        canvas.delete("all")
        rounded_rect(canvas, 0, 0, 118, 36, 10, fill=fill_color, outline="")
        canvas.create_text(60, 18, text="KAYDET", font=("Segoe UI", 11, "bold"), fill="#1e1e2e")

    def _drag_start(self, source_btn):
        self._refresh_button_bounds()
        self._drag_source = source_btn
        self.status_label.configure(text=f"{source_btn.f_key.upper()} surukleniyor", fg="#f9e2af")
        source_btn.canvas.delete("all")
        size = DeckButton.SIZE
        radius = DeckButton.RADIUS
        rounded_rect(source_btn.canvas, 0, 0, size - 4, size - 4, radius, fill="#45475a", outline="#cdd6f4")
        source_btn.canvas.create_text((size - 4) // 2, (size - 4) // 2, text="DRAG", font=("Consolas", 20, "bold"), fill="#cdd6f4")
        source_btn.canvas.create_text((size - 4) // 2, size - 22, text=source_btn.f_key.upper(), font=("Segoe UI", 10, "bold"), fill="#cdd6f4")

    def _drag_motion(self, event):
        if not self._drag_source:
            return

        target = self._find_button_at(event.x_root, event.y_root)
        if target == self._last_highlight_target:
            return

        if self._last_highlight_target and self._last_highlight_target != self._drag_source:
            self._last_highlight_target.highlight(False)

        if target and target != self._drag_source:
            target.highlight(True)

        self._last_highlight_target = target

    def _drag_end(self, source_btn, x_root, y_root):
        if not self._drag_source:
            return

        target = self._find_button_at(x_root, y_root)
        if self._last_highlight_target and self._last_highlight_target != source_btn:
            self._last_highlight_target.highlight(False)

        if target and target != source_btn:
            source_action = source_btn.action
            target_action = target.action
            source_btn.update_action(target_action)
            target.update_action(source_action)
            self.status_label.configure(text=f"{source_btn.f_key.upper()} <-> {target.f_key.upper()} degisti", fg="#a6e3a1")
        else:
            source_btn._draw(source_btn.color["bg"])
            self.status_label.configure(text="Hazir", fg=SUBTLE_COLOR)

        self._drag_source = None
        self._last_highlight_target = None

    def _find_button_at(self, x_root, y_root):
        for button in self._button_list:
            try:
                if button.contains_screen_point(x_root, y_root):
                    return button
            except Exception:
                pass
        return None

    def _refresh_button_bounds(self):
        self._button_list = list(self.deck_buttons.values())
        for button in self._button_list:
            button.update_bounds()

    def _on_configure(self, event):
        if event.widget == self.root and self.deck_buttons:
            self._refresh_button_bounds()

    def _show_menu(self, event, deck_btn):
        menu = tk.Menu(self.root, tearoff=0, font=("Segoe UI", 11))
        menu.configure(bg="#1e1e2e", fg="#cdd6f4", activebackground="#89b4fa", activeforeground="#1e1e2e")

        for action_key, action_name in MEDIA_ACTION_NAMES.items():
            label = f"{ACTION_ICONS.get(action_key, '')}  {action_name}"
            menu.add_command(label=label, command=lambda db=deck_btn, ak=action_key: self._set_action(db, ak))

        menu.post(event.x_root, event.y_root)

    def _set_action(self, deck_btn, action):
        deck_btn.update_action(action)
        self.status_label.configure(text=f"{deck_btn.f_key.upper()} -> {ACTION_SHORT_NAMES[action]}", fg="#89b4fa")

    def _save(self):
        config = load_config()
        config["mappings"] = {f_key: deck_btn.action for f_key, deck_btn in self.deck_buttons.items()}
        save_config(config)

        if self.on_save_callback:
            self.on_save_callback(config["mappings"])

        self.status_label.configure(text="Ayarlar kaydedildi", fg="#a6e3a1")
        messagebox.showinfo("MiniKeyCtrl", "Ayarlar kaydedildi", parent=self.root)

    def _on_close(self):
        if self.root:
            self.root.destroy()
            self.root = None
