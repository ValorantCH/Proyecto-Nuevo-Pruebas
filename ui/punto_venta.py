import tkinter as tk
from tkinter import ttk, messagebox
from db.db import obtener_datos, ejecutar_query, ejecutar_transaccion
from ui.styles import AppTheme
from datetime import datetime

class PantallaVentas(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.theme = AppTheme()
        self.carrito = []
        self.productos = []
        self.clientes = []
        self.medios_pago = []
        self.descuento_global = 0.0  # Descuento aplicado a toda la venta
        
        self._cargar_datos()
        self._crear_widgets()
        self._actualizar_totales()
        self.productos_filtrados = []

    def _cargar_datos(self):
        """Cargar datos iniciales desde la base de datos"""
        # Productos activos con stock
        self.productos = obtener_datos("""
            SELECT id_producto, nombre, precio_venta, sku, codigo_barras, stock_actual
            FROM Productos WHERE estado = 1 AND stock_actual > 0
            ORDER BY nombre
            """)
        
        # Clientes activos con sus direcciones
        self.clientes = obtener_datos("""
            SELECT c.id_cliente, 
                   c.nombres || ' ' || COALESCE(c.apellido_p, '') || ' ' || COALESCE(c.apellido_m, ''),
                   c.rfc,
                   d.id_direccion,
                   d.calle || ' ' || d.numero_domicilio || ', ' || d.colonia || ', ' || d.ciudad
            FROM Clientes c
            LEFT JOIN Direcciones d ON c.id_cliente = d.id_cliente AND d.principal = 1
            WHERE c.estado = 1
            """)
        
        # Medios de pago configurados
        self.medios_pago = obtener_datos("""
            SELECT id_medio_pago, clave_sat, nombre 
            FROM Medios_pago 
            ORDER BY id_medio_pago
            """)

    def _crear_widgets(self):
        """Construir todos los componentes de la interfaz gráfica"""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel izquierdo - Búsqueda y productos
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._crear_panel_busqueda(left_panel)
        
        # Panel derecho - Carrito y totales
        right_panel = ttk.Frame(main_frame, width=450)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        self._crear_panel_carrito(right_panel)
        self._crear_controles_finales(right_panel)

    def _crear_panel_busqueda(self, parent):
        """Crear sección de búsqueda de productos"""
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, pady=5)
        
        # Configurar proporción 30-70
        search_frame.columnconfigure(0, weight=1)
        search_frame.columnconfigure(1, weight=3)
        
        ttk.Label(search_frame, text="🔍 Buscar:").grid(row=0, column=0, sticky=tk.EW)
        self.entrada_busqueda = ttk.Entry(search_frame)
        self.entrada_busqueda.grid(row=0, column=1, sticky=tk.EW, padx=5)
        self.entrada_busqueda.bind("<KeyRelease>", self._actualizar_lista_productos)
        
        # Lista de productos con scroll
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(container)
        self.lista_productos = tk.Listbox(
            container, 
            yscrollcommand=scrollbar.set,
            height=15,
            selectbackground=self.theme.colors['accent']
        )
        scrollbar.config(command=self.lista_productos.yview)
        
        self.lista_productos.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Doble clic para agregar al carrito
        self.lista_productos.bind("<Double-Button-1>", self._agregar_al_carrito)

    def _crear_panel_carrito(self, parent):
        """Crear tabla del carrito de compras"""
        columns = ("producto", "cantidad", "precio", "descuento", "subtotal")
        self.tabla_carrito = ttk.Treeview(
            parent,
            columns=columns,
            show="headings",
            height=8,
            selectmode="browse",
            style="Custom.Treeview" 
        )
        
        # Configurar columnas 
        self.tabla_carrito.heading("producto", text="Producto", anchor=tk.W)
        self.tabla_carrito.heading("cantidad", text="Cantidad", anchor=tk.CENTER)
        self.tabla_carrito.heading("precio", text="P. Unitario", anchor=tk.E)
        self.tabla_carrito.heading("descuento", text="Descuento", anchor=tk.E)
        self.tabla_carrito.heading("subtotal", text="Subtotal", anchor=tk.E)
        
        self.tabla_carrito.column("producto", width=250, stretch=tk.YES)
        self.tabla_carrito.column("cantidad", width=80, minwidth=70)
        self.tabla_carrito.column("precio", width=110, anchor=tk.E)
        self.tabla_carrito.column("descuento", width=110, anchor=tk.E)
        self.tabla_carrito.column("subtotal", width=120, anchor=tk.E)
        
        self.tabla_carrito.pack(fill=tk.BOTH, expand=True) 

        # Controles del carrito
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=5)
        
        ttk.Button(
            btn_frame, 
            text="Aplicar Descuento", 
            style="Secondary.TButton",
            command=self._mostrar_dialogo_descuento
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            btn_frame, 
            text="Eliminar", 
            style="Danger.TButton",
            command=self._eliminar_item
        ).pack(side=tk.LEFT, padx=5)

    def _crear_controles_finales(self, parent):
        """Crear sección de finalización de venta"""
        # Frame para datos del cliente
        cliente_frame = ttk.LabelFrame(parent, text="Datos del Cliente")
        cliente_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(cliente_frame, text="Cliente:").grid(row=0, column=0, sticky=tk.W)
        self.combo_clientes = ttk.Combobox(
            cliente_frame, 
            state="readonly",
            values=[c[1] for c in self.clientes]
        )
        self.combo_clientes.grid(row=0, column=1, sticky=tk.EW, padx=5)
        self.combo_clientes.bind("<<ComboboxSelected>>", self._actualizar_direcciones)
        
        ttk.Label(cliente_frame, text="Dirección:").grid(row=1, column=0, sticky=tk.W)
        self.combo_direcciones = ttk.Combobox(cliente_frame, state="readonly")
        self.combo_direcciones.grid(row=1, column=1, sticky=tk.EW, padx=5)
        
        # Frame para pago
        pago_frame = ttk.LabelFrame(parent, text="Datos de Pago")
        pago_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(pago_frame, text="Medio de pago:").grid(row=0, column=0, sticky=tk.W)
        self.combo_medios_pago = ttk.Combobox(
            pago_frame,
            state="readonly",
            values=[f"{mp[2]} ({mp[1]})" for mp in self.medios_pago]
        )
        self.combo_medios_pago.grid(row=0, column=1, sticky=tk.EW, padx=5)
        
        # Totales
        total_frame = ttk.Frame(parent)
        total_frame.pack(fill=tk.X, pady=10)
        
        self.subtotal_var = tk.StringVar(value="$0.00")
        self.descuento_var = tk.StringVar(value="$0.00")
        self.iva_var = tk.StringVar(value="$0.00")
        self.total_var = tk.StringVar(value="$0.00")
        
        ttk.Label(total_frame, text="Subtotal:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(total_frame, textvariable=self.subtotal_var).grid(row=0, column=1, sticky=tk.E)
        
        ttk.Label(total_frame, text="Descuento:").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(total_frame, textvariable=self.descuento_var).grid(row=1, column=1, sticky=tk.E)
        
        ttk.Label(total_frame, text="IVA (16%):").grid(row=2, column=0, sticky=tk.W)
        ttk.Label(total_frame, textvariable=self.iva_var).grid(row=2, column=1, sticky=tk.E)
        
        ttk.Label(total_frame, text="Total:", style="Bold.TLabel").grid(row=3, column=0, sticky=tk.W)
        ttk.Label(total_frame, textvariable=self.total_var, style="Bold.TLabel").grid(row=3, column=1, sticky=tk.E)
        
        # Facturación
        self.factura_var = tk.BooleanVar()
        ttk.Checkbutton(
            parent, 
            text="Generar factura CFDI", 
            variable=self.factura_var,
            command=self._validar_facturacion
        ).pack(pady=5)
        
        # Botón final
        ttk.Button(
            parent, 
            text="🖨️ Finalizar Venta", 
            style="Success.TButton",
            command=self._procesar_venta
        ).pack(pady=10, fill=tk.X)

    def _actualizar_lista_productos(self, event=None):
        """Actualizar lista de productos según criterio de búsqueda"""
        busqueda = self.entrada_busqueda.get().lower()
        self.lista_productos.delete(0, tk.END)
        self.productos_filtrados = []
        
        for p in self.productos:
            match = any([
                busqueda in str(p[0]).lower(),
                busqueda in p[1].lower(),
                (p[3] and busqueda in p[3].lower()),
                (p[4] and busqueda in p[4].lower())
            ])
            
            if match and p[5] > 0:
                self.lista_productos.insert(tk.END, f"{p[1]} - ${p[2]:.2f} | Stock: {p[5]}")
                self.productos_filtrados.append(p)

    def _agregar_al_carrito(self, event):
        """Agregar producto seleccionado al carrito"""
        seleccion = self.lista_productos.curselection()
        if not seleccion:
            return
        
        producto_idx = seleccion[0]
        producto = self.productos_filtrados[seleccion[0]]
        
        # Verificar stock
        if producto[5] < 1:
            messagebox.showwarning("Stock", "Producto sin stock disponible")
            return
        
        # Buscar si ya está en el carrito
        for item in self.carrito:
            if item["id_producto"] == producto[0]:
                if (item["cantidad"] + 1) > producto[5]:
                    messagebox.showwarning("Stock", "No hay suficiente stock")
                    return
                item["cantidad"] += 1
                break
        else:
            self.carrito.append({
                "id_producto": producto[0],
                "nombre": producto[1],
                "precio": producto[2],
                "cantidad": 1,
                "descuento": 0.0  # Descuento individual
            })
        
        self._actualizar_carrito()
        self._actualizar_totales()

    def _actualizar_carrito(self):
        """Actualizar visualización del carrito"""
        self.tabla_carrito.delete(*self.tabla_carrito.get_children())
        
        for item in self.carrito:
            descuento_total = (item["precio"] * item["cantidad"] * 
                             (self.descuento_global + item["descuento"]))
            
            subtotal = (item["precio"] * item["cantidad"]) - descuento_total
            
            self.tabla_carrito.insert("", tk.END, values=(
                item["nombre"],
                item["cantidad"],
                f"${item['precio']:.2f}",
                f"${descuento_total:.2f}",
                f"${subtotal:.2f}"
            ))

    def _actualizar_totales(self):
        """Calcular y mostrar totales actualizados"""
        subtotal = sum(item["precio"] * item["cantidad"] for item in self.carrito)
        descuento = sum(
            (item["precio"] * item["cantidad"] * 
             (self.descuento_global + item["descuento"])) 
            for item in self.carrito
        )
        base_gravable = subtotal - descuento
        iva = base_gravable * 0.16
        total = base_gravable + iva
        
        self.subtotal_var.set(f"${subtotal:.2f}")
        self.descuento_var.set(f"${descuento:.2f}")
        self.iva_var.set(f"${iva:.2f}")
        self.total_var.set(f"${total:.2f}")

    def _mostrar_dialogo_descuento(self):
        """Mostrar diálogo para aplicar descuentos"""
        dialogo = tk.Toplevel(self)
        dialogo.title("Gestión de Descuentos")
        dialogo.geometry("400x250")  
        dialogo.resizable(False, False)
        dialogo.configure(bd=0) 
        
        # Frame principal con borde sutil
        main_frame = ttk.Frame(dialogo, padding=15, relief="solid", borderwidth=1)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tipo de descuento
        ttk.Label(main_frame, text="Tipo de descuento:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.tipo_descuento = tk.StringVar(value="global")
        
        rb_frame = ttk.Frame(main_frame)
        rb_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W)
        
        ttk.Radiobutton(rb_frame, 
                    text="Descuento Global (a toda la venta)",  
                    variable=self.tipo_descuento, 
                    value="global").pack(anchor=tk.W, pady=3)
        
        ttk.Radiobutton(rb_frame, 
                    text="Descuento Individual (a producto seleccionado)", 
                    variable=self.tipo_descuento, 
                    value="producto").pack(anchor=tk.W, pady=3)
        
        # Valor del descuento
        ttk.Label(main_frame, text="Porcentaje de descuento:").grid(row=2, column=0, sticky=tk.W, pady=10)
        self.entrada_descuento = ttk.Entry(main_frame, width=10)
        self.entrada_descuento.grid(row=2, column=1, sticky=tk.W, padx=5)
        ttk.Label(main_frame, text="%").grid(row=2, column=2, sticky=tk.W)
        
        # Sección de advertencia
        self.lbl_advertencia = ttk.Label(main_frame, 
                                        text="⚠ Para descuento individual, seleccione\nun producto en el carrito primero",
                                        foreground="#d08770",
                                        wraplength=300) 
        self.lbl_advertencia.grid(row=3, column=0, columnspan=3, pady=10)
        
        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=10)
        
        ttk.Button(btn_frame, 
                text="Aplicar Descuento", 
                style="Primary.TButton",
                command=lambda: self._aplicar_descuento(dialogo)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, 
                text="Cancelar", 
                style="Secondary.TButton",
                command=dialogo.destroy).pack(side=tk.RIGHT)
        
        # Ajustar columnas
        main_frame.columnconfigure(1, weight=1)
        
        # Actualizar visibilidad de advertencia
        self._actualizar_visibilidad_advertencia()

    def _aplicar_descuento(self, dialogo):
        """Aplicar descuento según selección"""
        try:
            valor = float(self.entrada_descuento.get())
            if valor < 0 or valor > 100:
                raise ValueError("El descuento debe ser entre 0 y 100%")
                
            if self.tipo_descuento.get() == "global":
                self.descuento_global = valor / 100
            else:
                selected_item = self.tabla_carrito.selection()
                if not selected_item:
                    messagebox.showwarning("Selección requerida", 
                                        "Seleccione un producto del carrito primero")
                    return
                    
                item_idx = self.tabla_carrito.index(selected_item[0])
                self.carrito[item_idx]["descuento"] = valor / 100
                
            self._actualizar_carrito()
            self._actualizar_totales()
            dialogo.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Valor inválido: {str(e)}")

    def _actualizar_direcciones(self, event=None):
        """Actualizar direcciones al seleccionar cliente"""
        cliente_idx = self.combo_clientes.current()
        if cliente_idx == -1:
            return
        
        id_cliente = self.clientes[cliente_idx][0]
        direcciones = obtener_datos(f"""
            SELECT id_direccion, 
                   calle || ' ' || numero_domicilio || ', ' || colonia || ', ' || ciudad
            FROM Direcciones
            WHERE id_cliente = {id_cliente}
            """)
        
        self.combo_direcciones["values"] = [d[1] for d in direcciones]
        if direcciones:
            self.combo_direcciones.current(0)

    def _validar_facturacion(self):
        """Validar requisitos para facturación"""
        if self.factura_var.get():
            if self.combo_clientes.current() == -1:
                messagebox.showwarning("Facturación", "Se requiere cliente para facturar")
                self.factura_var.set(False)
                return
            
            cliente_idx = self.combo_clientes.current()
            if not self.clientes[cliente_idx][2]:  # Verificar RFC
                messagebox.showwarning("Facturación", "El cliente no tiene RFC registrado")
                self.factura_var.set(False)

    def _procesar_venta(self):
        """Procesar toda la transacción en la base de datos"""
        if not self._validar_venta():
            return
        
        try:
            # Obtener índices de selección
            cliente_idx = self.combo_clientes.current()
            medio_pago_idx = self.combo_medios_pago.current()
            direccion_idx = self.combo_direcciones.current()

            # Validar medio de pago obligatorio
            if medio_pago_idx == -1:
                raise ValueError("Selecciona un medio de pago")

            # Obtener ID de cliente si existe
            id_cliente = None
            if cliente_idx >= 0:
                id_cliente = self.clientes[cliente_idx][0]

            # 1. Insertar transacción principal
            transaccion_query = (
                """
                INSERT INTO Transacciones (
                    tipo, fecha, id_cliente, id_medio_pago,
                    subtotal, impuestos, total, moneda, estado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "venta",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    id_cliente,
                    self.medios_pago[medio_pago_idx][0],
                    float(self.subtotal_var.get()[1:]),
                    float(self.iva_var.get()[1:]),
                    float(self.total_var.get()[1:]),
                    "MXN",
                    "completada"
                )
            )
            
            # Ejecutar transacción principal y obtener ID
            id_transaccion = ejecutar_transaccion([transaccion_query])

            # Preparar queries dependientes del ID de transacción
            queries = []
            
            # 2. Detalles de transacción
            for item in self.carrito:
                descuento_total = (item["precio"] * item["cantidad"] * 
                                (self.descuento_global + item["descuento"]))
                
                queries.append((
                    """
                    INSERT INTO Detalle_transaccion (
                        id_transaccion, id_producto, cantidad,
                        precio_unitario, descuento, iva_aplicado
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        id_transaccion,
                        item["id_producto"],
                        item["cantidad"],
                        item["precio"],
                        descuento_total,
                        (item["precio"] * item["cantidad"] - descuento_total) * 0.16
                    )
                ))

            # 3. Movimientos de inventario
            ref_cliente = f"cliente {id_cliente}" if id_cliente else "sin cliente"
            for item in self.carrito:
                queries.append((
                    """
                    INSERT INTO Movimientos (
                        tipo, fecha, cantidad, id_producto, referencia
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        "salida",
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        -item["cantidad"],
                        item["id_producto"],
                        f"Venta {ref_cliente} - trans {id_transaccion}"
                    )
                ))

            # 4. Actualizar stock
            for item in self.carrito:
                queries.append((
                    """
                    UPDATE Productos 
                    SET stock_actual = stock_actual - ? 
                    WHERE id_producto = ?
                    """,
                    (item["cantidad"], item["id_producto"])
                ))

            # Ejecutar todas las operaciones restantes
            ejecutar_transaccion(queries)

            # 5. Facturación (si aplica)
            if self.factura_var.get():
                self._generar_factura(id_transaccion, cliente_idx, direccion_idx)

            messagebox.showinfo("Éxito", f"Venta #{id_transaccion} procesada")
            self._limpiar_venta()

        except ValueError as ve:
            messagebox.showwarning("Validación", str(ve))
        except Exception as e:
            messagebox.showerror("Error", f"Error al procesar venta:\n{str(e)}")

    def _generar_factura(self, id_transaccion, cliente_idx, direccion_idx):
        """Generar registro de factura en la base de datos"""
        try:
            cliente = self.clientes[cliente_idx]
            direccion = self.combo_direcciones.get()
            
            # Obtener datos necesarios para la factura
            datos_factura = {
                "id_transaccion": id_transaccion,
                "id_direccion_fiscal": cliente[3],  # ID de dirección principal
                "serie": "FAC",  # Serie fija (puede personalizarse)
                "folio": f"FAC-{id_transaccion:04d}",  # Folio secuencial
                "fecha_emision": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "lugar_expedicion": direccion.split(",")[-1].strip(),  # Ciudad de la dirección
                "forma_pago": "Pago en una sola exhibición",
                "metodo_pago": self.medios_pago[self.combo_medios_pago.current()][1],  # Clave SAT
                "uso_cfdi": "G03",  # Uso genérico
                "nombre_cliente": cliente[1],  # Nombre completo
                "rfc_cliente": cliente[2],  # RFC del cliente
                "subtotal": float(self.subtotal_var.get()[1:]),
                "iva": float(self.iva_var.get()[1:]),
                "total": float(self.total_var.get()[1:]),
                "estado": "generada"
            }
            
            # Insertar factura en la base de datos
            ejecutar_query(
                """
                INSERT INTO Facturas (
                    id_transaccion, id_direccion_fiscal, serie, folio,
                    fecha_emision, lugar_expedicion, forma_pago, metodo_pago,
                    uso_cfdi, nombre_cliente, rfc_cliente, subtotal, iva, total, estado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(datos_factura.values())
            )
            
            # Generar PDF básico (opcional)
            self._generar_pdf_factura(datos_factura)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar factura:\n{str(e)}")

    def _generar_pdf_factura(self, datos):
        """Generar PDF básico de la factura (esqueleto)"""
        try:
            from fpdf import FPDF
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Cabecera
            pdf.cell(200, 10, txt=f"Factura {datos['serie']}-{datos['folio']}", ln=1, align='C')
            pdf.cell(200, 10, txt=f"Fecha: {datos['fecha_emision']}", ln=1)
            
            # Datos del cliente
            pdf.cell(200, 10, txt=f"Cliente: {datos['nombre_cliente']}", ln=1)
            pdf.cell(200, 10, txt=f"RFC: {datos['rfc_cliente']}", ln=1)
            
            # Totales
            pdf.cell(200, 10, txt=f"Subtotal: ${datos['subtotal']:.2f}", ln=1)
            pdf.cell(200, 10, txt=f"IVA: ${datos['iva']:.2f}", ln=1)
            pdf.cell(200, 10, txt=f"Total: ${datos['total']:.2f}", ln=1)
            
            # Guardar PDF
            nombre_archivo = f"factura_{datos['folio']}.pdf"
            pdf.output(nombre_archivo)
            
        except ImportError:
            print("FPDF2 no está instalado. Instala con: pip install fpdf2")
        except Exception as e:
            print(f"Error al generar PDF: {str(e)}")

    def _validar_venta(self):
        """Validar datos requeridos antes de procesar"""
        errores = []
        if not self.carrito:
            errores.append("- Agregar productos al carrito")
        if self.combo_medios_pago.current() == -1:
            errores.append("- Seleccionar medio de pago")
        if self.factura_var.get() and self.combo_direcciones.current() == -1:
            errores.append("- Seleccionar dirección fiscal")
        
        if errores:
            messagebox.showwarning("Validación", "Corrige estos errores:\n" + "\n".join(errores))
            return False
        return True

    def _eliminar_item(self):
        """Eliminar item seleccionado del carrito"""
        seleccion = self.tabla_carrito.selection()
        if not seleccion:
            return
        
        item_idx = self.tabla_carrito.index(seleccion[0])
        del self.carrito[item_idx]
        self._actualizar_carrito()
        self._actualizar_totales()

    def _limpiar_venta(self):
        """Restablecer interfaz para nueva venta"""
        self.carrito.clear()
        self.descuento_global = 0.0
        self.combo_clientes.set("")
        self.combo_direcciones.set("")
        self.combo_medios_pago.set("")
        self.factura_var.set(False)
        self._actualizar_carrito()
        self._actualizar_totales()
        self._actualizar_lista_productos()
    
    def _actualizar_visibilidad_advertencia(self):
        """Mostrar/ocultar advertencia según selección"""
        if self.tipo_descuento.get() == "producto":
            self.lbl_advertencia.grid()
        else:
            self.lbl_advertencia.grid_remove()

if __name__ == "__main__":
    root = tk.Tk()
    app = PantallaPuntoVenta(root)
    root.mainloop()