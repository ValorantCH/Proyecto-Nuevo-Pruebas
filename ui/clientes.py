import tkinter as tk
from tkinter import ttk, messagebox
from threading import Timer
from db.db import obtener_datos, ejecutar_query
from ui.styles import AppTheme
from utils.helpers import get_inactive_color  
from ui.dialogos.dialogo_clientes import DialogoCliente 
from ui.dialogos.dialogo_direccion import DialogoDireccion 

class PantallaClientes(ttk.Frame):
    COLUMNAS = {
        'Principal': [
            ('id_cliente', 'ID', 60),
            ('nombre_completo', 'Nombre', 250),
            ('tipo_persona', 'Tipo', 150),
            ('direccion_principal', 'Dirección', 200),
            ('correo', 'Correo', 200),
            ('telefono', 'Teléfono', 150),
            ('fecha_registro', 'Fecha Registro', 150),
            ('estado', 'Estado', 100),
        ]
    }
    
    ESTADOS = {
        1: 'Activo',
        0: 'Inactivo'
    }
    
    CAMPOS_BUSQUEDA = ['c.nombres', 'c.apellido_p', 'c.apellido_m', 'c.rfc']  
    def __init__(self, parent):
        super().__init__(parent)
        self.theme = AppTheme()
        self.datos = []
        self.filtros = {
            'busqueda': '',
            'estado': 'Todos',
        }
        self.orden = {'columna': None, 'ascendente': True}
        
        self._inicializar_ui()
        self._cargar_datos()

    def _inicializar_ui(self):
        self._crear_controles()
        self._configurar_tabla()
        self._actualizar_boton_estado()

    def _crear_controles(self):
        self.controles_frame = ttk.Frame(self)
        self.controles_frame.pack(fill=tk.X, padx=10, pady=10)

        # Búsqueda
        ttk.Label(self.controles_frame, text="Buscar:").pack(side=tk.LEFT)
        self.entrada_busqueda = ttk.Entry(self.controles_frame)
        self.entrada_busqueda.pack(side=tk.LEFT, padx=5)
        self.entrada_busqueda.bind("<KeyRelease>", lambda e: self._aplicar_debounce_filtros())

        # Filtro Estado
        ttk.Label(self.controles_frame, text="Estado:").pack(side=tk.LEFT, padx=(15, 0))
        self.combo_estado = ttk.Combobox(
            self.controles_frame,
            values=["Todos", self.ESTADOS[0], self.ESTADOS[1]],
            state="readonly"
        )
        self.combo_estado.set("Todos")
        self.combo_estado.pack(side=tk.LEFT, padx=5)
        self.combo_estado.bind("<<ComboboxSelected>>", lambda e: self._aplicar_filtros())

        # Botones
        self.btn_estado = ttk.Button(
            self.controles_frame,
            text="Activar/Inactivar",
            style="Secondary.TButton",
            command=self._cambiar_estado_cliente,
            state="disabled"
        )
        self.btn_estado.pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            self.controles_frame,
            text="➕ Registrar Cliente",
            style="Primary.TButton",
            command=lambda: DialogoCliente(self, self._cargar_datos)
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            self.controles_frame,
            text="🏠 Agregar Dirección",
            style="Secondary.TButton",
            command=lambda: DialogoDireccion(self, self._cargar_datos)
        ).pack(side=tk.RIGHT, padx=5)

    def _configurar_tabla(self):
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL)

        self.tabla = ttk.Treeview(
            frame,
            columns=[col[0] for col in self.COLUMNAS['Principal']],
            show="headings",
            yscrollcommand=scrollbar.set,
            selectmode="browse"
        )

        for col in self.COLUMNAS['Principal']:
            self.tabla.heading(col[0], text=col[1], command=lambda c=col[0]: self._ordenar_por_columna(c))
            self.tabla.column(col[0], width=col[2], anchor=tk.CENTER)

        # Configurar color para inactivos
        self.tabla.tag_configure('inactivo', background=get_inactive_color())
        
        scrollbar.config(command=self.tabla.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tabla.pack(fill=tk.BOTH, expand=True)
        self.tabla.bind("<<TreeviewSelect>>", lambda e: self._actualizar_boton_estado())

    def _cargar_datos(self):
        try:
            query = """
                SELECT 
                    c.id_cliente,
                    c.nombres || ' ' || COALESCE(c.apellido_p, '') || ' ' || COALESCE(c.apellido_m, '') AS nombre_completo,
                    c.tipo_persona,
                    d.calle || ' ' || d.numero_domicilio AS direccion_principal,
                    c.correo,
                    c.telefono,
                    c.fecha_registro,
                    c.estado
                FROM Clientes c
                LEFT JOIN Direcciones d ON c.id_cliente = d.id_cliente AND d.principal = 1
                {where}
                ORDER BY {order_by}
            """.format(
                where=self._construir_where(),
                order_by=self._construir_orden()
            )
            
            parametros = []
            if self.filtros['busqueda']:
                parametros.extend([f"%{self.filtros['busqueda']}%"] * len(self.CAMPOS_BUSQUEDA))
            if self.filtros['estado'] != 'Todos':
                parametros.append(1 if self.filtros['estado'] == self.ESTADOS[1] else 0)
                
            self.datos = obtener_datos(query, parametros)
            
            self._actualizar_tabla()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando datos: {str(e)}")

    def _actualizar_tabla(self):
        self.tabla.delete(*self.tabla.get_children())
        for cliente in self.datos:
            estado = self.ESTADOS[cliente[7]]  
            direccion = cliente[3] or "Sin dirección"
            
            self.tabla.insert("", tk.END, values=(
                cliente[0],  # ID
                cliente[1],  # Nombre
                cliente[2],  # Tipo persona
                direccion,
                cliente[4],  # Correo
                cliente[5],  # Teléfono
                cliente[6],  # Fecha Registro
                estado
            ), tags=('inactivo',) if cliente[7] == 0 else ())

    def _cambiar_estado_cliente(self):
        seleccion = self.tabla.focus()
        if not seleccion:
            return
        
        cliente_id = self.tabla.item(seleccion, "values")[0]
        
        try:
            resultado = obtener_datos(
                "SELECT estado FROM Clientes WHERE id_cliente = ?",
                (cliente_id,)
            )
            
            if not resultado:
                messagebox.showerror("Error", "Cliente no encontrado")
                return
                
            current_estado = resultado[0][0]
            nuevo_estado = 0 if current_estado == 1 else 1
            
            if messagebox.askyesno("Confirmar", f"¿Cambiar estado a {self.ESTADOS[nuevo_estado]}?"):
                ejecutar_query(
                    "UPDATE Clientes SET estado = ? WHERE id_cliente = ?",
                    (nuevo_estado, cliente_id)
                )
                
                # 1. Quitar la selección ANTES de recargar
                self.tabla.selection_remove(seleccion)
                
                # 2. Recargar datos y actualizar tabla
                self._cargar_datos()
                
        except Exception as e:
            messagebox.showerror("Error", f"Error actualizando estado: {str(e)}")
    
    def _construir_where(self):
        condiciones = []
        if self.filtros['busqueda']:
            condiciones.append(" OR ".join([f"{campo} LIKE ?" for campo in self.CAMPOS_BUSQUEDA]))
        if self.filtros['estado'] != 'Todos':
            condiciones.append("c.estado = ?")
            
        return "WHERE " + " AND ".join(condiciones) if condiciones else ""

    def _construir_orden(self):
        if not self.orden['columna']:
            return "c.id_cliente ASC"  # Orden inicial ascendente
        return f"{self.orden['columna']} {'ASC' if self.orden['ascendente'] else 'DESC'}"
    
    def _aplicar_debounce_filtros(self):
        if hasattr(self, '_timer_filtro'):
            self._timer_filtro.cancel()
        self._timer_filtro = Timer(0.3, self._aplicar_filtros)
        self._timer_filtro.start()

    def _aplicar_filtros(self, event=None):
        self.filtros.update({
            'busqueda': self.entrada_busqueda.get().strip(),
            'estado': self.combo_estado.get(),
        })
        self._cargar_datos()

    def _ordenar_por_columna(self, columna):
        column_map = {
            'id_cliente': 'c.id_cliente',
            'nombre_completo': 'nombre_completo',  # Es un alias, no necesita 'c.'
            'tipo_persona': 'c.tipo_persona',
            'direccion_principal': 'direccion_principal',  # Alias de la consulta
            'estado': 'c.estado'
        }
        
        # Obtener columna mapeada
        nueva_columna = column_map.get(columna, 'c.id_cliente')
        
        # Si es la misma columna, invertir orden
        if self.orden['columna'] == nueva_columna:
            self.orden['ascendente'] = not self.orden['ascendente']
        else:
            self.orden['columna'] = nueva_columna
            self.orden['ascendente'] = True
        
        self._cargar_datos()

    def _actualizar_boton_estado(self):
        seleccion = self.tabla.focus()
        
        if not seleccion:
            self.btn_estado.config(state="disabled")
            return
            
        # Obtener valores de la fila seleccionada
        valores = self.tabla.item(seleccion, "values")
        
        # Verificar que hay datos y habilitar botón
        if valores:
            self.btn_estado.config(state="normal")
        else:
            self.btn_estado.config(state="disabled")

    def _abrir_dialogo_nuevo(self):
        DialogoCliente(self.dialogo, self.callback_actualizar)
