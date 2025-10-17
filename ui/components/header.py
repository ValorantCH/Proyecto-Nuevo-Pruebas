from tkinter import ttk
from ui.styles import AppTheme

class Header(ttk.Frame):
    def __init__(self, parent, current_screen, on_nav_click):
        super().__init__(parent, style="Header.TFrame")
        self.theme = AppTheme()
        self.on_nav_click = on_nav_click
        
        # Logo
        ttk.Label(
            self,
            text="Ventas",
            style="Header.TLabel",
            font=("Rubik", 14, "bold"),
            foreground="#d8dee9"
        ).pack(side="left", padx=20)
        
        # Navegación (derecha)
        nav_frame = ttk.Frame(self, style="Header.TFrame")
        nav_frame.pack(side="right", padx=20)
        
        # Botones de navegación
        nav_buttons = [
            ("Inicio", "inicio"),
            ("Ventas", "ventas"),
            ("Inventario", "inventario"),
            ("Clientes", "clientes"),
            ("Transacciones", "transacciones"),
            ("Movimientos", "movimientos")
        ]
        
        for text, screen_key in nav_buttons:
            btn = ttk.Button(
                nav_frame,
                text=text,
                style="Nav.TButton",
                command=lambda sk=screen_key: self.on_nav_click(sk)
            )
            btn.pack(side="left", padx=12)