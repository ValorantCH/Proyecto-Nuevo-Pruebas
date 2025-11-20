import tkinter as tk
from ui.main import MainWindow
from ui.login import LoginWindow

# Variable global para mantener la referencia de la app principal
app = None

def cerrar_sesion():
    """
    Limpia la interfaz actual y vuelve a mostrar el Login.
    """
    global root
    
    # 1. Ocultamos la ventana principal
    root.withdraw()
    
    # 2. Limpiamos todos los widgets que MainWindow agregó al root
    # Esto es importante para que al volver a entrar no se dupliquen cosas
    for widget in root.winfo_children():
        if isinstance(widget, tk.Toplevel):
            # Si hay ventanas flotantes abiertas, las cerramos
            widget.destroy()
        else:
            # Destruimos el contenido (Header, Contenedor Principal)
            widget.destroy()

    # 3. Abrimos el Login de nuevo
    LoginWindow(root, on_login_success=iniciar_aplicacion)

def iniciar_aplicacion(usuario):
    """
    Se ejecuta cuando el login es exitoso.
    """
    global app
    
    # Mostramos la ventana root (que ahora está vacía tras el login)
    root.deiconify()
    
    # Instanciamos la ventana principal pasándole la función de cerrar sesión
    app = MainWindow(root, usuario, on_logout=cerrar_sesion)

if __name__ == "__main__":
    root = tk.Tk()
    
    # 1. Ocultamos la ventana principal al inicio
    root.withdraw()
    
    # 2. Abrimos el Login
    LoginWindow(root, on_login_success=iniciar_aplicacion)
    
    # 3. Iniciamos el bucle
    root.mainloop()