import tkinter as tk
from tkinter import ttk, messagebox

# Usuarios de texto plano
USERS = {
    "admin": {"password": "123", "rol": "admin"},
    "inventario": {"password": "123", "rol": "inventario"},
    "ventas": {"password": "123", "rol": "ventas"}
}

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Inicio de Sesión")
        self.geometry("350x250")
        self.resizable(False, False)

        self.intentos_restantes = 3

        ttk.Label(self, text="Usuario:").pack(pady=10)
        self.entry_user = ttk.Entry(self)
        self.entry_user.pack()

        ttk.Label(self, text="Contraseña:").pack(pady=10)
        self.entry_pass = ttk.Entry(self, show="*")
        self.entry_pass.pack()

        ttk.Button(self, text="Ingresar", command=self.login).pack(pady=20)

    def login(self):
        user = self.entry_user.get().strip()
        psw = self.entry_pass.get().strip()

        if user in USERS and USERS[user]["password"] == psw:
            rol = USERS[user]["rol"]

            self.destroy()
            from ui.main import start_main_window
            start_main_window(rol)

        else:
            self.intentos_restantes -= 1

            if self.intentos_restantes > 0:
                messagebox.showerror(
                    "Error",
                    f"Credenciales incorrectas\nIntentos restantes: {self.intentos_restantes}"
                )
            else:
                messagebox.showerror("Bloqueado", "Se agotaron los 3 intentos")
                self.destroy()
                exit()
