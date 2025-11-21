import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
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
        self.descuento_global = 0.0
        self.productos_filtrados = []
        
        self._configurar_estilos_extra()
        self._cargar_datos()
        self._crear_layout_principal()
        self._actualizar_totales()

    def _configurar_estilos_extra(self):
        """Configura estilos visuales específicos para el POS"""
        style = ttk.Style()
        
        # Estilo para totales grandes
        style.configure("BigTotal.TLabel", font=("Helvetica", 28, "bold"), foreground="#2E3440")
        style.configure("SubTotal.TLabel", font=("Helvetica", 12), foreground="#4C566A")
        
        # Botones de Acción
        style.configure("Cobrar.TButton", font=("Helvetica", 14, "bold"), background="#A3BE8C", foreground="black")
        style.configure("Danger.TButton", font=("Helvetica", 10, "bold"), background="#BF616A", foreground="black")
        style.configure("Warning.TButton", font=("Helvetica", 10, "bold"), background="#EBCB8B", foreground="black")
        style.configure("Action.TButton", font=("Helvetica", 10, "bold"), background="#5E81AC", foreground="black")
        
        # Treeview Moderna
        style.configure("Carrito.Treeview", rowheight=30, font=("Arial", 10))
        style.configure("Carrito.Treeview.Heading", font=("Arial", 10, "bold"), background="#ECEFF4")

    def _cargar_datos(self):
        """Carga inicial de datos"""
        self.productos = obtener_datos("""
            SELECT id_producto, nombre, precio_venta, sku, codigo_barras, stock_actual
            FROM Productos WHERE estado = 1 AND stock_actual > 0
            ORDER BY nombre
        """)
        
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
        
        self.medios_pago = obtener_datos("SELECT id_medio_pago, clave_sat, nombre FROM Medios_pago ORDER BY id_medio_pago")

    def _crear_layout_principal(self):
        """Diseño de 2 columnas: Catálogo (Izq) y Proceso de Venta (Der)"""
        
        # Contenedor principal dividido
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg="#D8DEE9", sashwidth=5)
        paned.pack(fill=tk.BOTH, expand=True)

        # ================== PANEL IZQUIERDO (CATÁLOGO) ==================
        left_frame = tk.Frame(paned, bg="white")
        paned.add(left_frame, width=700)

        # Barra de búsqueda estilizada
        search_frame = tk.Frame(left_frame, bg="#ECEFF4", pady=15, padx=15)
        search_frame.pack(fill=tk.X)
        
        tk.Label(search_frame, text="📦 Catálogo de Productos", font=("Helvetica", 14, "bold"), bg="#ECEFF4", fg="#2E3440").pack(anchor="w")
        
        search_box = tk.Frame(search_frame, bg="#ECEFF4", pady=5)
        search_box.pack(fill=tk.X)
        
        tk.Label(search_box, text="🔍 Buscar:", bg="#ECEFF4", font=("Arial", 11)).pack(side="left")
        self.entrada_busqueda = ttk.Entry(search_box, font=("Arial", 12))
        self.entrada_busqueda.pack(side="left", fill=tk.X, expand=True, padx=10)
        self.entrada_busqueda.bind("<KeyRelease>", self._actualizar_lista_productos)

        # Lista de productos (Treeview para mejor alineación)
        cols_prod = ("Producto", "Precio", "Stock", "SKU")
        self.tree_productos = ttk.Treeview(left_frame, columns=cols_prod, show="headings", selectmode="browse")
        
        self.tree_productos.heading("Producto", text="Producto / Descripción")
        self.tree_productos.heading("Precio", text="Precio")
        self.tree_productos.heading("Stock", text="Stock")
        self.tree_productos.heading("SKU", text="SKU/Código")
        
        self.tree_productos.column("Producto", width=300)
        self.tree_productos.column("Precio", width=80, anchor="e")
        self.tree_productos.column("Stock", width=60, anchor="center")
        self.tree_productos.column("SKU", width=100)
        
        self.tree_productos.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # --- CAMBIO: El evento llama a _pedir_cantidad ---
        self.tree_productos.bind("<Double-1>", self._pedir_cantidad_producto)

        # Info footer
        tk.Label(left_frame, text="💡 Doble clic para agregar al carrito", bg="white", fg="#88C0D0").pack(pady=5)

        # ================== PANEL DERECHO (CARRITO Y PAGO) ==================
        right_frame = tk.Frame(paned, bg="#F0F4F7", padx=10, pady=10)
        paned.add(right_frame)

        # 1. Datos del Cliente
        cliente_frame = tk.LabelFrame(right_frame, text="👤 Datos del Cliente", bg="#F0F4F7", font=("Arial", 10, "bold"))
        cliente_frame.pack(fill=tk.X, pady=5)
        
        self.combo_clientes = ttk.Combobox(cliente_frame, state="readonly", values=[c[1] for c in self.clientes])
        self.combo_clientes.pack(fill=tk.X, padx=5, pady=2)
        self.combo_clientes.set("Seleccionar Cliente...")
        self.combo_clientes.bind("<<ComboboxSelected>>", self._actualizar_direcciones)
        
        self.combo_direcciones = ttk.Combobox(cliente_frame, state="readonly")
        self.combo_direcciones.pack(fill=tk.X, padx=5, pady=5)
        self.combo_direcciones.set("Dirección fiscal...")

        # 2. Tabla Carrito
        tk.Label(right_frame, text="🛒 Carrito de Compras", font=("Arial", 11, "bold"), bg="#F0F4F7").pack(anchor="w", pady=(10,5))
        
        cols_cart = ("Cant", "Producto", "Total")
        self.tabla_carrito = ttk.Treeview(right_frame, columns=cols_cart, show="headings", height=12, style="Carrito.Treeview")
        
        self.tabla_carrito.heading("Cant", text="#")
        self.tabla_carrito.heading("Producto", text="Item")
        self.tabla_carrito.heading("Total", text="Total")
        
        self.tabla_carrito.column("Cant", width=40, anchor="center")
        self.tabla_carrito.column("Producto", width=180)
        self.tabla_carrito.column("Total", width=80, anchor="e")
        
        self.tabla_carrito.pack(fill=tk.BOTH, expand=True)

        # Botones de manipulación carrito
        btn_tools = tk.Frame(right_frame, bg="#F0F4F7")
        btn_tools.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_tools, text="🏷️ Descuento", style="Warning.TButton", command=self._mostrar_dialogo_descuento).pack(side="left", fill="x", expand=True, padx=2)
        ttk.Button(btn_tools, text="🗑️ Quitar", style="Danger.TButton", command=self._eliminar_item).pack(side="left", fill="x", expand=True, padx=2)

        # 3. Totales y Pago
        pago_frame = tk.Frame(right_frame, bg="white", relief="raised", bd=1, padx=15, pady=15)
        pago_frame.pack(fill=tk.X, pady=10)

        # Selección Medio Pago
        tk.Label(pago_frame, text="Medio de Pago:", bg="white").pack(anchor="w")
        self.combo_medios_pago = ttk.Combobox(pago_frame, state="readonly", values=[f"{mp[2]}" for mp in self.medios_pago])
        self.combo_medios_pago.pack(fill=tk.X, pady=(0, 10))
        if self.medios_pago: self.combo_medios_pago.current(0)

        # Opciones
        self.factura_var = tk.BooleanVar()
        tk.Checkbutton(pago_frame, text="Generar Factura XML/PDF", variable=self.factura_var, bg="white", command=self._validar_facturacion).pack(anchor="w")

        # Totales Numéricos
        self.lbl_subtotal = ttk.Label(pago_frame, text="Subtotal: $0.00", style="SubTotal.TLabel", background="white")
        self.lbl_subtotal.pack(anchor="e", pady=2)
        
        self.lbl_iva = ttk.Label(pago_frame, text="IVA (16%): $0.00", style="SubTotal.TLabel", background="white")
        self.lbl_iva.pack(anchor="e", pady=2)
        
        ttk.Separator(pago_frame, orient="horizontal").pack(fill="x", pady=5)
        
        self.total_var = tk.StringVar(value="$0.00")
        ttk.Label(pago_frame, textvariable=self.total_var, style="BigTotal.TLabel", background="white").pack(anchor="e")

        # BOTÓN GIGANTE COBRAR
        ttk.Button(right_frame, text="✅ COBRAR E IMPRIMIR", style="Cobrar.TButton", command=self._procesar_venta).pack(fill=tk.X, ipady=10)

    # ================= LÓGICA DEL NEGOCIO =================

    def _actualizar_lista_productos(self, event=None):
        busqueda = self.entrada_busqueda.get().lower()
        for item in self.tree_productos.get_children():
            self.tree_productos.delete(item)
            
        self.productos_filtrados = []
        
        for p in self.productos:
            match = busqueda in p[1].lower() or (p[3] and busqueda in p[3].lower())
            if match and p[5] > 0:
                self.tree_productos.insert("", "end", values=(
                    p[1], 
                    f"${p[2]:.2f}", 
                    p[5], 
                    p[3] or "S/N"
                ))
                self.productos_filtrados.append(p)

    # --- NUEVA FUNCIÓN: PEDIR CANTIDAD ---
    def _pedir_cantidad_producto(self, event):
        """Abre un popup para pedir cantidad antes de agregar"""
        seleccion = self.tree_productos.selection()
        if not seleccion: return
        
        item_id = self.tree_productos.index(seleccion[0])
        producto = self.productos_filtrados[item_id]
        
        # Verificar cuánto stock queda realmente (restando lo que ya está en carrito)
        stock_real = producto[5]
        en_carrito = 0
        for item in self.carrito:
            if item["id_producto"] == producto[0]:
                en_carrito = item["cantidad"]
                break
        
        stock_disponible = stock_real - en_carrito
        
        if stock_disponible <= 0:
            messagebox.showwarning("Sin Stock", "Ya has añadido todo el stock disponible de este producto.")
            return

        # Crear Ventana Modal Personalizada
        dialog = tk.Toplevel(self)
        dialog.title("Agregar Producto")
        dialog.geometry("350x220")
        dialog.config(bg="white")
        dialog.resizable(False, False)
        
        # Centrar en pantalla
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 175
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 110
        dialog.geometry(f"+{x}+{y}")

        tk.Label(dialog, text="📦 Agregar al Carrito", font=("Helvetica", 12, "bold"), bg="white", fg="#5E81AC").pack(pady=(15, 5))
        tk.Label(dialog, text=producto[1], font=("Arial", 10), bg="white").pack()
        tk.Label(dialog, text=f"Stock disponible: {stock_disponible}", font=("Arial", 9, "italic"), bg="white", fg="gray").pack(pady=5)

        tk.Label(dialog, text="Cantidad:", bg="white").pack()
        entry_cant = ttk.Entry(dialog, width=10, font=("Arial", 12), justify="center")
        entry_cant.pack(pady=5)
        entry_cant.insert(0, "1")
        entry_cant.select_range(0, tk.END)
        entry_cant.focus()

        def confirmar(event=None):
            try:
                cantidad = int(entry_cant.get())
                if cantidad <= 0:
                    messagebox.showerror("Error", "La cantidad debe ser mayor a 0", parent=dialog)
                    return
                if cantidad > stock_disponible:
                    messagebox.showerror("Error", f"Solo hay {stock_disponible} unidades disponibles", parent=dialog)
                    return
                
                # Si pasa validaciones, agregamos
                self._agregar_al_carrito_final(producto, cantidad)
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Ingresa un número válido", parent=dialog)

        entry_cant.bind("<Return>", confirmar)

        btn_frame = tk.Frame(dialog, bg="white")
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Agregar ➔", style="Action.TButton", command=confirmar).pack(side="left", padx=5)

    def _agregar_al_carrito_final(self, producto, cantidad_agregar):
        """Lógica interna para añadir a la lista después de validar cantidad"""
        # Buscar si ya existe
        found = False
        for item in self.carrito:
            if item["id_producto"] == producto[0]:
                item["cantidad"] += cantidad_agregar
                found = True
                break
        
        if not found:
            self.carrito.append({
                "id_producto": producto[0],
                "nombre": producto[1],
                "precio": producto[2],
                "cantidad": cantidad_agregar,
                "descuento": 0.0
            })
        
        self._actualizar_carrito()
        self._actualizar_totales()

    def _actualizar_carrito(self):
        for item in self.tabla_carrito.get_children():
            self.tabla_carrito.delete(item)
            
        for item in self.carrito:
            descuento = (item["precio"] * item["cantidad"] * (self.descuento_global + item["descuento"]))
            total = (item["precio"] * item["cantidad"]) - descuento
            
            self.tabla_carrito.insert("", "end", values=(
                item["cantidad"],
                item["nombre"],
                f"${total:.2f}"
            ))

    def _actualizar_totales(self):
        subtotal_bruto = sum(i["precio"] * i["cantidad"] for i in self.carrito)
        descuento = sum((i["precio"] * i["cantidad"] * (self.descuento_global + i["descuento"])) for i in self.carrito)
        
        base = subtotal_bruto - descuento
        iva = base * 0.16
        total = base + iva
        
        self.lbl_subtotal.config(text=f"Subtotal: ${subtotal_bruto:.2f}")
        self.lbl_iva.config(text=f"IVA (16%): ${iva:.2f}")
        self.total_var.set(f"${total:.2f}")
        
        self.datos_totales = {"subtotal": base, "iva": iva, "total": total}

    def _eliminar_item(self):
        sel = self.tabla_carrito.selection()
        if sel:
            idx = self.tabla_carrito.index(sel[0])
            del self.carrito[idx]
            self._actualizar_carrito()
            self._actualizar_totales()

    def _mostrar_dialogo_descuento(self):
        res = tk.simpledialog.askfloat("Descuento", "Ingrese porcentaje de descuento global (0-100):", parent=self)
        if res is not None and 0 <= res <= 100:
            self.descuento_global = res / 100
            self._actualizar_carrito()
            self._actualizar_totales()

    def _actualizar_direcciones(self, event):
        idx = self.combo_clientes.current()
        if idx >= 0:
            id_cliente = self.clientes[idx][0]
            dirs = obtener_datos(f"SELECT id_direccion, calle || ' ' || colonia FROM Direcciones WHERE id_cliente={id_cliente}")
            self.combo_direcciones['values'] = [d[1] for d in dirs]
            if dirs: self.combo_direcciones.current(0)

    def _validar_facturacion(self):
        if self.factura_var.get() and self.combo_clientes.current() == -1:
            messagebox.showwarning("Aviso", "Seleccione un cliente para facturar")
            self.factura_var.set(False)

    # ================= PROCESAMIENTO Y UI DE FACTURA =================

    def _procesar_venta(self):
        if not self.carrito:
            messagebox.showwarning("Vacío", "El carrito está vacío")
            return
        
        if self.combo_medios_pago.current() == -1:
            messagebox.showwarning("Pago", "Seleccione medio de pago")
            return

        try:
            cliente_id = self.clientes[self.combo_clientes.current()][0] if self.combo_clientes.current() >= 0 else None
            medio_id = self.medios_pago[self.combo_medios_pago.current()][0]
            
            query_venta = ("INSERT INTO Transacciones (tipo, fecha, id_cliente, id_medio_pago, subtotal, impuestos, total, estado) VALUES (?,?,?,?,?,?,?,?)",
                           ("venta", datetime.now(), cliente_id, medio_id, self.datos_totales["subtotal"], self.datos_totales["iva"], self.datos_totales["total"], "completada"))
            
            id_transaccion = ejecutar_transaccion([query_venta])
            
            queries_extra = []
            for item in self.carrito:
                queries_extra.append(("INSERT INTO Detalle_transaccion (id_transaccion, id_producto, cantidad, precio_unitario, descuento, iva_aplicado) VALUES (?,?,?,?,?,?)",
                                     (id_transaccion, item["id_producto"], item["cantidad"], item["precio"], 0, 0)))
                queries_extra.append(("UPDATE Productos SET stock_actual = stock_actual - ? WHERE id_producto = ?", 
                                     (item["cantidad"], item["id_producto"])))
                queries_extra.append(("INSERT INTO Movimientos (tipo, fecha, cantidad, id_producto, referencia) VALUES (?,?,?,?,?)",
                                     ("salida", datetime.now(), -item["cantidad"], item["id_producto"], f"Venta #{id_transaccion}")))

            ejecutar_transaccion(queries_extra)

            self._mostrar_ticket_visual(id_transaccion)
            self._limpiar_todo()

        except Exception as e:
            messagebox.showerror("Error", f"Error procesando venta: {e}")

    def _mostrar_ticket_visual(self, id_transaccion):
        popup = tk.Toplevel(self)
        popup.title(f"Recibo de Venta #{id_transaccion}")
        popup.geometry("450x650")
        popup.config(bg="white")
        
        header = tk.Frame(popup, bg="#A3BE8C", pady=20)
        header.pack(fill="x")
        
        tk.Label(header, text="✅ VENTA EXITOSA", font=("Helvetica", 16, "bold"), bg="#A3BE8C", fg="white").pack()
        tk.Label(header, text=f"Folio: {id_transaccion:05d}", font=("Courier", 12), bg="#A3BE8C", fg="white").pack()
        tk.Label(header, text=datetime.now().strftime("%d/%m/%Y %H:%M"), bg="#A3BE8C", fg="white").pack()

        info = tk.Frame(popup, bg="white", padx=20, pady=10)
        info.pack(fill="x")
        cli_txt = self.combo_clientes.get() or "Público General"
        tk.Label(info, text=f"Cliente: {cli_txt}", font=("Arial", 10, "bold"), bg="white").pack(anchor="w")
        
        table_frame = tk.Frame(popup, bg="white", padx=10)
        table_frame.pack(fill="both", expand=True)
        
        cols = ("Cant", "Desc", "Importe")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=10)
        tree.heading("Cant", text="#")
        tree.heading("Desc", text="Producto")
        tree.heading("Importe", text="Total")
        tree.column("Cant", width=40, anchor="center")
        tree.column("Desc", width=200)
        tree.column("Importe", width=80, anchor="e")
        tree.pack(fill="both", expand=True)

        for item in self.carrito:
            tot = item["cantidad"] * item["precio"]
            tree.insert("", "end", values=(item["cantidad"], item["nombre"], f"${tot:.2f}"))

        footer = tk.Frame(popup, bg="#ECEFF4", padx=20, pady=20)
        footer.pack(fill="x")
        
        tk.Label(footer, text=f"TOTAL: ${self.datos_totales['total']:.2f}", bg="#ECEFF4", font=("Helvetica", 16, "bold")).pack(anchor="e")

        ttk.Button(footer, text="🖨️ Imprimir y Cerrar", command=popup.destroy).pack(fill="x", pady=(15, 0))

    def _limpiar_todo(self):
        self.carrito = []
        self.descuento_global = 0.0
        self._actualizar_carrito()
        self._actualizar_totales()
        self.entrada_busqueda.delete(0, tk.END)
        self._actualizar_lista_productos()