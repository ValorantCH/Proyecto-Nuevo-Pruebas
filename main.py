import tkinter as tk
from ui.main import MainWindow  # Importa la clase del menú

if __name__ == "__main__":
    root = tk.Tk()
    app = MainWindow(root)      # Crea la ventana principal
    root.mainloop()             # Inicia el bucle de Tkinter
