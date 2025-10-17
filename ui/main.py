import tkinter as tk
from tkinter import ttk, font
from ui.styles import AppTheme
from ui.components.header import Header
from ui.inventario import PantallaInventario

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.theme = AppTheme()
        self.root.title("Gestor de Ventas")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # Configurar fuente
        self.header_font = font.Font(
            family="Helvetica",
            size=16,
            weight="bold"
        )
        
        # ========== Encabezado ==========
        self.header = Header(
            self.root,
            current_screen="inicio",
            on_nav_click=self.cambiar_pantalla
        )
        self.header.pack(fill=tk.X, side=tk.TOP)
        
        # ========== Contenedor principal ==========
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Pantalla inicial
        self.pantalla_actual = None
        self.mostrar_pantalla_inicio()

    def cambiar_pantalla(self, clave_pantalla):
        """Cambia dinámicamente entre módulos"""
        # Destruir pantalla anterior
        if self.pantalla_actual:
            self.pantalla_actual.destroy()
        
        # Cargar nueva pantalla
        if clave_pantalla == "inicio":
            self.mostrar_pantalla_inicio()
        elif clave_pantalla == "ventas":
            from .punto_venta import PantallaVentas
            self.pantalla_actual = PantallaVentas(self.main_container)
        elif clave_pantalla == "inventario":
            from .inventario import PantallaInventario
            self.pantalla_actual = PantallaInventario(self.main_container)
        elif clave_pantalla == "clientes":
            from .clientes import PantallaClientes
            self.pantalla_actual = PantallaClientes(self.main_container)
        elif clave_pantalla == "transacciones":
            from .transacciones import PantallaTransacciones
            self.pantalla_actual = PantallaTransacciones(self.main_container)
        elif clave_pantalla == "movimientos":
            from .movimientos import PantallaMovimientos
            self.pantalla_actual = PantallaMovimientos(self.main_container)
        
        if self.pantalla_actual:
            self.pantalla_actual.pack(fill=tk.BOTH, expand=True)

    def mostrar_pantalla_inicio(self):
        """Pantalla de bienvenida"""
        self.pantalla_actual = ttk.Frame(self.main_container)
        lbl_titulo = ttk.Label(
            self.pantalla_actual,
            text="Bienvenido al Sistema de Gestión",
            font=self.header_font,
            foreground=self.theme.colors["text_primary"]
        )
        lbl_titulo.pack(pady=100)
        
        lbl_subtitulo = ttk.Label(
            self.pantalla_actual,
            text="Seleccione un módulo desde el menú superior",
            foreground=self.theme.colors["text_secondary"]
        )
        lbl_subtitulo.pack()
        self.pantalla_actual.pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()
