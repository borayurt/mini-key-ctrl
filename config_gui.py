"""
config_gui.py - Elgato Stream Deck tarzı 4x2 grid tuş yapılandırma penceresi.
Rounded corners (Canvas) + Sürükle-Bırak ile tuş fonksiyonu değiştirme.
"""

import tkinter as tk
from tkinter import messagebox
import json
import os

from key_mapper import F_KEYS, MEDIA_ACTION_NAMES, NAME_TO_ACTION


CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

# Emoji ikonları
ACTION_ICONS = {
    "mute":          "🔇",
    "volume_down":   "🔉",
    "volume_up":     "🔊",
    "next_track":    "⏭",
    "prev_track":    "⏮",
    "stop":          "⏹",
    "play_pause":    "⏯",
    "launch_media":  "🎵",
}

ACTION_SHORT_NAMES = {
    "mute":          "Sessiz",
    "volume_down":   "Ses -",
    "volume_up":     "Ses +",
    "next_track":    "Sonraki",
    "prev_track":    "Önceki",
    "stop":          "Durdur",
    "play_pause":    "Oynat",
    "launch_media":  "Medya",
}

# Catppuccin Mocha renk paleti
BUTTON_COLORS = [
    {"bg": "#f38ba8", "hover": "#f5a0b8", "glow": "#f38ba840"},  # F1
    {"bg": "#fab387", "hover": "#fbc4a0", "glow": "#fab38740"},  # F2
    {"bg": "#f9e2af", "hover": "#fae8c0", "glow": "#f9e2af40"},  # F3
    {"bg": "#a6e3a1", "hover": "#b8e8b4", "glow": "#a6e3a140"},  # F4
    {"bg": "#89b4fa", "hover": "#a0c4fb", "glow": "#89b4fa40"},  # F5
    {"bg": "#89dceb", "hover": "#a0e4ef", "glow": "#89dceb40"},  # F6
    {"bg": "#cba6f7", "hover": "#d6b8f9", "glow": "#cba6f740"},  # F7
    {"bg": "#f5c2e7", "hover": "#f7d0ec", "glow": "#f5c2e740"},  # F8
]

BG_COLOR = "#11111b"
CARD_BG = "#1e1e2e"
TEXT_COLOR = "#cdd6f4"
SUBTLE_COLOR = "#6c7086"
BORDER_COLOR = "#313244"


def load_config() -> dict:
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "mappings": {
                "f1": "mute", "f2": "volume_down", "f3": "volume_up",
                "f4": "prev_track", "f5": "play_pause", "f6": "next_track",
                "f7": "stop", "f8": "launch_media",
            },
            "autostart": True,
        }


