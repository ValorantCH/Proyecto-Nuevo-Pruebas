import tkinter as tk
from tkinter import ttk, messagebox

class LoginWindow(tk.Toplevel):
    def __init__(self, parent, on_login_success):
        super().__init__(parent)
        self.on_login_success = on_login_success
        
        # Configuración básica
        self.geometry("750x450")
        
        # --- ELIMINAR BORDES Y BARRA DE TÍTULO ---
        self.overrideredirect(True) 
        
        # Centrar ventana en pantalla
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_cordinate = int((screen_width/2) - (750/2))
        y_cordinate = int((screen_height/2) - (450/2))
        self.geometry(f"750x450+{x_cordinate}+{y_cordinate}")

        # Variables para el arrastre de ventana
        self.offset_x = 0
        self.offset_y = 0

        # Configurar estilos
        self.configure_styles()

        # Layout principal: Dos columnas
        # Lado Izquierdo: Branding / Decorativo
        self.left_frame = tk.Frame(self, bg="#2E3440", width=300)
        self.left_frame.pack(side="left", fill="y")
        self.left_frame.pack_propagate(False)

        # Contenido lado izquierdo
        tk.Label(
            self.left_frame, 
            text="🛒", 
            font=("Segoe UI", 80), 
            bg="#2E3440", 
            fg="#88C0D0"
        ).pack(pady=(100, 20))

        tk.Label(
            self.left_frame, 
            text="SISTEMA DE\nVENTAS", 
            font=("Helvetica", 20, "bold"), 
            bg="#2E3440", 
            fg="#ECEFF4",
            justify="center"
        ).pack()

        # --- TEXTO CAMBIADO ---
        tk.Label(
            self.left_frame, 
            text="Valorant Champagne 2025", 
            font=("Helvetica", 10, "italic"), 
            bg="#2E3440", 
            fg="#D8DEE9"
        ).pack(side="bottom", pady=20)

        # Lado Derecho: Formulario
        self.right_frame = tk.Frame(self, bg="#FFFFFF")
        self.right_frame.pack(side="right", fill="both", expand=True)

        # --- Botón de Cerrar (X) en la esquina superior derecha ---
        btn_close = tk.Button(
            self.right_frame,
            text="✕",
            font=("Arial", 12, "bold"),
            bg="#FFFFFF",
            fg="#4C566A",
            bd=0,
            cursor="hand2",
            activebackground="#BF616A",
            activeforeground="white",
            command=self.cerrar_aplicacion
        )
        btn_close.place(x=410, y=10) # Posición absoluta

        self.create_form()

        # --- EVENTOS PARA MOVER LA VENTANA (DRAG) ---
        # Permitir mover desde el panel izquierdo
        self.left_frame.bind("<Button-1>", self.click_ventana)
        self.left_frame.bind("<B1-Motion>", self.mover_ventana)
        
        # Permitir mover desde el panel derecho (fondo)
        self.right_frame.bind("<Button-1>", self.click_ventana)
        self.right_frame.bind("<B1-Motion>", self.mover_ventana)

    def configure_styles(self):
        style = ttk.Style()
        
        # Estilo Botón Ingresar
        style.configure(
            "Login.TButton", 
            font=("Helvetica", 11, "bold"), 
            background="#5E81AC", 
            foreground="black", 
            padding=10
        )

    def create_form(self):
        # Título
        lbl_titulo = tk.Label(
            self.right_frame, 
            text="Iniciar Sesión", 
            font=("Helvetica", 24, "bold"), 
            bg="#FFFFFF", 
            fg="#3B4252"
        )
        lbl_titulo.pack(pady=(50, 40))
        
        # Permitir mover ventana desde el título
        lbl_titulo.bind("<Button-1>", self.click_ventana)
        lbl_titulo.bind("<B1-Motion>", self.mover_ventana)

        # === Usuario ===
        user_frame = tk.Frame(self.right_frame, bg="#FFFFFF")
        user_frame.pack(pady=10, padx=50, fill="x")
        
        tk.Label(user_frame, text="👤", font=("Arial", 14), bg="#FFFFFF", fg="#88C0D0").pack(side="left", padx=5)
        
        self.user_var = tk.StringVar()
        self.entry_user = ttk.Entry(user_frame, textvariable=self.user_var, font=("Helvetica", 12))
        self.entry_user.pack(side="left", fill="x", expand=True, ipady=5)
        
        # === Contraseña ===
        pass_frame = tk.Frame(self.right_frame, bg="#FFFFFF")
        pass_frame.pack(pady=20, padx=50, fill="x")
        
        tk.Label(pass_frame, text="🔒", font=("Arial", 14), bg="#FFFFFF", fg="#88C0D0").pack(side="left", padx=5)
        
        self.pass_var = tk.StringVar()
        self.entry_pass = ttk.Entry(pass_frame, textvariable=self.pass_var, font=("Helvetica", 12), show="•")
        self.entry_pass.pack(side="left", fill="x", expand=True, ipady=5)

        self.entry_pass.bind('<Return>', lambda event: self.validar())
        
        self.entry_user.focus()

        # === Botones ===
        btn_frame = tk.Frame(self.right_frame, bg="#FFFFFF")
        btn_frame.pack(pady=40, fill="x", padx=50)

        btn_login = ttk.Button(
            btn_frame, 
            text="INGRESAR ➔", 
            style="Login.TButton", 
            cursor="hand2",
            command=self.validar
        )
        btn_login.pack(fill="x", pady=5)
        
        # Se eliminó el botón SALIR de aquí

    # --- FUNCIONES LÓGICAS ---

    def click_ventana(self, event):
        """Guarda la posición del mouse al hacer click"""
        self.offset_x = event.x
        self.offset_y = event.y

    def mover_ventana(self, event):
        """Mueve la ventana al arrastrar"""
        new_x = self.winfo_pointerx() - self.offset_x
        new_y = self.winfo_pointery() - self.offset_y
        self.geometry(f"+{new_x}+{new_y}")

    def cerrar_aplicacion(self):
        """Cierra toda la aplicación"""
        self.quit()

    def validar(self):
        usuario = self.user_var.get()
        password = self.pass_var.get()

        # LOGIN TEXTO PLANO
        if usuario == "admin" and password == "1234":
            self.on_login_success(usuario)
            self.destroy()
        elif usuario == "vendedor" and password == "1234":
            self.on_login_success(usuario)
            self.destroy()
        else:
            messagebox.showerror("Error de Acceso", "Usuario o contraseña incorrectos.")
            self.user_var.set("")
            self.pass_var.set("")
            self.entry_user.focus()