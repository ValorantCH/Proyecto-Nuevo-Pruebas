import tkinter as tk
from tkinter import ttk, font
from ui.styles import AppTheme
from ui.components.header import Header

class MainWindow:
    def __init__(self, root, usuario, on_logout):
        self.root = root
        self.usuario = usuario
        self.on_logout = on_logout
        self.theme = AppTheme()
        
        self.root.title(f"Gestor de Ventas - Sesión: {self.usuario}")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # --- ROLES Y PERMISOS ---
        if self.usuario == "admin":
            # Admin tiene acceso al Dashboard
            self.permisos = ["dashboard", "ventas", "inventario", "clientes", "transacciones", "movimientos"]
        elif self.usuario == "vendedor":
            self.permisos = ["ventas", "clientes", "transacciones"]
        else:
            self.permisos = []

        self.header_font = font.Font(family="Helvetica", size=16, weight="bold")
        
        # ========== Encabezado ==========
        self.header = Header(
            self.root,
            current_screen="inicio",
            on_nav_click=self.cambiar_pantalla,
            on_logout=self.on_logout,
            usuario=self.usuario,
            permisos=self.permisos
        )
        self.header.pack(fill=tk.X, side=tk.TOP)
        
        # ========== Contenedor principal ==========
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Pantalla inicial
        self.pantalla_actual = None
        self.mostrar_pantalla_inicio()

    def cambiar_pantalla(self, clave_pantalla):
        if clave_pantalla != "inicio" and clave_pantalla not in self.permisos:
            return 

        if self.pantalla_actual:
            self.pantalla_actual.destroy()
        
        if clave_pantalla == "inicio":
            self.mostrar_pantalla_inicio()
        elif clave_pantalla == "dashboard": # <--- NUEVO
            from .dashboard import PantallaDashboard
            self.pantalla_actual = PantallaDashboard(self.main_container)
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
        
        if self.pantalla_actual and clave_pantalla != "inicio":
            self.pantalla_actual.pack(fill=tk.BOTH, expand=True)

    def mostrar_pantalla_inicio(self):
        self.pantalla_actual = tk.Frame(self.main_container, bg="#ECEFF4")
        self.pantalla_actual.pack(fill=tk.BOTH, expand=True)

        welcome_frame = tk.Frame(self.pantalla_actual, bg="#ECEFF4")
        welcome_frame.pack(pady=(40, 20))

        lbl_saludo = tk.Label(
            welcome_frame,
            text=f"¡Hola, {self.usuario.capitalize()}!",
            font=("Helvetica", 28, "bold"),
            bg="#ECEFF4",
            fg="#2E3440"
        )
        lbl_saludo.pack()

        lbl_desc = tk.Label(
            welcome_frame,
            text="Panel de Control General",
            font=("Helvetica", 14),
            bg="#ECEFF4",
            fg="#4C566A"
        )
        lbl_desc.pack(pady=5)

        grid_frame = tk.Frame(self.pantalla_actual, bg="#ECEFF4")
        grid_frame.pack(expand=True)

        # AGREGADO: Botón Dashboard
        todos_los_botones = [
            ("Dashboard", "📊", "#ebcb8b", "dashboard"), # <--- Color Amarillo suave
            ("Punto de Venta", "🛒", "#A3BE8C", "ventas"),      
            ("Inventario", "📦", "#5E81AC", "inventario"),    
            ("Clientes", "👥", "#D08770", "clientes"),        
            ("Transacciones", "📄", "#B48EAD", "transacciones"), 
            ("Movimientos", "⇄", "#88C0D0", "movimientos"),   
        ]

        botones_visibles = [b for b in todos_los_botones if b[3] in self.permisos]

        for i, (texto, icono, color, clave) in enumerate(botones_visibles):
            fila = i // 3
            col = i % 3
            self.crear_tarjeta_acceso(
                grid_frame, 
                texto, 
                icono, 
                color, 
                lambda c=clave: self.cambiar_pantalla(c)
            ).grid(row=fila, column=col, padx=20, pady=20)

    def crear_tarjeta_acceso(self, parent, texto, icono, color_bg, comando):
        btn = tk.Button(
            parent,
            text=f"{icono}\n\n{texto}",
            font=("Helvetica", 14, "bold"),
            bg=color_bg,
            fg="white",
            activebackground=color_bg,
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            width=18,
            height=7,
            command=comando,
            bd=0
        )
        
        def on_enter(e): btn.config(bg=self.ajustar_brillo(color_bg, -20))
        def on_leave(e): btn.config(bg=color_bg)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def ajustar_brillo(self, hex_color, factor):
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        r = max(0, min(255, r + factor))
        g = max(0, min(255, g + factor))
        b = max(0, min(255, b + factor))
        return f"#{r:02x}{g:02x}{b:02x}"