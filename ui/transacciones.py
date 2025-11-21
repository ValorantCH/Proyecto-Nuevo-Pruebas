import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
from tkcalendar import DateEntry  # <--- Requisito cumplido
from ui.styles import AppTheme

class PantallaTransacciones(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.theme = AppTheme()
        self.db_path = "data/ventas.db"
        
        self.setup_ui()
        self.cargar_transacciones()

    def setup_ui(self):
        # ==========================================
        # 1. PANEL SUPERIOR (Título y Filtros)
        # ==========================================
        top_frame = tk.Frame(self, bg="#ECEFF4", pady=20, padx=20)
        top_frame.pack(fill="x")

        # Título con Icono
        tk.Label(
            top_frame, 
            text="📄 Historial de Transacciones", 
            font=("Helvetica", 20, "bold"),
            bg="#ECEFF4", fg="#2E3440"
        ).pack(side="left")

        # Contenedor de Filtros (Alineado a la derecha)
        filter_container = tk.Frame(top_frame, bg="#ECEFF4")
        filter_container.pack(side="right")

        # --- Filtro: Fechas (Calendarios) ---
        # Fecha Inicio
        tk.Label(filter_container, text="Desde:", bg="#ECEFF4", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        
        inicio_mes = datetime.now() - timedelta(days=30)
        self.cal_inicio = DateEntry(
            filter_container,
            width=12,
            background='#5E81AC', # Color Azul Nórdico
            foreground='white',
            borderwidth=2,
            date_pattern='y-mm-dd', # Formato SQL (2023-12-31)
            font=("Arial", 10),
            headersbackground='#4C566A',
            headersforeground='white'
        )
        self.cal_inicio.set_date(inicio_mes)
        self.cal_inicio.pack(side="left", padx=5)

        # Fecha Fin
        tk.Label(filter_container, text="Hasta:", bg="#ECEFF4", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        
        self.cal_fin = DateEntry(
            filter_container,
            width=12,
            background='#5E81AC',
            foreground='white',
            borderwidth=2,
            date_pattern='y-mm-dd',
            font=("Arial", 10),
            headersbackground='#4C566A',
            headersforeground='white'
        )
        self.cal_fin.set_date(datetime.now())
        self.cal_fin.pack(side="left", padx=5)

        # --- Filtro: Buscador ---
        tk.Label(filter_container, text="Cliente:", bg="#ECEFF4", font=("Arial", 10)).pack(side="left", padx=(15, 5))
        
        self.entry_buscar = ttk.Entry(filter_container, width=20, font=("Arial", 10))
        self.entry_buscar.pack(side="left", padx=5)
        
        # Permitir buscar con Enter
        self.entry_buscar.bind('<Return>', lambda e: self.cargar_transacciones())

        # Botón Buscar
        ttk.Button(
            filter_container, 
            text="🔍 Buscar", 
            command=self.cargar_transacciones
        ).pack(side="left", padx=10)

        # ==========================================
        # 2. PANEL CENTRAL (Tabla)
        # ==========================================
        table_frame = tk.Frame(self, bg="#ECEFF4", padx=20, pady=10)
        table_frame.pack(fill="both", expand=True)

        columns = ("ID", "Fecha", "Cliente", "Tipo", "Total", "Estado")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side="right", fill="y")

        # Treeview
        self.tree = ttk.Treeview(
            table_frame, 
            columns=columns, 
            show="headings", 
            selectmode="browse",
            yscrollcommand=scrollbar.set
        )
        
        scrollbar.config(command=self.tree.yview)

        # Configurar Cabeceras
        headers = [
            ("ID", 60, "center"),
            ("Fecha", 150, "center"),
            ("Cliente", 250, "w"),
            ("Tipo", 100, "center"),
            ("Total", 100, "e"),
            ("Estado", 100, "center")
        ]

        for col, width, anchor in headers:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor=anchor)

        self.tree.pack(side="left", fill="both", expand=True)
        
        # Doble click para detalles
        self.tree.bind("<Double-1>", self.ver_detalles)

        # ==========================================
        # 3. PANEL INFERIOR (Botones de Acción)
        # ==========================================
        actions_frame = tk.Frame(self, bg="#ECEFF4", pady=15, padx=20)
        actions_frame.pack(fill="x")

        ttk.Button(
            actions_frame, 
            text="📄 Ver Detalle Recibo", 
            command=self.ver_detalles
        ).pack(side="right")

        ttk.Button(
            actions_frame, 
            text="🔄 Refrescar", 
            command=self.cargar_transacciones
        ).pack(side="right", padx=10)

    # --- LÓGICA DE DATOS ---

    def ejecutar_consulta(self, query, params=()):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Error BD", str(e))
            return []

    def cargar_transacciones(self):
        # Limpiar tabla actual
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Obtener datos de los filtros
        fecha_ini = self.cal_inicio.get()
        fecha_fin = self.cal_fin.get()
        busqueda = f"%{self.entry_buscar.get()}%"

        query = """
            SELECT 
                t.id_transaccion, 
                t.fecha,
                CASE 
                    WHEN t.id_cliente IS NOT NULL THEN c.nombres || ' ' || IFNULL(c.apellido_p, '') 
                    ELSE 'Público General' 
                END as ClienteNombre,
                t.tipo,
                t.total,
                t.estado
            FROM Transacciones t
            LEFT JOIN Clientes c ON t.id_cliente = c.id_cliente
            WHERE date(t.fecha) BETWEEN ? AND ?
            AND (ClienteNombre LIKE ? OR t.id_transaccion LIKE ?)
            ORDER BY t.fecha DESC
        """

        # Buscamos por nombre O por ID de transacción
        datos = self.ejecutar_consulta(query, (fecha_ini, fecha_fin, busqueda, busqueda))

        for fila in datos:
            # Formatear el total con signo de moneda
            fila_lista = list(fila)
            total_val = fila_lista[4]
            fila_lista[4] = f"${total_val:,.2f}"
            
            # Insertar en tabla
            self.tree.insert("", "end", values=fila_lista)

    def ver_detalles(self, event=None):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Seleccione una transacción para ver los detalles.")
            return

        item = self.tree.item(seleccion[0])
        datos = item['values']
        
        id_transaccion = datos[0]
        cliente_nombre = datos[2]
        fecha = datos[1]
        total_global = datos[4]

        self.mostrar_popup_detalle(id_transaccion, cliente_nombre, fecha, total_global)

    def mostrar_popup_detalle(self, id_tx, cliente, fecha, total):
        # Crear ventana flotante con estilo
        popup = tk.Toplevel(self)
        popup.title(f"Ticket de Venta #{id_tx}")
        popup.geometry("500x600")
        popup.configure(bg="white")
        popup.resizable(False, True)

        # --- Encabezado del Ticket ---
        header = tk.Frame(popup, bg="#ECEFF4", pady=20)
        header.pack(fill="x")

        tk.Label(header, text="🛒 SISTEMA DE VENTAS", font=("Helvetica", 10, "bold"), bg="#ECEFF4", fg="#4C566A").pack()
        tk.Label(header, text=f"Recibo de Venta #{id_tx}", font=("Helvetica", 16, "bold"), bg="#ECEFF4", fg="#2E3440").pack(pady=(5,0))
        
        info_frame = tk.Frame(popup, bg="white", pady=15, padx=20)
        info_frame.pack(fill="x")
        
        tk.Label(info_frame, text=f"Fecha de Emisión: {fecha}", bg="white", font=("Arial", 10)).pack(anchor="w")
        tk.Label(info_frame, text=f"Cliente: {cliente}", bg="white", font=("Arial", 10, "bold")).pack(anchor="w")
        
        ttk.Separator(popup, orient='horizontal').pack(fill='x', padx=20)

        # --- Lista de Productos ---
        tree_frame = tk.Frame(popup, bg="white", padx=20, pady=10)
        tree_frame.pack(fill="both", expand=True)

        cols = ("Prod", "Cant", "Total")
        tree_det = ttk.Treeview(tree_frame, columns=cols, show="headings", height=10)
        
        tree_det.heading("Prod", text="Producto")
        tree_det.heading("Cant", text="Cant.")
        tree_det.heading("Total", text="Importe")
        
        tree_det.column("Prod", width=240)
        tree_det.column("Cant", width=60, anchor="center")
        tree_det.column("Total", width=80, anchor="e")
        
        tree_det.pack(fill="both", expand=True)

        # Cargar detalle desde BD
        query = """
            SELECT p.nombre, dt.cantidad, (dt.cantidad * dt.precio_unitario)
            FROM Detalle_transaccion dt
            JOIN Productos p ON dt.id_producto = p.id_producto
            WHERE dt.id_transaccion = ?
        """
        detalles = self.ejecutar_consulta(query, (id_tx,))

        for det in detalles:
            tree_det.insert("", "end", values=(
                det[0],
                det[1],
                f"${det[2]:,.2f}"
            ))

        # --- Total y Cierre ---
        footer = tk.Frame(popup, bg="#ECEFF4", pady=20, padx=30)
        footer.pack(fill="x", side="bottom")

        # Total Grande
        total_frame = tk.Frame(footer, bg="#ECEFF4")
        total_frame.pack(fill="x")
        
        tk.Label(total_frame, text="TOTAL PAGADO", font=("Arial", 10), bg="#ECEFF4", fg="#4C566A").pack(side="left")
        tk.Label(total_frame, text=total, font=("Helvetica", 22, "bold"), bg="#ECEFF4", fg="#BF616A").pack(side="right") # Color Rojo Nórdico

        ttk.Separator(footer, orient='horizontal').pack(fill='x', pady=10)
        
        ttk.Button(footer, text="Cerrar Recibo", command=popup.destroy).pack()