import tkinter as tk
from tkinter import ttk
from ui.styles import AppTheme

class Header(ttk.Frame):
    def __init__(self, parent, current_screen, on_nav_click, rol_usuario):
        super().__init__(parent, style="Header.TFrame")
        self.on_nav_click = on_nav_click
        self.rol_usuario = rol_usuario

        ttk.Label(
            self,
            text="Ventas",
            style="Header.TLabel",
            font=("Rubik", 14, "bold"),
            foreground="#d8dee9"
        ).pack(side="left", padx=20)

        nav_frame = ttk.Frame(self, style="Header.TFrame")
        nav_frame.pack(side="right", padx=20)

        # PERMISOS POR ROL
        permisos = {
            "admin": ["inicio", "ventas", "inventario", "clientes", "transacciones", "movimientos"],
            "inventario": ["inicio", "inventario", "movimientos"],
            "ventas": ["inicio", "ventas", "clientes"]
        }

        nav_buttons = [
            ("Inicio", "inicio"),
            ("Ventas", "ventas"),
            ("Inventario", "inventario"),
            ("Clientes", "clientes"),
            ("Transacciones", "transacciones"),
            ("Movimientos", "movimientos")
        ]

        botones_permitidos = permisos[self.rol_usuario]

        for text, screen_key in nav_buttons:
            if screen_key in botones_permitidos:
                ttk.Button(
                    nav_frame,
                    text=text,
                    style="Nav.TButton",
                    command=lambda sk=screen_key: self.on_nav_click(sk)
                ).pack(side="left", padx=12)
