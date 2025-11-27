import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime, timedelta
import os

# --- GRÁFICOS ---
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# --- CALENDARIO ---
from tkcalendar import DateEntry

# --- REPORTE PDF ---
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

# --- REPORTE EXCEL ---
import pandas as pd

from ui.styles import AppTheme

class PantallaDashboard(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.theme = AppTheme()
        self.db_path = "data/ventas.db"
        
        # Almacenes de memoria para el reporte
        self.figuras = {}      # Guardará los objetos Figure de matplotlib
        self.data_cache = {}   # Guardará los resultados de las queries SQL
        
        # Configurar estilo de gráficos
        plt.style.use('ggplot')
        plt.rcParams['axes.facecolor'] = '#ECEFF4'
        plt.rcParams['figure.facecolor'] = '#ECEFF4'
        plt.rcParams['text.color'] = '#2E3440'
        
        self.setup_ui()
        
    def setup_ui(self):
        # --- Barra Superior ---
        top_frame = tk.Frame(self, bg="#ECEFF4")
        top_frame.pack(fill="x", padx=20, pady=10)

        tk.Label(
            top_frame, 
            text="📊 Dashboard Financiero", 
            font=("Helvetica", 20, "bold"),
            bg="#ECEFF4", fg="#2E3440"
        ).pack(side="left")

        # --- Filtros y Botones ---
        filter_frame = tk.Frame(top_frame, bg="#ECEFF4")
        filter_frame.pack(side="right")

        hoy = datetime.now()
        inicio_mes = hoy - timedelta(days=30)

        # Filtros de Fecha
        tk.Label(filter_frame, text="Desde:", bg="#ECEFF4", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        self.cal_inicio = DateEntry(filter_frame, width=12, background='#5E81AC', foreground='white', borderwidth=2, date_pattern='y-mm-dd')
        self.cal_inicio.set_date(inicio_mes)
        self.cal_inicio.pack(side="left", padx=5)

        tk.Label(filter_frame, text="Hasta:", bg="#ECEFF4", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        self.cal_fin = DateEntry(filter_frame, width=12, background='#5E81AC', foreground='white', borderwidth=2, date_pattern='y-mm-dd')
        self.cal_fin.set_date(hoy)
        self.cal_fin.pack(side="left", padx=5)

        # Botón Actualizar
        ttk.Button(filter_frame, text="🔄 Actualizar", command=self.cargar_datos).pack(side="left", padx=10)

        # Botón Exportar (NUEVO)
        btn_export = tk.Button(
            filter_frame, 
            text="📂 Exportar Reporte", 
            font=("Arial", 9, "bold"),
            bg="#A3BE8C", fg="white", 
            activebackground="#8FBCBB",
            cursor="hand2",
            command=self.mostrar_opciones_exportar
        )
        btn_export.pack(side="left", padx=10)

        # --- KPIs ---
        self.kpi_frame = tk.Frame(self, bg="#ECEFF4")
        self.kpi_frame.pack(fill="x", padx=20, pady=5)
        
        # --- Gráficos ---
        self.charts_frame = tk.Frame(self, bg="#ECEFF4")
        self.charts_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.charts_frame.columnconfigure(0, weight=1)
        self.charts_frame.columnconfigure(1, weight=1)
        self.charts_frame.rowconfigure(0, weight=1)
        self.charts_frame.rowconfigure(1, weight=1)

        self.cargar_datos()

    def ejecutar_consulta(self, query, params=()):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def cargar_datos(self):
        fecha_ini = self.cal_inicio.get()
        fecha_fin = self.cal_fin.get()

        # Limpiar UI anterior
        for widget in self.kpi_frame.winfo_children(): widget.destroy()
        for widget in self.charts_frame.winfo_children(): widget.destroy()
        self.figuras = {} # Limpiar caché de figuras

        try:
            # --- 1. KPIs ---
            sql_total = "SELECT SUM(total) FROM Transacciones WHERE tipo='venta' AND date(fecha) BETWEEN ? AND ?"
            res_total = self.ejecutar_consulta(sql_total, (fecha_ini, fecha_fin))[0][0] or 0
            
            sql_count = "SELECT COUNT(*) FROM Transacciones WHERE tipo='venta' AND date(fecha) BETWEEN ? AND ?"
            res_count = self.ejecutar_consulta(sql_count, (fecha_ini, fecha_fin))[0][0] or 0
            
            # Guardar KPIs en memoria
            self.data_cache['kpis'] = {"total": res_total, "count": res_count, "desde": fecha_ini, "hasta": fecha_fin}

            self.crear_kpi_card(self.kpi_frame, "Ingresos Totales", f"${res_total:,.2f}", "💰", "#A3BE8C")
            self.crear_kpi_card(self.kpi_frame, "Ventas Realizadas", f"{res_count}", "🧾", "#5E81AC")
            self.crear_kpi_card(self.kpi_frame, "Periodo Analizado", f"{fecha_ini} a {fecha_fin}", "📅", "#B48EAD")

            # --- 2. Top Productos (Pie) ---
            sql_prod = """
                SELECT p.nombre, SUM(d.cantidad) as total_qty
                FROM Detalle_transaccion d
                JOIN Productos p ON d.id_producto = p.id_producto
                JOIN Transacciones t ON d.id_transaccion = t.id_transaccion
                WHERE t.tipo='venta' AND date(t.fecha) BETWEEN ? AND ?
                GROUP BY p.id_producto ORDER BY total_qty DESC LIMIT 5
            """
            data_prod = self.ejecutar_consulta(sql_prod, (fecha_ini, fecha_fin))
            self.data_cache['productos'] = data_prod
            self.generar_grafico_pastel(data_prod, 0, 0, "Top 5 Productos", "chart_prod")

            # --- 3. Top Clientes (Barras) ---
            sql_cli = """
                SELECT c.nombres || ' ' || IFNULL(c.apellido_p, ''), SUM(t.total)
                FROM Transacciones t
                JOIN Clientes c ON t.id_cliente = c.id_cliente
                WHERE t.tipo='venta' AND date(t.fecha) BETWEEN ? AND ?
                GROUP BY c.id_cliente ORDER BY SUM(t.total) DESC LIMIT 5
            """
            data_cli = self.ejecutar_consulta(sql_cli, (fecha_ini, fecha_fin))
            self.data_cache['clientes'] = data_cli
            self.generar_grafico_barras(data_cli, 0, 1, "Top Clientes ($)", "chart_cli")

            # --- 4. Proveedores (Dona) ---
            sql_prov = """
                SELECT pr.nombre, COUNT(p.id_producto)
                FROM Productos p
                JOIN Proveedores pr ON p.id_proveedor = pr.id_proveedor
                GROUP BY pr.id_proveedor
            """
            data_prov = self.ejecutar_consulta(sql_prov)
            self.data_cache['proveedores'] = data_prov
            self.generar_grafico_dona(data_prov, 1, 0, "Catálogo x Proveedor", "chart_prov")

            # --- 5. Ventas x Día (Línea) ---
            sql_tiempo = """
                SELECT date(fecha), SUM(total)
                FROM Transacciones
                WHERE tipo='venta' AND date(fecha) BETWEEN ? AND ?
                GROUP BY date(fecha) ORDER BY date(fecha)
            """
            data_tiempo = self.ejecutar_consulta(sql_tiempo, (fecha_ini, fecha_fin))
            self.data_cache['tiempo'] = data_tiempo
            self.generar_grafico_linea(data_tiempo, 1, 1, "Evolución Ventas", "chart_time")

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar datos: {e}")

    # --- UI Helpers ---
    def crear_kpi_card(self, parent, titulo, valor, icono, color_bg):
        frame = tk.Frame(parent, bg=color_bg, padx=15, pady=10)
        frame.pack(side="left", fill="x", expand=True, padx=5)
        tk.Label(frame, text=icono, font=("Segoe UI Emoji", 24), bg=color_bg, fg="white").pack(side="left")
        right = tk.Frame(frame, bg=color_bg)
        right.pack(side="right", fill="both")
        tk.Label(right, text=titulo, font=("Helvetica", 10), bg=color_bg, fg="white").pack(anchor="e")
        tk.Label(right, text=valor, font=("Helvetica", 16, "bold"), bg=color_bg, fg="white").pack(anchor="e")

    def dibujar_canvas(self, fig, row, col):
        canvas = FigureCanvasTkAgg(fig, master=self.charts_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

    # --- Generadores de Gráficos (Ahora guardan la figura en self.figuras) ---
    def generar_grafico_pastel(self, datos, row, col, titulo, key):
        if not datos: return
        labels = [str(r[0])[:15] for r in datos]
        sizes = [r[1] for r in datos]
        colors = ['#BF616A', '#D08770', '#EBCB8B', '#A3BE8C', '#B48EAD']
        
        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=45, colors=colors)
        ax.set_title(titulo, fontsize=10)
        
        self.figuras[key] = fig # Guardar para reporte
        self.dibujar_canvas(fig, row, col)

    def generar_grafico_barras(self, datos, row, col, titulo, key):
        if not datos: return
        labels = [str(r[0]) for r in datos]
        values = [r[1] for r in datos]
        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.barh(labels, values, color='#5E81AC')
        ax.set_title(titulo, fontsize=10)
        ax.invert_yaxis()
        self.figuras[key] = fig
        self.dibujar_canvas(fig, row, col)

    def generar_grafico_dona(self, datos, row, col, titulo, key):
        if not datos: return
        labels = [str(r[0]) for r in datos]
        sizes = [r[1] for r in datos]
        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.pie(sizes, labels=labels, autopct='%1.0f%%', pctdistance=0.85)
        ax.add_artist(plt.Circle((0,0),0.70,fc='#ECEFF4'))
        ax.set_title(titulo, fontsize=10)
        self.figuras[key] = fig
        self.dibujar_canvas(fig, row, col)

    def generar_grafico_linea(self, datos, row, col, titulo, key):
        if not datos: return
        fechas = [r[0][5:] for r in datos]
        valores = [r[1] for r in datos]
        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(fechas, valores, marker='o', color='#BF616A')
        ax.set_title(titulo, fontsize=10)
        if len(fechas) > 5: plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)
        self.figuras[key] = fig
        self.dibujar_canvas(fig, row, col)

    # =======================================================
    #              MÓDULO DE EXPORTACIÓN
    # =======================================================
    
    def mostrar_opciones_exportar(self):
        """Popup para elegir PDF o Excel"""
        popup = tk.Toplevel(self)
        popup.title("Exportar Reporte")
        popup.geometry("300x150")
        popup.resizable(False, False)
        
        # Centrar
        x = self.winfo_rootx() + 50
        y = self.winfo_rooty() + 50
        popup.geometry(f"+{x}+{y}")
        
        tk.Label(popup, text="Seleccione el formato:", font=("Arial", 11, "bold")).pack(pady=15)
        
        frame_btns = tk.Frame(popup)
        frame_btns.pack(pady=10)
        
        tk.Button(
            frame_btns, text="📄 PDF (Detallado)", 
            bg="#BF616A", fg="white", font=("Arial", 10),
            command=lambda: [popup.destroy(), self.generar_reporte_pdf()]
        ).pack(side="left", padx=10)
        
        tk.Button(
            frame_btns, text="📊 Excel (Datos)", 
            bg="#A3BE8C", fg="white", font=("Arial", 10),
            command=lambda: [popup.destroy(), self.generar_reporte_excel()]
        ).pack(side="left", padx=10)

    def generar_reporte_pdf(self):
        """Genera un PDF A4 con KPIs, Gráficos y Tablas"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF Document", "*.pdf")],
                title="Guardar Reporte",
                initialfile=f"Reporte_Ventas_{datetime.now().strftime('%Y%m%d')}.pdf"
            )
            if not filename: return

            # Guardar imágenes de gráficos temporalmente
            temp_images = []
            for key, fig in self.figuras.items():
                temp_path = f"temp_{key}.png"
                fig.savefig(temp_path, format='png', bbox_inches='tight')
                temp_images.append(temp_path)

            # --- Crear PDF ---
            doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm)
            elements = []
            styles = getSampleStyleSheet()
            
            # Encabezado
            elements.append(Paragraph("<b>REPORTE GERENCIAL DE VENTAS</b>", styles["Title"]))
            elements.append(Spacer(1, 5*mm))
            
            kpi = self.data_cache.get('kpis', {})
            txt_resumen = f"""
            <b>Periodo:</b> {kpi.get('desde')} al {kpi.get('hasta')}<br/>
            <b>Total Ingresos:</b> ${kpi.get('total', 0):,.2f}<br/>
            <b>Total Operaciones:</b> {kpi.get('count', 0)}
            """
            elements.append(Paragraph(txt_resumen, styles["Normal"]))
            elements.append(Spacer(1, 10*mm))

            # --- SECCIÓN 1: PRODUCTOS ---
            elements.append(Paragraph("<b>1. Desempeño de Productos</b>", styles["Heading2"]))
            # Imagen
            if 'chart_prod' in self.figuras:
                elements.append(RLImage("temp_chart_prod.png", width=120*mm, height=80*mm))
            # Tabla Detallada
            data_prod = [["Producto", "Cantidad Vendida"]] + [[str(p[0]), str(p[1])] for p in self.data_cache.get('productos', [])]
            t_prod = Table(data_prod, colWidths=[100*mm, 40*mm])
            t_prod.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#5E81AC")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ]))
            elements.append(Spacer(1, 5*mm))
            elements.append(t_prod)
            elements.append(Spacer(1, 10*mm))

            # --- SECCIÓN 2: CLIENTES ---
            elements.append(Paragraph("<b>2. Clientes Estrella</b>", styles["Heading2"]))
            if 'chart_cli' in self.figuras:
                elements.append(RLImage("temp_chart_cli.png", width=120*mm, height=80*mm))
            
            data_cli = [["Cliente", "Total Comprado ($)"]] + [[str(c[0]), f"${c[1]:,.2f}"] for c in self.data_cache.get('clientes', [])]
            t_cli = Table(data_cli, colWidths=[100*mm, 40*mm])
            t_cli.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#A3BE8C")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ]))
            elements.append(Spacer(1, 5*mm))
            elements.append(t_cli)

            doc.build(elements)
            
            # Limpiar temporales
            for img in temp_images:
                if os.path.exists(img): os.remove(img)

            messagebox.showinfo("Éxito", "Reporte PDF generado correctamente.")
            os.startfile(filename)

        except Exception as e:
            messagebox.showerror("Error PDF", str(e))

    def generar_reporte_excel(self):
        """Genera un Excel con múltiples hojas usando Pandas"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel File", "*.xlsx")],
                title="Guardar Excel",
                initialfile=f"Data_Ventas_{datetime.now().strftime('%Y%m%d')}.xlsx"
            )
            if not filename: return

            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Hoja 1: Resumen
                kpi = self.data_cache.get('kpis', {})
                df_kpi = pd.DataFrame([kpi])
                df_kpi.to_excel(writer, sheet_name="Resumen", index=False)

                # Hoja 2: Productos
                data_prod = self.data_cache.get('productos', [])
                df_prod = pd.DataFrame(data_prod, columns=["Producto", "Cantidad"])
                df_prod.to_excel(writer, sheet_name="Top Productos", index=False)

                # Hoja 3: Clientes
                data_cli = self.data_cache.get('clientes', [])
                df_cli = pd.DataFrame(data_cli, columns=["Cliente", "Total Comprado"])
                df_cli.to_excel(writer, sheet_name="Top Clientes", index=False)

                # Hoja 4: Tendencia
                data_time = self.data_cache.get('tiempo', [])
                df_time = pd.DataFrame(data_time, columns=["Fecha", "Venta Total"])
                df_time.to_excel(writer, sheet_name="Ventas Diarias", index=False)

            messagebox.showinfo("Éxito", "Reporte Excel generado correctamente.")
            os.startfile(filename)

        except Exception as e:
            messagebox.showerror("Error Excel", f"No se pudo generar el Excel.\nAsegúrese de tener 'pandas' y 'openpyxl' instalados.\nError: {e}")