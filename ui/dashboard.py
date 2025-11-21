import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from tkcalendar import DateEntry  # <--- IMPORTANTE: Librería del calendario
from ui.styles import AppTheme

class PantallaDashboard(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.theme = AppTheme()
        self.db_path = "data/ventas.db"
        
        # Configurar estilo de gráficos
        plt.style.use('ggplot')
        plt.rcParams['axes.facecolor'] = '#ECEFF4'
        plt.rcParams['figure.facecolor'] = '#ECEFF4'
        plt.rcParams['text.color'] = '#2E3440'
        
        self.setup_ui()
        
    def setup_ui(self):
        # --- Barra Superior: Título y Filtros ---
        top_frame = tk.Frame(self, bg="#ECEFF4")
        top_frame.pack(fill="x", padx=20, pady=10)

        tk.Label(
            top_frame, 
            text="📊 Dashboard Financiero", 
            font=("Helvetica", 20, "bold"),
            bg="#ECEFF4", fg="#2E3440"
        ).pack(side="left")

        # --- Filtros con Calendario ---
        filter_frame = tk.Frame(top_frame, bg="#ECEFF4")
        filter_frame.pack(side="right")

        # Fechas por defecto
        hoy = datetime.now()
        inicio_mes = hoy - timedelta(days=30)

        # 1. Selector Fecha Inicio
        tk.Label(filter_frame, text="Desde:", bg="#ECEFF4", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        
        self.cal_inicio = DateEntry(
            filter_frame, 
            width=12, 
            background='#5E81AC', # Color azul nórdico
            foreground='white', 
            borderwidth=2,
            date_pattern='y-mm-dd', # Formato compatible con SQL (2023-12-31)
            font=("Arial", 10)
        )
        self.cal_inicio.set_date(inicio_mes) # Establecer fecha inicial
        self.cal_inicio.pack(side="left", padx=5)

        # 2. Selector Fecha Fin
        tk.Label(filter_frame, text="Hasta:", bg="#ECEFF4", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        
        self.cal_fin = DateEntry(
            filter_frame, 
            width=12, 
            background='#5E81AC',
            foreground='white', 
            borderwidth=2,
            date_pattern='y-mm-dd',
            font=("Arial", 10)
        )
        self.cal_fin.set_date(hoy) # Establecer fecha hoy
        self.cal_fin.pack(side="left", padx=5)

        # Botón Generar
        ttk.Button(
            filter_frame, 
            text="🔄 Actualizar", 
            command=self.cargar_datos
        ).pack(side="left", padx=15)

        # --- Área de Resumen (KPI Cards) ---
        self.kpi_frame = tk.Frame(self, bg="#ECEFF4")
        self.kpi_frame.pack(fill="x", padx=20, pady=5)
        
        # --- Área de Gráficos (Grid) ---
        self.charts_frame = tk.Frame(self, bg="#ECEFF4")
        self.charts_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Configurar grid 2x2 para gráficos
        self.charts_frame.columnconfigure(0, weight=1)
        self.charts_frame.columnconfigure(1, weight=1)
        self.charts_frame.rowconfigure(0, weight=1)
        self.charts_frame.rowconfigure(1, weight=1)

        # Cargar datos iniciales
        self.cargar_datos()

    def crear_kpi_card(self, parent, titulo, valor, icono, color_bg):
        frame = tk.Frame(parent, bg=color_bg, padx=15, pady=10)
        frame.pack(side="left", fill="x", expand=True, padx=5)
        
        # Icono
        tk.Label(frame, text=icono, font=("Segoe UI Emoji", 24), bg=color_bg, fg="white").pack(side="left")
        
        # Texto
        right = tk.Frame(frame, bg=color_bg)
        right.pack(side="right", fill="both")
        
        tk.Label(right, text=titulo, font=("Helvetica", 10), bg=color_bg, fg="white").pack(anchor="e")
        tk.Label(right, text=valor, font=("Helvetica", 16, "bold"), bg=color_bg, fg="white").pack(anchor="e")

    def ejecutar_consulta(self, query, params=()):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def cargar_datos(self):
        # Obtener fechas directamente del widget DateEntry
        # Gracias a date_pattern='y-mm-dd', .get() ya devuelve el string correcto para SQL
        fecha_ini = self.cal_inicio.get()
        fecha_fin = self.cal_fin.get()

        # Limpiar widgets anteriores
        for widget in self.kpi_frame.winfo_children(): widget.destroy()
        for widget in self.charts_frame.winfo_children(): widget.destroy()

        try:
            # --- KPIS ---
            # Total Ventas
            sql_total = "SELECT SUM(total) FROM Transacciones WHERE tipo='venta' AND date(fecha) BETWEEN ? AND ?"
            res_total = self.ejecutar_consulta(sql_total, (fecha_ini, fecha_fin))[0][0] or 0
            
            # Cantidad Ventas
            sql_count = "SELECT COUNT(*) FROM Transacciones WHERE tipo='venta' AND date(fecha) BETWEEN ? AND ?"
            res_count = self.ejecutar_consulta(sql_count, (fecha_ini, fecha_fin))[0][0] or 0

            self.crear_kpi_card(self.kpi_frame, "Ingresos Totales", f"${res_total:,.2f}", "💰", "#A3BE8C") # Verde
            self.crear_kpi_card(self.kpi_frame, "Ventas Realizadas", f"{res_count}", "🧾", "#5E81AC") # Azul
            self.crear_kpi_card(self.kpi_frame, "Periodo", f"Del {fecha_ini}", "📅", "#B48EAD") # Morado

            # --- GRAFICOS ---

            # 1. Top 5 Productos (Pie)
            sql_prod = """
                SELECT p.nombre, SUM(d.cantidad) as total_qty
                FROM Detalle_transaccion d
                JOIN Productos p ON d.id_producto = p.id_producto
                JOIN Transacciones t ON d.id_transaccion = t.id_transaccion
                WHERE t.tipo='venta' AND date(t.fecha) BETWEEN ? AND ?
                GROUP BY p.id_producto
                ORDER BY total_qty DESC
                LIMIT 5
            """
            data_prod = self.ejecutar_consulta(sql_prod, (fecha_ini, fecha_fin))
            self.generar_grafico_pastel(data_prod, 0, 0, "Top 5 Productos Más Vendidos")

            # 2. Top 5 Clientes (Barras)
            sql_cli = """
                SELECT c.nombres || ' ' || IFNULL(c.apellido_p, ''), SUM(t.total)
                FROM Transacciones t
                JOIN Clientes c ON t.id_cliente = c.id_cliente
                WHERE t.tipo='venta' AND date(t.fecha) BETWEEN ? AND ?
                GROUP BY c.id_cliente
                ORDER BY SUM(t.total) DESC
                LIMIT 5
            """
            data_cli = self.ejecutar_consulta(sql_cli, (fecha_ini, fecha_fin))
            self.generar_grafico_barras(data_cli, 0, 1, "Top 5 Clientes ($)")

            # 3. Proveedores (Dona) - Inventario Global
            sql_prov = """
                SELECT pr.nombre, COUNT(p.id_producto)
                FROM Productos p
                JOIN Proveedores pr ON p.id_proveedor = pr.id_proveedor
                GROUP BY pr.id_proveedor
            """
            data_prov = self.ejecutar_consulta(sql_prov)
            self.generar_grafico_dona(data_prov, 1, 0, "Distribución por Proveedor")
            
            # 4. Ventas por día (Línea) - Nuevo Gráfico extra
            sql_tiempo = """
                SELECT date(fecha), SUM(total)
                FROM Transacciones
                WHERE tipo='venta' AND date(fecha) BETWEEN ? AND ?
                GROUP BY date(fecha)
                ORDER BY date(fecha)
            """
            data_tiempo = self.ejecutar_consulta(sql_tiempo, (fecha_ini, fecha_fin))
            self.generar_grafico_linea(data_tiempo, 1, 1, "Tendencia de Ventas")

        except Exception as e:
            messagebox.showerror("Error Dashboard", f"No se pudieron cargar los datos: {str(e)}")

    # --- Funciones de Dibujo de Gráficos ---

    def generar_grafico_pastel(self, datos, row, col, titulo):
        if not datos: return self.mostrar_no_data(row, col, titulo)
        
        labels = [str(r[0])[:15] for r in datos] # Recortar nombres largos
        sizes = [r[1] for r in datos]
        colors = ['#BF616A', '#D08770', '#EBCB8B', '#A3BE8C', '#B48EAD']

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=45, colors=colors)
        ax.set_title(titulo, fontsize=10)

        self.dibujar_canvas(fig, row, col)

    def generar_grafico_barras(self, datos, row, col, titulo):
        if not datos: return self.mostrar_no_data(row, col, titulo)
        
        labels = [str(r[0]) for r in datos]
        values = [r[1] for r in datos]

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.barh(labels, values, color='#5E81AC')
        ax.set_title(titulo, fontsize=10)
        ax.invert_yaxis()
        
        # Formato moneda en eje X
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        plt.setp(ax.get_xticklabels(), rotation=0, fontsize=8)

        self.dibujar_canvas(fig, row, col)

    def generar_grafico_dona(self, datos, row, col, titulo):
        if not datos: return self.mostrar_no_data(row, col, titulo)
        
        labels = [str(r[0]) for r in datos]
        sizes = [r[1] for r in datos]
        colors = ['#8FBCBB', '#88C0D0', '#81A1C1', '#5E81AC']

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.pie(sizes, labels=labels, autopct='%1.0f%%', pctdistance=0.85, colors=colors)
        # Círculo central
        ax.add_artist(plt.Circle((0,0),0.70,fc='#ECEFF4'))
        ax.set_title(titulo, fontsize=10)

        self.dibujar_canvas(fig, row, col)

    def generar_grafico_linea(self, datos, row, col, titulo):
        # Si hay pocos datos o ninguno, manejarlo
        if not datos: 
            return self.mostrar_no_data(row, col, titulo)

        fechas = [r[0][5:] for r in datos] # Solo Mes-Dia para que quepa
        valores = [r[1] for r in datos]

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(fechas, valores, marker='o', linestyle='-', color='#BF616A', linewidth=2)
        ax.fill_between(fechas, valores, color='#BF616A', alpha=0.3)
        ax.set_title(titulo, fontsize=10)
        
        # Rotar fechas si son muchas
        if len(fechas) > 5:
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)

        self.dibujar_canvas(fig, row, col)

    def mostrar_no_data(self, row, col, titulo):
        frame = tk.Frame(self.charts_frame, bg="#ECEFF4")
        frame.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
        tk.Label(frame, text=titulo, font=("Arial", 10, "bold"), bg="#ECEFF4").pack(pady=5)
        tk.Label(frame, text="(Sin datos para este periodo)", font=("Arial", 9, "italic"), bg="#ECEFF4", fg="#999").pack(expand=True)

    def dibujar_canvas(self, fig, row, col):
        canvas = FigureCanvasTkAgg(fig, master=self.charts_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=row, column=col, padx=10, pady=10, sticky="nsew")