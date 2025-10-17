import tkinter as tk
from tkinter import ttk, messagebox
import re
from db.db import ejecutar_query

class DialogoProveedor(tk.Toplevel):
    """
    Diálogo para registro completo de proveedores con validaciones avanzadas
    
    Atributos:
        parent (tk.Widget): Ventana padre
        callback_actualizar (function): Función para actualizar listas principales
        entries (dict): Diccionario con los campos del formulario
    """
    
    def __init__(self, parent, callback_actualizar):
        super().__init__(parent)
        self.callback_actualizar = callback_actualizar
        self.title("Nuevo Proveedor")
        self.geometry("500x550")
        self._crear_widgets()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._cerrar_dialogo)

    def _crear_widgets(self):
        """Construye la interfaz con todos los campos requeridos"""
        contenido = ttk.Frame(self, padding=10)
        contenido.pack(fill=tk.BOTH, expand=True)
        
        # Configurar grid responsivo
        contenido.columnconfigure(1, weight=1)
        
        # Lista de campos con etiquetas y validaciones
        campos = [
            ('nombre', "Nombre*:", True, 0),
            ('rfc', "RFC:", False, 1),
            ('calle', "Calle:", False, 2),
            ('numero_domicilio', "Número:", False, 3),
            ('colonia', "Colonia:", False, 4),
            ('ciudad', "Ciudad:", False, 5),
            ('entidad', "Estado/Provincia:", False, 6),
            ('codigo_postal', "Código Postal:", False, 7),
            ('telefono', "Teléfono:", False, 8),
            ('correo', "Correo:", False, 9)
        ]
        
        self.entries = {}
        
        # Crear campos dinámicamente
        for campo, etiqueta, requerido, fila in campos:
            ttk.Label(contenido, text=etiqueta).grid(row=fila, column=0, sticky=tk.W, pady=2)
            entry = ttk.Entry(contenido)
            entry.grid(row=fila, column=1, sticky=tk.EW, pady=2)
            self.entries[campo] = entry
        
        # Botones
        btn_frame = ttk.Frame(contenido)
        btn_frame.grid(row=10, column=0, columnspan=2, pady=15)
        
        ttk.Button(
            btn_frame,
            text="Guardar",
            style="Primary.TButton",
            command=self._validar_proveedor
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Cancelar",
            command=self._cerrar_dialogo
        ).pack(side=tk.RIGHT, padx=5)

    def _validar_proveedor(self):
        """Ejecuta todas las validaciones antes de guardar"""
        try:
            datos = self._obtener_datos()
            self._validar_campos_obligatorios(datos)
            self._validar_formato_rfc(datos['rfc'])
            self._validar_email(datos['correo'])
            self._validar_telefono(datos['telefono'])
            self._guardar_proveedor(datos)
        except ValueError as e:
            messagebox.showwarning("Validación fallida", str(e), parent=self)

    def _obtener_datos(self):
        """Recolecta y sanitiza los datos del formulario"""
        return {
            'nombre': self.entries['nombre'].get().strip(),
            'rfc': self.entries['rfc'].get().strip().upper() or None,
            'calle': self.entries['calle'].get().strip() or None,
            'numero_domicilio': self.entries['numero_domicilio'].get().strip() or None,
            'colonia': self.entries['colonia'].get().strip() or None,
            'ciudad': self.entries['ciudad'].get().strip() or None,
            'entidad': self.entries['entidad'].get().strip() or None,
            'codigo_postal': self.entries['codigo_postal'].get().strip() or None,
            'telefono': self.entries['telefono'].get().strip() or None,
            'correo': self.entries['correo'].get().strip().lower() or None
        }

    def _validar_campos_obligatorios(self, datos):
        """Valida campos requeridos"""
        if not datos['nombre']:
            raise ValueError("El nombre del proveedor es obligatorio")

    def _validar_formato_rfc(self, rfc):
        """Valida formato básico de RFC (opcional)"""
        if rfc and len(rfc) not in (12, 13):
            raise ValueError("El RFC debe tener 12 o 13 caracteres")

    def _validar_email(self, email):
        """Valida formato de correo electrónico con regex"""
        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Formato de correo electrónico inválido")

    def _validar_telefono(self, telefono):
        """Valida que el teléfono contenga solo números"""
        if telefono and not telefono.isdigit():
            raise ValueError("El teléfono solo debe contener números")

    def _guardar_proveedor(self, datos):
        """Ejecuta la inserción en la base de datos"""
        try:
            ejecutar_query(
                """INSERT INTO Proveedores (
                    nombre, rfc, calle, numero_domicilio, colonia, ciudad,
                    entidad, codigo_postal, telefono, correo, fecha_registro, estado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), 1)""",
                tuple(datos.values())
            )
            self.callback_actualizar()
            self._cerrar_dialogo()
            messagebox.showinfo("Éxito", "Proveedor registrado correctamente", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"Error en base de datos:\n{str(e)}", parent=self)

    def _cerrar_dialogo(self):
        """Cierra la ventana limpiamente"""
        self.destroy()