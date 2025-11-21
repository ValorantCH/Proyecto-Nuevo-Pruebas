import tkinter as tk
from tkinter import ttk
from ui.styles import AppTheme

class Header(ttk.Frame):
    def __init__(self, parent, current_screen, on_nav_click, on_logout, usuario="", permisos=None):
        super().__init__(parent, style="Header.TFrame")
        self.theme = AppTheme()
        self.on_nav_click = on_nav_click
        self.on_logout = on_logout
        self.usuario = usuario
        self.permisos = permisos or []
        
        self.columnconfigure(1, weight=1)

        # Logo
        logo_frame = ttk.Frame(self, style="Header.TFrame")
        logo_frame.pack(side="left", padx=20)
        ttk.Label(logo_frame, text="🛒 Ventas", style="Header.TLabel", font=("Helvetica", 16, "bold"), foreground="#ECEFF4").pack(side="left")

        # Navegación
        nav_frame = ttk.Frame(self, style="Header.TFrame")
        nav_frame.pack(side="left", padx=40)
        
        nav_buttons = [
            ("Inicio", "inicio"),
            ("Dashboard", "dashboard"), # <--- NUEVO
            ("Ventas", "ventas"),
            ("Inventario", "inventario"),
            ("Clientes", "clientes"),
            ("Transacciones", "transacciones"),
            ("Movimientos", "movimientos")
        ]
        
        for text, screen_key in nav_buttons:
            if screen_key == "inicio" or screen_key in self.permisos:
                btn = ttk.Button(
                    nav_frame,
                    text=text,
                    style="Nav.TButton",
                    command=lambda sk=screen_key: self.on_nav_click(sk)
                )
                btn.pack(side="left", padx=5)

        # Info Usuario
        user_frame = ttk.Frame(self, style="Header.TFrame")
        user_frame.pack(side="right", padx=20)

        ttk.Label(user_frame, text=f"👤 {self.usuario}", font=("Helvetica", 10), foreground="#88C0D0", background="#2E3440").pack(side="left", padx=(0, 15))
        
        tk.Button(
            user_frame, text="Salir ➔", font=("Helvetica", 9, "bold"), bg="#BF616A", fg="white", bd=0, padx=10, pady=2, cursor="hand2",
            command=self.on_logout
        ).pack(side="left")