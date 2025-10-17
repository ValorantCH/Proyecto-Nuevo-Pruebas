import tkinter as tk
from tkinter import ttk, messagebox
from db.db import ejecutar_query, obtener_datos

class DialogoDireccion(tk.Toplevel):
    TIPOS_DIRECCION = ['Casa', 'Oficina', 'Sucursal', 'Otro']
    
    def __init__(self, parent, callback_actualizar):
        super().__init__(parent)
        self.callback_actualizar = callback_actualizar
        self.title("Registrar Dirección")
        self.clientes = self._obtener_clientes()
        self._inicializar_ui()

    def _obtener_clientes(self):
        return obtener_datos(
            "SELECT id_cliente, nombres || ' ' || apellido_p as nombre FROM Clientes WHERE estado = 1"
        )

    def _inicializar_ui(self):
        contenido = ttk.Frame(self, padding=10)
        contenido.pack(fill=tk.BOTH, expand=True)
        
        # Combobox para selección de cliente
        ttk.Label(contenido, text="Cliente:").grid(row=0, column=0, sticky=tk.W)
        self.combo_cliente = ttk.Combobox(
            contenido, 
            values=[f"{c[0]} - {c[1]}" for c in self.clientes],
            state="readonly"
        )
        self.combo_cliente.grid(row=0, column=1, sticky=tk.EW, pady=5)
        
        # Campos de dirección
        campos = [
            ('calle', 'Calle:', 1),
            ('numero_domicilio', 'Número:', 2),
            ('colonia', 'Colonia:', 3),
            ('ciudad', 'Ciudad:', 4),
            ('entidad', 'Estado:', 5),
            ('codigo_postal', 'Código Postal:', 6),
            ('tipo', 'Tipo:', 7),
            ('principal', 'Principal:', 8),
            ('referencias', 'Referencias:', 9)
        ]
        
        self.entries = {}
        
        for campo, etiqueta, fila in campos:
            ttk.Label(contenido, text=etiqueta).grid(row=fila, column=0, sticky=tk.W)
            
            if campo == 'tipo':
                entry = ttk.Combobox(contenido, values=self.TIPOS_DIRECCION, state="readonly")
                entry.current(0)
            elif campo == 'principal':
                entry = ttk.Combobox(contenido, values=['Sí', 'No'], state="readonly")
                entry.current(1)
            elif campo == 'referencias':
                entry = tk.Text(contenido, height=4, width=30)
            else:
                entry = ttk.Entry(contenido)
            
            entry.grid(row=fila, column=1, sticky=tk.EW, pady=2)
            self.entries[campo] = entry

        # Botones
        btn_frame = ttk.Frame(contenido)
        btn_frame.grid(row=10, columnspan=2, pady=10)
        
        ttk.Button(
            btn_frame,
            text="Guardar Dirección",
            command=self._guardar_direccion
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Cancelar",
            command=self.destroy
        ).pack(side=tk.RIGHT, padx=5)

    def _validar_codigo_postal(self, codigo):
        if codigo and (not codigo.isdigit() or len(codigo) != 5):
            raise ValueError("Código postal debe tener 5 dígitos numéricos")

    def _guardar_direccion(self):
        try:
            # Obtener ID del cliente seleccionado
            cliente_str = self.combo_cliente.get()
            if not cliente_str:
                raise ValueError("Debe seleccionar un cliente")
            
            cliente_id = int(cliente_str.split(" - ")[0])
            
            # Recolectar datos
            datos = {
                'calle': self.entries['calle'].get().strip(),
                'numero': self.entries['numero_domicilio'].get().strip(),
                'colonia': self.entries['colonia'].get().strip(),
                'ciudad': self.entries['ciudad'].get().strip(),
                'entidad': self.entries['entidad'].get().strip(),
                'codigo_postal': self.entries['codigo_postal'].get().strip(),
                'tipo': self.entries['tipo'].get(),
                'principal': 1 if self.entries['principal'].get() == 'Sí' else 0,
                'referencias': self.entries['referencias'].get("1.0", tk.END).strip()
            }
            
            # Validaciones
            if not datos['calle'] or not datos['colonia']:
                raise ValueError("Calle y Colonia son campos obligatorios")
                
            self._validar_codigo_postal(datos['codigo_postal'])
            
            # Insertar dirección
            ejecutar_query(
                """INSERT INTO Direcciones (
                    id_cliente, calle, numero_domicilio, colonia, ciudad, 
                    entidad, codigo_postal, tipo, principal, referencias
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    cliente_id,
                    datos['calle'],
                    datos['numero'],
                    datos['colonia'],
                    datos['ciudad'],
                    datos['entidad'],
                    datos['codigo_postal'],
                    datos['tipo'],
                    datos['principal'],
                    datos['referencias']
                )
            )
            
            messagebox.showinfo("Éxito", "Dirección registrada exitosamente")
            self.callback_actualizar()
            self.destroy()
            
        except ValueError as e:
            messagebox.showwarning("Validación fallida", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar dirección: {str(e)}")