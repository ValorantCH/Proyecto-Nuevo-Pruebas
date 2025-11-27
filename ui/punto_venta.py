import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import platform
import subprocess
from datetime import datetime

# --- IMPORTACIONES DE REPORTLAB (PDF) ---
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# --- TUS MODULOS ---
from db.db import obtener_datos, ejecutar_transaccion
from ui.styles import AppTheme

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
        self.datos_totales = {"subtotal": 0, "iva": 0, "total": 0}
        
        self._configurar_estilos_extra()
        self._cargar_datos()
        self._crear_layout_principal()
        self._actualizar_totales()

    def _configurar_estilos_extra(self):
        style = ttk.Style()
        style.configure("BigTotal.TLabel", font=("Helvetica", 28, "bold"), foreground="#2E3440")
        style.configure("SubTotal.TLabel", font=("Helvetica", 12), foreground="#4C566A")
        style.configure("Cobrar.TButton", font=("Helvetica", 14, "bold"), background="#A3BE8C", foreground="black")
        style.configure("Danger.TButton", font=("Helvetica", 10, "bold"), background="#BF616A", foreground="black")
        style.configure("Warning.TButton", font=("Helvetica", 10, "bold"), background="#EBCB8B", foreground="black")
        style.configure("Action.TButton", font=("Helvetica", 10, "bold"), background="#5E81AC", foreground="black")
        style.configure("Carrito.Treeview", rowheight=30, font=("Arial", 10))
        style.configure("Carrito.Treeview.Heading", font=("Arial", 10, "bold"), background="#ECEFF4")

    def _cargar_datos(self):
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
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg="#D8DEE9", sashwidth=5)
        paned.pack(fill=tk.BOTH, expand=True)

        # === PANEL IZQUIERDO (CATÁLOGO) ===
        left_frame = tk.Frame(paned, bg="white")
        paned.add(left_frame, width=700)

        search_frame = tk.Frame(left_frame, bg="#ECEFF4", pady=15, padx=15)
        search_frame.pack(fill=tk.X)
        
        tk.Label(search_frame, text="📦 Catálogo de Productos", font=("Helvetica", 14, "bold"), bg="#ECEFF4", fg="#2E3440").pack(anchor="w")
        
        search_box = tk.Frame(search_frame, bg="#ECEFF4", pady=5)
        search_box.pack(fill=tk.X)
        
        tk.Label(search_box, text="🔍 Buscar:", bg="#ECEFF4", font=("Arial", 11)).pack(side="left")
        self.entrada_busqueda = ttk.Entry(search_box, font=("Arial", 12))
        self.entrada_busqueda.pack(side="left", fill=tk.X, expand=True, padx=10)
        self.entrada_busqueda.bind("<KeyRelease>", self._actualizar_lista_productos)

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
        self.tree_productos.bind("<Double-1>", self._pedir_cantidad_producto)

        tk.Label(left_frame, text="💡 Doble clic para agregar al carrito", bg="white", fg="#88C0D0").pack(pady=5)

        # === PANEL DERECHO (CARRITO) ===
        right_frame = tk.Frame(paned, bg="#F0F4F7", padx=10, pady=10)
        paned.add(right_frame)

        cliente_frame = tk.LabelFrame(right_frame, text="👤 Datos del Cliente", bg="#F0F4F7", font=("Arial", 10, "bold"))
        cliente_frame.pack(fill=tk.X, pady=5)
        
        self.combo_clientes = ttk.Combobox(cliente_frame, state="readonly", values=[c[1] for c in self.clientes])
        self.combo_clientes.pack(fill=tk.X, padx=5, pady=2)
        self.combo_clientes.set("Seleccionar Cliente...")
        
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

        btn_tools = tk.Frame(right_frame, bg="#F0F4F7")
        btn_tools.pack(fill=tk.X, pady=5)
        ttk.Button(btn_tools, text="🏷️ Descuento", style="Warning.TButton", command=self._mostrar_dialogo_descuento).pack(side="left", fill="x", expand=True, padx=2)
        ttk.Button(btn_tools, text="🗑️ Quitar", style="Danger.TButton", command=self._eliminar_item).pack(side="left", fill="x", expand=True, padx=2)

        pago_frame = tk.Frame(right_frame, bg="white", relief="raised", bd=1, padx=15, pady=15)
        pago_frame.pack(fill=tk.X, pady=10)

        tk.Label(pago_frame, text="Medio de Pago:", bg="white").pack(anchor="w")
        self.combo_medios_pago = ttk.Combobox(pago_frame, state="readonly", values=[f"{mp[2]}" for mp in self.medios_pago])
        self.combo_medios_pago.pack(fill=tk.X, pady=(0, 10))
        if self.medios_pago: self.combo_medios_pago.current(0)

        self.lbl_subtotal = ttk.Label(pago_frame, text="Subtotal: $0.00", style="SubTotal.TLabel", background="white")
        self.lbl_subtotal.pack(anchor="e", pady=2)
        
        self.lbl_iva = ttk.Label(pago_frame, text="IVA (16%): $0.00", style="SubTotal.TLabel", background="white")
        self.lbl_iva.pack(anchor="e", pady=2)
        
        ttk.Separator(pago_frame, orient="horizontal").pack(fill="x", pady=5)
        
        self.total_var = tk.StringVar(value="$0.00")
        ttk.Label(pago_frame, textvariable=self.total_var, style="BigTotal.TLabel", background="white").pack(anchor="e")

        ttk.Button(right_frame, text="✅ COBRAR E IMPRIMIR", style="Cobrar.TButton", command=self._procesar_venta).pack(fill=tk.X, ipady=10)

    # ================= LÓGICA DE NEGOCIO =================

    def _actualizar_lista_productos(self, event=None):
        busqueda = self.entrada_busqueda.get().lower()
        for item in self.tree_productos.get_children():
            self.tree_productos.delete(item)
            
        self.productos_filtrados = []
        for p in self.productos:
            match = busqueda in p[1].lower() or (p[3] and busqueda in p[3].lower())
            if match and p[5] > 0:
                self.tree_productos.insert("", "end", values=(p[1], f"${p[2]:.2f}", p[5], p[3] or "S/N"))
                self.productos_filtrados.append(p)

    def _pedir_cantidad_producto(self, event):
        seleccion = self.tree_productos.selection()
        if not seleccion: return
        
        item_id = self.tree_productos.index(seleccion[0])
        producto = self.productos_filtrados[item_id]
        
        stock_real = producto[5]
        en_carrito = sum(item["cantidad"] for item in self.carrito if item["id_producto"] == producto[0])
        stock_disponible = stock_real - en_carrito
        
        if stock_disponible <= 0:
            messagebox.showwarning("Sin Stock", "Stock agotado para este producto.")
            return

        dialog = tk.Toplevel(self)
        dialog.title("Cantidad")
        dialog.geometry("300x200")
        dialog.config(bg="white")
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 150
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 100
        dialog.geometry(f"+{x}+{y}")
        dialog.transient(self) 
        dialog.grab_set()

        tk.Label(dialog, text=producto[1], font=("Arial", 10, "bold"), bg="white").pack(pady=10)
        tk.Label(dialog, text=f"Disponible: {stock_disponible}", bg="white", fg="gray").pack()
        
        entry_cant = ttk.Entry(dialog, width=10, font=("Arial", 12), justify="center")
        entry_cant.pack(pady=10)
        entry_cant.insert(0, "1")
        entry_cant.focus()
        entry_cant.select_range(0, tk.END)

        def confirmar(event=None):
            try:
                c = int(entry_cant.get())
                if 0 < c <= stock_disponible:
                    self._agregar_al_carrito_final(producto, c)
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", f"Cantidad inválida (Máx: {stock_disponible})", parent=dialog)
            except ValueError:
                pass

        entry_cant.bind("<Return>", confirmar)
        ttk.Button(dialog, text="Agregar", command=confirmar).pack(pady=10)

    def _agregar_al_carrito_final(self, producto, cantidad):
        found = False
        for item in self.carrito:
            if item["id_producto"] == producto[0]:
                item["cantidad"] += cantidad
                found = True
                break
        if not found:
            self.carrito.append({"id_producto": producto[0], "nombre": producto[1], "precio": producto[2], "cantidad": cantidad, "descuento": 0.0})
        self._actualizar_carrito()
        self._actualizar_totales()

    def _actualizar_carrito(self):
        for item in self.tabla_carrito.get_children():
            self.tabla_carrito.delete(item)
        for item in self.carrito:
            total = (item["precio"] * item["cantidad"]) * (1 - self.descuento_global - item["descuento"])
            self.tabla_carrito.insert("", "end", values=(item["cantidad"], item["nombre"], f"${total:.2f}"))

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
        res = tk.simpledialog.askfloat("Descuento", "Ingrese % descuento global:", parent=self)
        if res is not None and 0 <= res <= 100:
            self.descuento_global = res / 100
            self._actualizar_carrito()
            self._actualizar_totales()

    # ================= PROCESAMIENTO =================

    def _procesar_venta(self):
        # 1. VALIDACIÓN DE CLIENTE (Nueva)
        if self.combo_clientes.current() == -1:
            messagebox.showwarning("Aviso", "⚠️ Debe seleccionar un cliente de la lista para procesar la venta.")
            return

        if not self.carrito:
            messagebox.showwarning("Vacío", "El carrito está vacío")
            return
        if self.combo_medios_pago.current() == -1:
            messagebox.showwarning("Pago", "Seleccione medio de pago")
            return

        try:
            # Datos ya validados
            cliente_idx = self.combo_clientes.current()
            id_cliente = self.clientes[cliente_idx][0]
            nom_cliente = self.clientes[cliente_idx][1]
            rfc_cliente = self.clientes[cliente_idx][2] or "N/A"

            medio_id = self.medios_pago[self.combo_medios_pago.current()][0]

            # Guardar en DB
            query_venta = ("INSERT INTO Transacciones (tipo, fecha, id_cliente, id_medio_pago, subtotal, impuestos, total, estado) VALUES (?,?,?,?,?,?,?,?)",
                           ("venta", datetime.now(), id_cliente, medio_id, self.datos_totales["subtotal"], self.datos_totales["iva"], self.datos_totales["total"], "completada"))
            
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

            # Generar PDF Escalado sin márgenes y sin columnas extra
            ruta_pdf = self._generar_boleta_premium(id_transaccion, nom_cliente, rfc_cliente)
            
            respuesta = messagebox.askyesno("Venta Exitosa", f"Venta #{id_transaccion} registrada.\nBoleta guardada en:\n{ruta_pdf}\n\n¿Desea abrirla ahora?")
            if respuesta:
                self._abrir_archivo(ruta_pdf)

            self._limpiar_todo()

        except Exception as e:
            messagebox.showerror("Error", f"Error procesando venta: {e}")

    def _generar_boleta_premium(self, id_transaccion, nombre_cliente, rfc_cliente):
        """Genera PDF Horizontal (A4) Escalado para ocupar toda la hoja"""
        
        ruta_raiz = os.getcwd()
        nombre_archivo = os.path.join(ruta_raiz, f"Boleta_Venta_{id_transaccion}.pdf")

        # Configuración A4 Landscape con MÁRGENES MÍNIMOS (5mm)
        doc = SimpleDocTemplate(
            nombre_archivo,
            pagesize=landscape(A4),
            rightMargin=5*mm, leftMargin=5*mm, 
            topMargin=5*mm, bottomMargin=5*mm
        )

        elementos = []
        styles = getSampleStyleSheet()
        
        # --- Estilos Personalizados ---
        style_empresa = ParagraphStyle('Empresa', parent=styles['Normal'], fontSize=9, leading=11)
        style_empresa_title = ParagraphStyle('EmpresaTitle', parent=styles['Normal'], fontSize=14, fontName='Helvetica-Bold', leading=16)
        style_label = ParagraphStyle('Label', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', leading=11)
        style_data = ParagraphStyle('Data', parent=styles['Normal'], fontSize=9, fontName='Helvetica', leading=11)
        
        COLOR_BORDE = colors.HexColor("#5DADE2") 
        COLOR_FONDO_GRIS = colors.HexColor("#E5E8E8")

        # Ancho útil aproximado: 297mm - 10mm (margenes) = 287mm
        ANCHO_UTIL = 287*mm

        # =========================================================
        # 1. ENCABEZADO
        # =========================================================
        
        # Izquierda (200mm)
        datos_empresa = [
            [Paragraph("MI EMPRESA S.A.C.", style_empresa_title)],
            [Paragraph("AV. PRINCIPAL 123 - LIMA - PERU", style_empresa)],
            [Paragraph("SUCURSAL: LIMA CENTRO", style_empresa)],
            [Paragraph("Telf: (01) 555-0000 | Email: ventas@empresa.com", style_empresa)],
        ]
        t_empresa = Table(datos_empresa, colWidths=['100%'])
        t_empresa.setStyle(TableStyle([('LEFTPADDING', (0,0), (-1,-1), 0)]))

        # Derecha (Resto)
        ruc_content = [
            [Paragraph("BOLETA DE VENTA", ParagraphStyle('RucTitle', parent=styles['Normal'], alignment=TA_CENTER, fontSize=14, fontName='Helvetica-Bold'))],
            [Paragraph("ELECTRONICA", ParagraphStyle('RucSub', parent=styles['Normal'], alignment=TA_CENTER, fontSize=14, fontName='Helvetica-Bold'))],
            [Paragraph(f"RUC: {rfc_cliente if rfc_cliente != 'XAXX010101000' else '20123456789'}", ParagraphStyle('RucNum', parent=styles['Normal'], alignment=TA_CENTER, fontSize=14, fontName='Helvetica-Bold', spaceBefore=5))],
            [Paragraph(f"EB01-{id_transaccion}", ParagraphStyle('Folio', parent=styles['Normal'], alignment=TA_CENTER, fontSize=12, textColor=colors.navy))]
        ]
        t_ruc = Table(ruc_content, colWidths=[80*mm])
        t_ruc.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 1, COLOR_BORDE),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ]))

        # Contenedor Encabezado
        t_header = Table([[t_empresa, t_ruc]], colWidths=[200*mm, 87*mm])
        t_header.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ]))
        elementos.append(t_header)
        elementos.append(Spacer(1, 5*mm))

        # =========================================================
        # 2. DATOS DEL CLIENTE (Sin Fecha Vencimiento)
        # =========================================================
        
        fecha_emision = datetime.now().strftime("%d/%m/%Y")
        nombre_cliente_paragraph = Paragraph(f"&nbsp; {nombre_cliente}", style_data)
        
        info_data = [
            # Eliminada la fila de Fecha de Vencimiento
            [Paragraph("Fecha de Emisión", style_label), Paragraph(":", style_label), Paragraph(fecha_emision, style_data)],
            [Paragraph("Señor(es)", style_label), Paragraph(":", style_label), nombre_cliente_paragraph],
            [Paragraph("DNI / RUC", style_label), Paragraph(":", style_label), Paragraph(rfc_cliente, style_data)],
            [Paragraph("Tipo de Moneda", style_label), Paragraph(":", style_label), Paragraph("PESOS MEXICANOS", style_data)],
            [Paragraph("Observación", style_label), Paragraph(":", style_label), Paragraph("VENTA DE MERCADERÍA", style_data)],
        ]

        # Anchos Escalados: Label(35mm), Sep(3mm), Valor(Resto=249mm)
        t_info = Table(info_data, colWidths=[35*mm, 3*mm, 249*mm])
        
        t_info.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 1, COLOR_BORDE),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            # Fondo gris para nombre cliente (Fila 1 ahora, antes era 2)
            ('BACKGROUND', (2, 1), (2, 1), COLOR_FONDO_GRIS),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))
        
        elementos.append(t_info)
        elementos.append(Spacer(1, 5*mm))

        # =========================================================
        # 3. TABLA DE PRODUCTOS (Sin Código)
        # =========================================================
        
        # Columnas restantes (6 columnas)
        headers = ["Cantidad", "Unidad Medida", "Descripción", "Valor Unitario(*)", "Descuento(*)", "Importe de Venta(**)"]
        
        style_header_table = ParagraphStyle('TableHeader', parent=styles['Normal'], fontSize=8, fontName='Helvetica-Bold', alignment=TA_CENTER)
        style_cell_center = ParagraphStyle('CellC', parent=styles['Normal'], fontSize=8, fontName='Helvetica', alignment=TA_CENTER)
        style_cell_left = ParagraphStyle('CellL', parent=styles['Normal'], fontSize=8, fontName='Helvetica', alignment=TA_LEFT)
        style_cell_right = ParagraphStyle('CellR', parent=styles['Normal'], fontSize=8, fontName='Helvetica', alignment=TA_RIGHT)

        data_productos = [[Paragraph(h, style_header_table) for h in headers]]

        for item in self.carrito:
            precio_unit = item['precio']
            cant = item['cantidad']
            importe = precio_unit * cant
            
            # Eliminada la columna Código
            row = [
                Paragraph(f"{cant:.2f}", style_cell_center),
                Paragraph("UNIDAD", style_cell_center),
                Paragraph(item['nombre'], style_cell_left),
                Paragraph(f"{precio_unit:.2f}", style_cell_right),
                Paragraph("0.00", style_cell_right),
                Paragraph(f"{importe:.2f}", style_cell_right),
            ]
            data_productos.append(row)

        # ANCHOS ESCALADOS (Suma debe ser aprox 287mm)
        # Cant(25) + Unidad(35) + Desc(135!!) + Val(30) + Desc(25) + Imp(37) = 287mm
        col_widths = [25*mm, 35*mm, 135*mm, 30*mm, 25*mm, 37*mm]

        t_productos = Table(data_productos, colWidths=col_widths)
        
        t_productos.setStyle(TableStyle([
            ('LINEABOVE', (0,0), (-1,0), 0.5, colors.gray),
            ('LINEBELOW', (0,0), (-1,0), 0.5, colors.gray),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('RIGHTPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('BOX', (0,0), (-1,-1), 1, COLOR_BORDE),
            ('GRID', (0,0), (-1,-1), 0.2, colors.lightgrey),
        ]))

        elementos.append(t_productos)
        elementos.append(Spacer(1, 5*mm))

        # =========================================================
        # 4. PIE DE PÁGINA
        # =========================================================
        
        style_total_label = ParagraphStyle('TotLab', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold', alignment=TA_RIGHT)
        style_total_val = ParagraphStyle('TotVal', parent=styles['Normal'], fontSize=10, fontName='Helvetica', alignment=TA_RIGHT, textColor=colors.gray)
        
        total_str = f"S/. {self.datos_totales['total']:,.2f}"
        
        data_totales = [
            [Paragraph("Otros Cargos :", style_total_label), Paragraph("0.00", style_total_val)],
            [Paragraph("Otros Tributos :", style_total_label), Paragraph("0.00", style_total_val)],
            [Paragraph("<b>Importe Total :</b>", ParagraphStyle('T', fontSize=10, fontName='Helvetica-Bold', alignment=TA_RIGHT)), 
             Paragraph(f"<b>{total_str}</b>", ParagraphStyle('T', fontSize=10, fontName='Helvetica-Bold', alignment=TA_RIGHT, textColor=colors.gray))]
        ]

        # Tabla Totales (35mm + 35mm = 70mm)
        t_totales = Table(data_totales, colWidths=[35*mm, 35*mm])
        
        t_totales.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BACKGROUND', (1,0), (1,2), COLOR_FONDO_GRIS),
            ('BOX', (1,0), (1,0), 0.5, colors.gray),
            ('BOX', (1,1), (1,1), 0.5, colors.gray),
            ('BOX', (1,2), (1,2), 0.5, colors.gray),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('RIGHTPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ]))

        # Alineación a la derecha (Espacio vacío = 217mm, Totales = 70mm)
        t_footer_container = Table([[ "", t_totales]], colWidths=[217*mm, 70*mm])
        t_footer_container.setStyle(TableStyle([('ALIGN', (-1,0), (-1,0), 'RIGHT')]))
        
        elementos.append(t_footer_container)

        doc.build(elementos)
        return nombre_archivo

    def _abrir_archivo(self, ruta):
        try:
            if platform.system() == 'Windows':
                os.startfile(ruta)
            elif platform.system() == 'Darwin':
                subprocess.call(['open', ruta])
            else:
                subprocess.call(['xdg-open', ruta])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo: {e}")

    def _limpiar_todo(self):
        self.carrito = []
        self.descuento_global = 0.0
        self._actualizar_carrito()
        self._actualizar_totales()
        self.entrada_busqueda.delete(0, tk.END)
        self._actualizar_lista_productos()