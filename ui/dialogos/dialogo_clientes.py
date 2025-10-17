import tkinter as tk
from tkinter import ttk, messagebox
import re
from db.db import ejecutar_query

class DialogoCliente(tk.Toplevel):
    def __init__(self, parent, actualizar_callback):
        super().__init__(parent)
        self.actualizar_callback = actualizar_callback
        self.title("Registrar Cliente")
        self._inicializar_ui()

    def _inicializar_ui(self):
        self.campos = [
            ('nombres', 'Nombres:'),
            ('apellido_p', 'Apellido Paterno:'),
            ('apellido_m', 'Apellido Materno:'), 
            ('tipo_persona', 'Tipo Persona:'),  
            ('rfc', 'RFC:'),
            ('correo', 'Correo:'),
            ('telefono', 'Teléfono:'),
            ('estado', 'Estado:')
        ]
        
        self.entries = {}
        for idx, (campo, etiqueta) in enumerate(self.campos):
            ttk.Label(self, text=etiqueta).grid(row=idx, column=0, padx=5, pady=5, sticky="e")
            
            if campo == 'tipo_persona':
                # Combobox para tipo de persona
                entry = ttk.Combobox(
                    self, 
                    values=["Física", "Moral"], 
                    state="readonly"
                )
                entry.current(0)  # Valor por defecto: Física
            elif campo == 'estado':
                entry = ttk.Combobox(self, values=['Activo', 'Inactivo'], state='readonly')
                entry.set('Activo')
            else:
                entry = ttk.Entry(self)
            
            entry.grid(row=idx, column=1, padx=5, pady=5, sticky="ew")
            self.entries[campo] = entry

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=len(self.campos)+1, columnspan=2, pady=10)
        
        ttk.Button(
            btn_frame,
            text="Guardar",
            command=self._guardar_cliente
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Cerrar",
            command=self.destroy
        ).pack(side=tk.RIGHT, padx=5)

    def _validar_rfc(self, rfc):
        if rfc and len(rfc) not in (12, 13):
            raise ValueError("El RFC debe tener 12 o 13 caracteres")

    def _validar_email(self, email):
        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Formato de correo electrónico inválido")

    def _guardar_cliente(self):
        datos = {
            'nombres': self.entries['nombres'].get().strip(),
            'apellido_p': self.entries['apellido_p'].get().strip(),
            'apellido_m': self.entries['apellido_m'].get().strip(), 
            'tipo_persona': self.entries['tipo_persona'].get().strip().capitalize(),
            'rfc': self.entries['rfc'].get().strip().upper(),
            'correo': self.entries['correo'].get().strip().lower(),
            'telefono': self.entries['telefono'].get().strip(),
            'estado': 1 if self.entries['estado'].get() == 'Activo' else 0
        }
        
        try:
            if not datos['nombres']:
                raise ValueError("El campo Nombres es obligatorio")
                
            if datos['tipo_persona'] not in ['Física', 'Moral']:
                raise ValueError("Tipo de persona debe ser 'Física' o 'Moral'")
                
            self._validar_rfc(datos['rfc'])
            self._validar_email(datos['correo'])
            
            ejecutar_query(
                """INSERT INTO Clientes 
                (nombres, apellido_p, apellido_m, tipo_persona, rfc, correo, telefono, estado, fecha_registro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",  
                tuple(datos.values())
            )
            
            messagebox.showinfo("Éxito", "Cliente registrado exitosamente")
            self.actualizar_callback()
            self.destroy()
            
        except ValueError as e:
            messagebox.showwarning("Validación fallida", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar cliente: {str(e)}")