def save_config(config: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def rounded_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    """Canvas üzerinde yuvarlatılmış köşeli dikdörtgen çizer."""
    r = radius
    canvas.create_arc(x1, y1, x1 + 2*r, y1 + 2*r, start=90, extent=90, style="pieslice", **kwargs)
    canvas.create_arc(x2 - 2*r, y1, x2, y1 + 2*r, start=0, extent=90, style="pieslice", **kwargs)
    canvas.create_arc(x1, y2 - 2*r, x1 + 2*r, y2, start=180, extent=90, style="pieslice", **kwargs)
    canvas.create_arc(x2 - 2*r, y2 - 2*r, x2, y2, start=270, extent=90, style="pieslice", **kwargs)
    canvas.create_rectangle(x1 + r, y1, x2 - r, y2, **kwargs)
    canvas.create_rectangle(x1, y1 + r, x1 + r, y2 - r, **kwargs)
    canvas.create_rectangle(x2 - r, y1 + r, x2, y2 - r, **kwargs)


class DeckButton:
    """Canvas tabanlı rounded-corner deck butonu."""

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

        s = self.SIZE
        self.canvas = tk.Canvas(
            parent, width=s, height=s,
            bg=BG_COLOR, highlightthickness=0,
        )
        self.canvas.grid(row=grid_row, column=grid_col, padx=6, pady=6)

        self._draw(color["bg"])

        # Event binding
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

    def _draw(self, fill_color):
        """Butonu Canvas üzerine çizer."""
        self.canvas.delete("all")
        s = self.SIZE
        r = self.RADIUS

        # Gölge
        rounded_rect(self.canvas, 3, 3, s - 1, s - 1, r,
                      fill="#0a0a12", outline="")

        # Ana dikdörtgen
        rounded_rect(self.canvas, 0, 0, s - 4, s - 4, r,
                      fill=fill_color, outline="")

        fg = "#1e1e2e"

        # F tuşu etiketi (üst sol)
        self.canvas.create_text(
            14, 12,
            text=self.f_key.upper(),
            font=("Segoe UI", 9, "bold"),
            fill=fg, anchor="nw",
        )

        # Büyük emoji
        self.canvas.create_text(
            (s - 4) // 2, (s - 4) // 2 - 4,
            text=ACTION_ICONS.get(self.action, "?"),
            font=("Segoe UI Emoji", 30),
            fill=fg, anchor="center",
        )

        # Alt metin
        self.canvas.create_text(
            (s - 4) // 2, s - 22,
            text=ACTION_SHORT_NAMES.get(self.action, "?"),
            font=("Segoe UI", 10, "bold"),
            fill=fg, anchor="center",
        )

    def _on_enter(self, e):
        if not self._dragging and not self._hovered:
            self._hovered = True
            self._draw(self.color["hover"])

    def _on_leave(self, e):
        if not self._dragging and self._hovered:
            self._hovered = False
            self._draw(self.color["bg"])

    def _on_press(self, e):
        self._dragging = True
        self._drag_start_x = e.x_root
        self._drag_start_y = e.y_root
        self.on_drag_start(self)

    def _on_motion(self, e):
        pass  # Drag visual handled by ConfigWindow

    def _on_release(self, e):
        self._dragging = False
        self._draw(self.color["bg"])
        self.on_drag_end(self, e.x_root, e.y_root)

    def update_action(self, new_action):
        self.action = new_action
        self._draw(self.color["bg"])

    def highlight(self, on=True):
        """Sürükleme hedefi olarak vurgula."""
        if on:
            self.canvas.delete("all")
            s = self.SIZE
            r = self.RADIUS
            # Parlayan border efekti
            rounded_rect(self.canvas, 0, 0, s - 4, s - 4, r,
                          fill=self.color["hover"], outline="#cdd6f4")
            fg = "#1e1e2e"
            self.canvas.create_text(
                (s - 4) // 2, (s - 4) // 2 - 4,
                text="↕",
                font=("Segoe UI", 32, "bold"),
                fill=fg, anchor="center",
            )
            self.canvas.create_text(
                (s - 4) // 2, s - 22,
                text="Bırak",
                font=("Segoe UI", 10, "bold"),
                fill=fg, anchor="center",
            )
        else:
            self._draw(self.color["bg"])


class ConfigWindow:
    """Stream Deck tarzı tuş eşleme penceresi - sürükle-bırak destekli."""

    def __init__(self, on_save_callback=None):
        self.on_save_callback = on_save_callback
        self.root = None
        self.deck_buttons = {}
        self._drag_source = None
        self._drag_label = None
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

        # --- Başlık ---
        header = tk.Frame(self.root, bg=BG_COLOR)
        header.pack(fill="x", padx=24, pady=(18, 0))

        tk.Label(
            header, text="⌨  MiniKeyCtrl",
            font=("Segoe UI", 18, "bold"),
            bg=BG_COLOR, fg=TEXT_COLOR,
        ).pack(side="left")

        tk.Label(
            header, text="Sürükle & Bırak",
            font=("Segoe UI", 10),
            bg=BG_COLOR, fg=SUBTLE_COLOR,
        ).pack(side="right", pady=(8, 0))

        # Ayırıcı
        tk.Frame(self.root, bg=BORDER_COLOR, height=1).pack(fill="x", padx=24, pady=(12, 0))

        # --- Bilgi ---
        info_bar = tk.Frame(self.root, bg=BG_COLOR)
        info_bar.pack(fill="x", padx=24, pady=(10, 0))
        tk.Label(
            info_bar,
            text="💡 Tuşları sürükle-bırak ile yer değiştir  •  Tıkla ile fonksiyon seç",
            font=("Segoe UI", 9),
            bg=BG_COLOR, fg=SUBTLE_COLOR,
        ).pack(side="left")

        # --- 4x2 Grid ---
        grid_frame = tk.Frame(self.root, bg=BG_COLOR)
        grid_frame.pack(padx=20, pady=(12, 12))

        self.deck_buttons = {}

        for i, f_key in enumerate(F_KEYS):
            row = i // 4
            col = i % 4
            action = mappings.get(f_key, "mute")
            color = BUTTON_COLORS[i]

            deck_btn = DeckButton(
                grid_frame,
                index=i,
                f_key=f_key,
                action=action,
                color=color,
                grid_row=row,
                grid_col=col,
                on_drag_start=self._drag_start,
                on_drag_end=self._drag_end,
            )
            # Sağ tık menüsü - fonksiyon seçmek için
            deck_btn.canvas.bind("<Button-3>", lambda e, db=deck_btn: self._show_menu(e, db))

            self.deck_buttons[f_key] = deck_btn

        # Ayırıcı
        tk.Frame(self.root, bg=BORDER_COLOR, height=1).pack(fill="x", padx=24, pady=(2, 0))

        # --- Alt bar ---
        bottom = tk.Frame(self.root, bg=BG_COLOR)
        bottom.pack(fill="x", padx=24, pady=(12, 18))

        # Durum etiketi
        self.status_label = tk.Label(
            bottom,
            text="Hazır",
            font=("Segoe UI", 9),
            bg=BG_COLOR, fg=SUBTLE_COLOR,
        )
        self.status_label.pack(side="left")

        # Kaydet butonu
        save_btn = tk.Canvas(bottom, width=120, height=38, bg=BG_COLOR, highlightthickness=0)
        save_btn.pack(side="right")
        rounded_rect(save_btn, 0, 0, 118, 36, 10, fill="#a6e3a1", outline="")
        save_btn.create_text(60, 18, text="💾 KAYDET", font=("Segoe UI", 11, "bold"), fill="#1e1e2e")
        save_btn.bind("<Button-1>", lambda e: self._save())
        save_btn.bind("<Enter>", lambda e: (save_btn.delete("all"),
                      rounded_rect(save_btn, 0, 0, 118, 36, 10, fill="#94e2d5", outline=""),
                      save_btn.create_text(60, 18, text="💾 KAYDET", font=("Segoe UI", 11, "bold"), fill="#1e1e2e")))
        save_btn.bind("<Leave>", lambda e: (save_btn.delete("all"),
                      rounded_rect(save_btn, 0, 0, 118, 36, 10, fill="#a6e3a1", outline=""),
                      save_btn.create_text(60, 18, text="💾 KAYDET", font=("Segoe UI", 11, "bold"), fill="#1e1e2e")))
        save_btn.configure(cursor="hand2")

        # Pencere boyutu ve pozisyon
        btn_s = DeckButton.SIZE
        total_w = (btn_s * 4) + (6 * 8) + 52
        total_h = (btn_s * 2) + (6 * 2) + 190
        self.root.geometry(f"{total_w}x{total_h}")
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (total_w // 2)
        y = (self.root.winfo_screenheight() // 2) - (total_h // 2)
        self.root.geometry(f"+{x}+{y}")

        # Global motion tracking for drag highlight
        self.root.bind("<B1-Motion>", self._drag_motion)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    # --- Sürükle-Bırak ---

    def _drag_start(self, source_btn):
        """Sürükleme başladığında."""
        self._drag_source = source_btn
        self.status_label.configure(
            text=f"🔄 {source_btn.f_key.upper()} sürükleniyor... Hedef tuşa bırak",
            fg="#f9e2af",
        )
        # Kaynak butonu vurgula
        source_btn.canvas.delete("all")
        s = DeckButton.SIZE
        r = DeckButton.RADIUS
        rounded_rect(source_btn.canvas, 0, 0, s - 4, s - 4, r,
                      fill="#45475a", outline="#cdd6f4")
        source_btn.canvas.create_text(
            (s - 4) // 2, (s - 4) // 2,
            text="📦",
            font=("Segoe UI Emoji", 30),
            fill="#cdd6f4", anchor="center",
        )
        source_btn.canvas.create_text(
            (s - 4) // 2, s - 22,
            text=source_btn.f_key.upper(),
            font=("Segoe UI", 10, "bold"),
            fill="#cdd6f4", anchor="center",
        )

    def _drag_motion(self, e):
        """Sürükleme sırasında hedef butonu vurgula (sadece değişen butonları yeniden çizer)."""
        if not self._drag_source:
            return

        target = self._find_button_at(e.x_root, e.y_root)
        # Sadece hedef değiştiyse yeniden çiz
        if target == self._last_highlight_target:
            return

        # Önceki hedefi eski haline döndür
        if self._last_highlight_target and self._last_highlight_target != self._drag_source:
            self._last_highlight_target.highlight(False)

        # Yeni hedefi vurgula
        if target and target != self._drag_source:
            target.highlight(True)

        self._last_highlight_target = target

    def _drag_end(self, source_btn, x_root, y_root):
        """Sürükleme bırakıldığında."""
        if not self._drag_source:
            return

        target = self._find_button_at(x_root, y_root)

        # Tüm vurgulamaları kaldır
        for btn in self.deck_buttons.values():
            btn.highlight(False)

        if target and target != source_btn:
            # Swap actions
            src_action = source_btn.action
            tgt_action = target.action
            source_btn.update_action(tgt_action)
            target.update_action(src_action)
            self.status_label.configure(
                text=f"✅ {source_btn.f_key.upper()} ↔ {target.f_key.upper()} yer değiştirildi",
                fg="#a6e3a1",
            )
        else:
            # İptal - geri dön
            source_btn._draw(source_btn.color["bg"])
            self.status_label.configure(text="Hazır", fg=SUBTLE_COLOR)

        self._drag_source = None
        self._last_highlight_target = None

    def _find_button_at(self, x_root, y_root):
        """Ekran koordinatlarına göre buton bulur."""
        for fk, btn in self.deck_buttons.items():
            try:
                bx = btn.canvas.winfo_rootx()
                by = btn.canvas.winfo_rooty()
                bw = btn.canvas.winfo_width()
                bh = btn.canvas.winfo_height()
                if bx <= x_root <= bx + bw and by <= y_root <= by + bh:
                    return btn
            except Exception:
                pass
        return None

    # --- Sağ Tık Menüsü ---

    def _show_menu(self, event, deck_btn):
        """Sağ tıkla fonksiyon seçme menüsü."""
        menu = tk.Menu(self.root, tearoff=0, font=("Segoe UI", 11))
        menu.configure(bg="#1e1e2e", fg="#cdd6f4",
                       activebackground="#89b4fa", activeforeground="#1e1e2e")

        for action_key, action_name in MEDIA_ACTION_NAMES.items():
            icon = ACTION_ICONS.get(action_key, "")
            label = f"{icon}  {action_name}"
            menu.add_command(
                label=label,
                command=lambda db=deck_btn, ak=action_key: self._set_action(db, ak),
            )

        menu.post(event.x_root, event.y_root)

    def _set_action(self, deck_btn, action):
        deck_btn.update_action(action)
        self.status_label.configure(
            text=f"✏️ {deck_btn.f_key.upper()} → {ACTION_SHORT_NAMES[action]}",
            fg="#89b4fa",
        )

    # --- Kaydet ---

    def _save(self):
        config = load_config()
        new_mappings = {}
        for f_key, deck_btn in self.deck_buttons.items():
            new_mappings[f_key] = deck_btn.action

        config["mappings"] = new_mappings
        save_config(config)

        if self.on_save_callback:
            self.on_save_callback(new_mappings)

        self.status_label.configure(text="✅ Ayarlar kaydedildi!", fg="#a6e3a1")
        messagebox.showinfo("MiniKeyCtrl", "✅ Ayarlar kaydedildi!", parent=self.root)

    def _on_close(self):
        if self.root:
            self.root.destroy()
            self.root = None
