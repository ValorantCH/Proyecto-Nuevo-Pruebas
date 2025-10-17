from tkinter import ttk

class AppTheme:
    def __init__(self):
        self.colors = {
            "background": "#eceff4",
            "header_bg": "#3b4252",
            "text_primary": "#2e3440",
            "text_secondary": "#4c566a",
            "accent": "#8fbcbb",
            "accent2": "#81a1c1",
            "hover": "#4c566a"
        }
        self._configurar_estilos()
    
    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        # ---- Estilo General ----
        style.configure(".", 
                      background=self.colors["background"], 
                      foreground=self.colors["text_primary"])
        
        # ---- Encabezado ----
        style.configure("Header.TFrame", 
                      background=self.colors["header_bg"],
                      padding=30)
                      
        # Estilo para el texto del logo
        style.configure("Header.TLabel", 
                      background=self.colors["header_bg"],
                      foreground="#d8dee9")  
        
        # Botones de navegación
        style.configure("Nav.TButton",
                      foreground="#d8dee9",
                      background=self.colors["header_bg"],
                      padding=10,
                      borderwidth=0,
                      font=("Rubik", 10))
        style.map("Nav.TButton",
                background=[("active", self.colors["hover"])])
        
        # ---- Botones de Acción ----
        # Botón Primario (énfasis)
        style.configure("Primary.TButton",
                      foreground=self.colors["text_primary"],
                      background=self.colors["accent"],
                      padding=10,
                      font=("Rubik", 10, "bold"),
                      borderwidth=0)
        style.map("Primary.TButton",
                      background=[("active", self.colors["accent2"])])
        
        # Botón Secundario (sin fondo, solo borde)
        style.configure("Secondary.TButton",
                      foreground=self.colors["text_primary"],
                      background=self.colors["background"],
                      bordercolor=self.colors["text_primary"],
                      borderwidth=0.5,
                      font=("Rubik", 10, "bold"),
                      relief="solid",
                      padding=6)
        style.map("Secondary.TButton",
                      foreground=[("active", self.colors["hover"])],
                      background=[("active", self.colors["background"])],
                      bordercolor=[("active", self.colors["hover"])])
        
