import tkinter as tk
from tkinter import ttk
from datetime import datetime
from tkinter import messagebox
from db.db import obtener_datos, ejecutar_query
from ui.styles import AppTheme

class PantallaTransacciones(ttk.Frame):
    COLUMNAS = {
        'Principal': [
            ('id_transaccion', 'ID', 60),
            ('fecha', 'Fecha', 150),
            ('tipo', 'Tipo', 100),
            ('cliente', 'Cliente', 200),
            ('medio_pago', 'Medio Pago', 150),
            ('subtotal', 'Subtotal', 100),
            ('impuestos', 'Impuestos', 100),
            ('total', 'Total', 120),
            ('estado', 'Estado', 100)
        ]
    }

    def __init__(self, parent):
        super().__init__(parent)
        self.theme = AppTheme()
        self.datos = []
        self.filtros = {
            'tipo': 'Todos',
            'estado': 'Todos',
            'fecha_inicio': '',
            'fecha_fin': ''
        }
        
        self._inicializar_ui()
        self._cargar_datos()

    def _inicializar_ui(self):
        self._crear_controles_filtro()
        self._configurar_tabla()
        self._crear_botones_accion()

    def _crear_controles_filtro(self):
        controles_frame = ttk.Frame(self)
        controles_frame.pack(fill=tk.X, padx=10, pady=10)

        # Filtro por tipo
        ttk.Label(controles_frame, text="Tipo:").grid(row=0, column=0, sticky=tk.W)
        self.combo_tipo = ttk.Combobox(
            controles_frame,
            values=["Todos", "venta", "compra", "devolucion"],
            state="readonly"
        )
        self.combo_tipo.set("Todos")
        self.combo_tipo.grid(row=0, column=1, padx=5, sticky=tk.W)
        self.combo_tipo.bind("<<ComboboxSelected>>", lambda e: self._aplicar_filtros())

        # Filtro por estado
        ttk.Label(controles_frame, text="Estado:").grid(row=0, column=2, padx=(10,0), sticky=tk.W)
        self.combo_estado = ttk.Combobox(
            controles_frame,
            values=["Todos", "completada", "cancelada", "pendiente"],
            state="readonly"
        )
        self.combo_estado.set("Todos")
        self.combo_estado.grid(row=0, column=3, padx=5, sticky=tk.W)
        self.combo_estado.bind("<<ComboboxSelected>>", lambda e: self._aplicar_filtros())

        # Filtro por fechas
        ttk.Label(controles_frame, text="Desde:").grid(row=1, column=0, pady=(10,0), sticky=tk.W)
        self.entrada_fecha_inicio = ttk.Entry(controles_frame)
        self.entrada_fecha_inicio.grid(row=1, column=1, pady=(10,0), padx=5, sticky=tk.W)
        self.entrada_fecha_inicio.bind("<FocusOut>", lambda e: self._aplicar_filtros())

        ttk.Label(controles_frame, text="Hasta:").grid(row=1, column=2, pady=(10,0), padx=(10,0), sticky=tk.W)
        self.entrada_fecha_fin = ttk.Entry(controles_frame)
        self.entrada_fecha_fin.grid(row=1, column=3, pady=(10,0), padx=5, sticky=tk.W)
        self.entrada_fecha_fin.bind("<FocusOut>", lambda e: self._aplicar_filtros())

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

        scrollbar.config(command=self.tabla.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tabla.pack(fill=tk.BOTH, expand=True)
        
        # Configurar colores para diferentes estados
        self.tabla.tag_configure('cancelada', foreground='#bf616a')  # Rojo
        self.tabla.tag_configure('pendiente', foreground='#ebcb8b')  # Amarillo

    def _crear_botones_accion(self):
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(
            btn_frame,
            text="Ver Detalle",
            style="Primary.TButton",
            command=self._ver_detalle
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Cancelar Transacción",
            style="Danger.TButton",
            command=self._cancelar_transaccion,
            state="disabled"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Exportar a Excel",
            style="Secondary.TButton",
            command=self._exportar_excel
        ).pack(side=tk.RIGHT, padx=5)

    def _cargar_datos(self):
        try:
            query = """
                SELECT 
                    t.id_transaccion,
                    strftime('%d/%m/%Y %H:%M', t.fecha) as fecha_formateada,
                    t.tipo,
                    CASE 
                        WHEN t.id_cliente IS NULL THEN 'Sistema'
                        ELSE c.nombres || ' ' || COALESCE(c.apellido_p, '')
                    END as cliente,
                    mp.nombre as medio_pago,
                    t.subtotal,
                    t.impuestos,
                    t.total,
                    t.estado
                FROM Transacciones t
                LEFT JOIN Clientes c ON t.id_cliente = c.id_cliente
                LEFT JOIN Medios_pago mp ON t.id_medio_pago = mp.id_medio_pago
                {where}
                ORDER BY t.fecha DESC
            """.format(where=self._construir_where())
            
            parametros = []
            if self.filtros['tipo'] != 'Todos':
                parametros.append(self.filtros['tipo'])
            if self.filtros['estado'] != 'Todos':
                parametros.append(self.filtros['estado'])
            if self.filtros['fecha_inicio']:
                parametros.append(self.filtros['fecha_inicio'])
            if self.filtros['fecha_fin']:
                parametros.append(self.filtros['fecha_fin'])
                
            self.datos = obtener_datos(query, parametros)
            self._actualizar_tabla()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error cargando datos: {str(e)}")

    def _construir_where(self):
        condiciones = []
        if self.filtros['tipo'] != 'Todos':
            condiciones.append("t.tipo = ?")
        if self.filtros['estado'] != 'Todos':
            condiciones.append("t.estado = ?")
        if self.filtros['fecha_inicio']:
            condiciones.append("t.fecha >= ?")
        if self.filtros['fecha_fin']:
            condiciones.append("t.fecha <= ?")
            
        return "WHERE " + " AND ".join(condiciones) if condiciones else ""

    def _actualizar_tabla(self):
        self.tabla.delete(*self.tabla.get_children())
        for transaccion in self.datos:
            self.tabla.insert("", tk.END, values=(
                transaccion[0],  # ID
                transaccion[1],  # Fecha
                transaccion[2].capitalize(),  # Tipo
                transaccion[3],  # Cliente
                transaccion[4],  # Medio pago
                f"${transaccion[5]:.2f}",  # Subtotal
                f"${transaccion[6]:.2f}",  # Impuestos
                f"${transaccion[7]:.2f}",  # Total
                transaccion[8].capitalize()  # Estado
            ), tags=(transaccion[8],))  # Tag para colorear por estado

    def _aplicar_filtros(self, event=None):
        self.filtros.update({
            'tipo': self.combo_tipo.get(),
            'estado': self.combo_estado.get(),
            'fecha_inicio': self.entrada_fecha_inicio.get(),
            'fecha_fin': self.entrada_fecha_fin.get()
        })
        self._cargar_datos()

    def _ordenar_por_columna(self, columna):
        # Implementar lógica de ordenamiento similar a tus otras pantallas
        pass

    def _ver_detalle(self):
        seleccion = self.tabla.focus()
        if not seleccion:
            messagebox.showwarning("Selección requerida", "Seleccione una transacción primero")
            return
            
        transaccion_id = self.tabla.item(seleccion, "values")[0]
        self._mostrar_dialogo_detalle(transaccion_id)

    def _mostrar_dialogo_detalle(self, transaccion_id):
        # Crear diálogo para mostrar detalles de la transacción
        dialogo = tk.Toplevel(self)
        dialogo.title(f"Detalle Transacción #{transaccion_id}")
        dialogo.geometry("800x600")
        
        # Obtener detalles de la transacción
        detalles = obtener_datos("""
            SELECT p.nombre, dt.cantidad, dt.precio_unitario, 
                   dt.descuento, dt.iva_aplicado,
                   (dt.precio_unitario * dt.cantidad - dt.descuento) as subtotal
            FROM Detalle_transaccion dt
            JOIN Productos p ON dt.id_producto = p.id_producto
            WHERE dt.id_transaccion = ?
            ORDER BY dt.id_detalle
        """, (transaccion_id,))
        
        # Crear tabla de detalles
        columns = ("producto", "cantidad", "precio", "descuento", "iva", "subtotal")
        tabla_detalle = ttk.Treeview(
            dialogo,
            columns=columns,
            show="headings"
        )
        
        # Configurar columnas
        tabla_detalle.heading("producto", text="Producto")
        tabla_detalle.heading("cantidad", text="Cantidad")
        tabla_detalle.heading("precio", text="Precio Unit.")
        tabla_detalle.heading("descuento", text="Descuento")
        tabla_detalle.heading("iva", text="IVA")
        tabla_detalle.heading("subtotal", text="Subtotal")
        
        tabla_detalle.column("producto", width=250)
        tabla_detalle.column("cantidad", width=80, anchor=tk.CENTER)
        tabla_detalle.column("precio", width=100, anchor=tk.E)
        tabla_detalle.column("descuento", width=100, anchor=tk.E)
        tabla_detalle.column("iva", width=100, anchor=tk.E)
        tabla_detalle.column("subtotal", width=120, anchor=tk.E)
        
        # Agregar datos
        for detalle in detalles:
            tabla_detalle.insert("", tk.END, values=(
                detalle[0],  # Producto
                detalle[1],  # Cantidad
                f"${detalle[2]:.2f}",  # Precio
                f"${detalle[3]:.2f}",  # Descuento
                f"${detalle[4]:.2f}",  # IVA
                f"${detalle[5]:.2f}"   # Subtotal
            ))
        
        tabla_detalle.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _cancelar_transaccion(self):
        # Implementar lógica para cancelar transacciones
        pass

    def _exportar_excel(self):
        # Implementar exportación a Excel
        pass

if __name__ == "__main__":
    root = tk.Tk()
    app = PantallaTransacciones(root)
    app.pack(fill=tk.BOTH, expand=True)
    root.mainloop()