import tkinter as tk
from tkinter import ttk, messagebox
from db.db import ejecutar_query

class DialogoCategoria(tk.Toplevel):
    """
    Diálogo para registro de categorías con validaciones
    
    Atributos:
        parent (tk.Widget): Ventana padre
        callback_actualizar (function): Función para actualizar listas principales
    """
    
    MAX_DESCRIPCION = 200  # Caracteres máximos para descripción
    
    def __init__(self, parent, callback_actualizar):
        super().__init__(parent)
        self.callback_actualizar = callback_actualizar
        self.title("Nueva Categoría")
        self.geometry("400x300")
        self._crear_widgets()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._cerrar_dialogo)

    def _crear_widgets(self):
        """Construye la interfaz con validaciones"""
        contenido = ttk.Frame(self, padding=10)
        contenido.pack(fill=tk.BOTH, expand=True)
        
        # Campo nombre
        ttk.Label(contenido, text="Nombre*:").grid(row=0, column=0, sticky=tk.W)
        self.entry_nombre = ttk.Entry(contenido)
        self.entry_nombre.grid(row=0, column=1, sticky=tk.EW, pady=5)
        
        # Campo descripción
        ttk.Label(contenido, text="Descripción:").grid(row=1, column=0, sticky=tk.NW)
        self.txt_descripcion = tk.Text(contenido, height=5, width=30)
        self.txt_descripcion.grid(row=1, column=1, sticky=tk.EW, pady=5)
        
        # Contador de caracteres
        self.lbl_contador = ttk.Label(contenido, text=f"Máximo {self.MAX_DESCRIPCION} caracteres")
        self.lbl_contador.grid(row=2, column=1, sticky=tk.E)
        
        # Botones
        btn_frame = ttk.Frame(contenido)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(
            btn_frame,
            text="Guardar",
            style="Primary.TButton",
            command=self._validar_categoria
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Cancelar",
            command=self._cerrar_dialogo
        ).pack(side=tk.RIGHT, padx=5)
        
        # Evento para el contador de caracteres
        self.txt_descripcion.bind("<KeyRelease>", self._actualizar_contador)

    def _validar_categoria(self):
        """Ejecuta todas las validaciones necesarias"""
        nombre = self.entry_nombre.get().strip()
        descripcion = self.txt_descripcion.get("1.0", tk.END).strip()
        
        try:
            if not nombre:
                raise ValueError("El nombre de la categoría es obligatorio")
            
            if len(descripcion) > self.MAX_DESCRIPCION:
                raise ValueError(f"Descripción excede máximo de {self.MAX_DESCRIPCION} caracteres")
            
            self._guardar_categoria(nombre, descripcion)
            
        except ValueError as e:
            messagebox.showwarning("Validación fallida", str(e), parent=self)

    def _guardar_categoria(self, nombre, descripcion):
        """Ejecuta la inserción en la base de datos"""
        try:
            ejecutar_query(
                "INSERT INTO Categorias (nombre, descripcion) VALUES (?, ?)",
                (nombre, descripcion or None)
            )
            self.callback_actualizar()
            self._cerrar_dialogo()
            messagebox.showinfo("Éxito", "Categoría creada exitosamente", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"Error en base de datos:\n{str(e)}", parent=self)

    def _actualizar_contador(self, event=None):
        """Actualiza el contador de caracteres en tiempo real"""
        contenido = self.txt_descripcion.get("1.0", tk.END)
        longitud = len(contenido.strip())
        self.lbl_contador.config(
            text=f"{longitud}/{self.MAX_DESCRIPCION} caracteres",
            foreground="red" if longitud > self.MAX_DESCRIPCION else "black"
        )

    def _cerrar_dialogo(self):
        """Cierra la ventana limpiamente"""
        self.destroy()