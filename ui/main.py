import tkinter as tk
from tkinter import ttk, font
from ui.styles import AppTheme
from ui.components.header import Header

class MainWindow:
    def __init__(self, root, rol_usuario):
        self.rol_usuario = rol_usuario

        self.root = root
        self.theme = AppTheme()
        self.root.title("Gestor de Ventas")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)

        self.header_font = font.Font(family="Helvetica", size=16, weight="bold")

        self.header = Header(
            self.root,
            current_screen="inicio",
            on_nav_click=self.cambiar_pantalla,
            rol_usuario=self.rol_usuario
        )
        self.header.pack(fill=tk.X, side=tk.TOP)

        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.pantalla_actual = None
        self.mostrar_pantalla_inicio()

    def cambiar_pantalla(self, clave_pantalla):

        if self.pantalla_actual:
            self.pantalla_actual.destroy()

        if clave_pantalla == "inicio":
            self.mostrar_pantalla_inicio()
        elif clave_pantalla == "ventas":
            from ui.punto_venta import PantallaVentas
            self.pantalla_actual = PantallaVentas(self.main_container)
        elif clave_pantalla == "inventario":
            from ui.inventario import PantallaInventario
            self.pantalla_actual = PantallaInventario(self.main_container)
        elif clave_pantalla == "clientes":
            from ui.clientes import PantallaClientes
            self.pantalla_actual = PantallaClientes(self.main_container)
        elif clave_pantalla == "transacciones":
            from ui.transacciones import PantallaTransacciones
            self.pantalla_actual = PantallaTransacciones(self.main_container)
        elif clave_pantalla == "movimientos":
            from ui.movimientos import PantallaMovimientos
            self.pantalla_actual = PantallaMovimientos(self.main_container)

        if self.pantalla_actual:
            self.pantalla_actual.pack(fill=tk.BOTH, expand=True)

    def mostrar_pantalla_inicio(self):
        self.pantalla_actual = ttk.Frame(self.main_container)

        lbl = ttk.Label(
            self.pantalla_actual,
            text=f"Bienvenido ({self.rol_usuario.upper()})",
            font=self.header_font,
            foreground=self.theme.colors["text_primary"]
        )
        lbl.pack(pady=100)

        self.pantalla_actual.pack(fill=tk.BOTH, expand=True)


def start_main_window(rol):
    root = tk.Tk()
    MainWindow(root, rol)
    root.mainloop()
