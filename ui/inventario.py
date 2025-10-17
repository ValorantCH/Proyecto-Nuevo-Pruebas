import tkinter as tk
from tkinter import ttk
from db.db import obtener_datos
from ui.styles import AppTheme
from utils import helpers
from ui.dialogos.dialogo_movimientos import DialogoMovimiento


class PantallaInventario(ttk.Frame):
    COLUMNAS = {
        'Básico': [
            ('id_producto', 'ID', 60),
            ('nombre', 'Producto', 200),
            ('categoria', 'Categoría', 150),
            ('proveedor', 'Proveedor', 150),
            ('stock_actual', 'Stock', 80),
            ('stock_minimo', 'Mínimo', 80),
            ('stock_maximo', 'Máximo', 80),
            ('precio_venta', 'P. Venta', 100),
            ('costo', 'Costo', 100),
            ('sku', 'SKU', 120),
            ('codigo_barras', 'Código Barras', 150),
            ('estado', 'Estado', 80)
        ]
    }

    def __init__(self, parent):
        super().__init__(parent)
        self.theme = AppTheme()
        self.productos = []
        self.categorias = []
        self.sort_column = 'id_producto'
        self.sort_ascending = True
        self.columnas_visibles = {'Básico': True}
        
        self._cargar_datos()
        self._crear_widgets()
        self._actualizar_tabla()

    def _cargar_datos(self):
        self.productos = obtener_datos("""
            SELECT 
                p.id_producto,          -- Índice 0
                p.nombre,               -- 1
                c.nombre,               -- 2 (categoría)
                pr.nombre,              -- 3 (proveedor)
                p.stock_actual,         -- 4
                p.stock_minimo,         -- 5
                p.stock_maximo,         -- 6
                p.precio_venta,         -- 7
                p.costo,                -- 8
                p.sku,                  -- 9
                p.codigo_barras,        -- 10
                p.estado                -- 11
            FROM Productos p
            LEFT JOIN Categorias c ON p.id_categoria = c.id_categoria
            LEFT JOIN Proveedores pr ON p.id_proveedor = pr.id_proveedor
            ORDER BY {}
            """.format(f"{self.sort_column} {'ASC' if self.sort_ascending else 'DESC'}")
        )
            
        raw_categorias = obtener_datos("SELECT id_categoria, nombre FROM Categorias")
        self.categorias = helpers.obtener_opciones_categorias(raw_categorias)

    def _crear_widgets(self):
        controles_frame = ttk.Frame(self)
        controles_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(controles_frame, text="Categoría:").pack(side=tk.LEFT)
        self.combo_categorias = ttk.Combobox(
            controles_frame,
            values=self.categorias,
            state="readonly"
        )
        self.combo_categorias.current(0)
        self.combo_categorias.pack(side=tk.LEFT, padx=5)
        self.combo_categorias.bind("<<ComboboxSelected>>", self._aplicar_filtros)
        
        ttk.Label(controles_frame, text="Buscar:").pack(side=tk.LEFT, padx=10)
        self.entrada_busqueda = ttk.Entry(controles_frame)
        self.entrada_busqueda.pack(side=tk.LEFT, padx=5)
        self.entrada_busqueda.bind("<KeyRelease>", self._aplicar_filtros)
        
        btn_entrada = ttk.Button(
            controles_frame,
            text="➕ Nueva Entrada",
            style="Primary.TButton",
            command=self._abrir_dialogo_movimiento
        )
        btn_entrada.pack(side=tk.RIGHT, padx=5)

        self._configurar_tabla()

    def _configurar_tabla(self):
        self.tabla_frame = ttk.Frame(self)
        self.tabla_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(self.tabla_frame, orient=tk.VERTICAL)
        
        todas_las_columnas = [
            col[0] 
            for grupo in self.COLUMNAS.values() 
            for col in grupo
        ]
        
        self.tabla = ttk.Treeview(
            self.tabla_frame,
            columns=todas_las_columnas,
            show="headings",
            yscrollcommand=scrollbar.set,
            selectmode="browse"
        )
        
        for grupo in self.COLUMNAS.values():
            for col_id, col_text, width in grupo:
                self.tabla.heading(col_id, text=col_text, 
                                command=lambda c=col_id: self._ordenar_por_columna(c))
                self.tabla.column(col_id, width=width, anchor=tk.CENTER)
        
        scrollbar.config(command=self.tabla.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.tabla.tag_configure('bajo_stock', foreground='#bf616a')
        self.tabla.tag_configure('minimo_stock', foreground='#ebcb8b')
        self.tabla.tag_configure('inactivo', foreground='#bf616a')

    def _ordenar_por_columna(self, columna):
        """Maneja el ordenamiento al hacer click en encabezados"""
        if columna == self.sort_column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = columna
            self.sort_ascending = True
            
        # Mapeo de columnas a índices
        column_map = {
            'id_producto': 0,
            'nombre': 1,
            'categoria': 2,
            'proveedor': 3,
            'stock_actual': 4,
            'stock_minimo': 5,
            'stock_maximo': 6,
            'precio_venta': 7,
            'costo': 8,
            'sku': 9,
            'codigo_barras': 10,
            'estado': 11
        }
        
        reverse = not self.sort_ascending
        self.productos.sort(
            key=lambda x: (
                str(x[column_map[columna]]).lower() 
                if columna in ['nombre', 'categoria', 'proveedor'] 
                else x[column_map[columna]]
            ),
            reverse=reverse
        )
        
        self._actualizar_tabla()
        self._actualizar_indicador_orden(columna)

    def _actualizar_indicador_orden(self, columna):
        """Actualiza flechas de ordenamiento"""
        for col in self.tabla["columns"]:
            current_text = self.tabla.heading(col)["text"]
            self.tabla.heading(col, text=current_text.rstrip(' ↑↓'))
            
        arrow = ' ↑' if self.sort_ascending else ' ↓'
        new_text = self.tabla.heading(columna)["text"] + arrow
        self.tabla.heading(columna, text=new_text)

    def _actualizar_tabla(self, datos=None):
        self.tabla.delete(*self.tabla.get_children())
        datos = datos or self.productos
        
        for prod in datos:
            stock_actual = prod[4]
            stock_minimo = prod[5]
            tags = []

            # Determinar tacg
            if stock_actual < stock_minimo:
                tags.append('bajo_stock')
            elif stock_actual == stock_minimo:
                tags.append('minimo_stock')
            if prod[11] != 1:  # Estado inactivo
                tags.append('inactivo')

            # Construir lista de valores con TODOS los campos
            valores = [
                prod[0],        # id_producto
                prod[1],        # nombre
                prod[2] or "-", # categoria
                prod[3] or "-", # proveedor
                helpers.formatear_stock(prod[4], prod[5])[0],  # stock_actual
                prod[5],        # stock_minimo
                prod[6],        # stock_maximo
                f"${prod[7]:.2f}",  # precio_venta
                f"${prod[8]:.2f}",  # costo
                prod[9] or "-", # sku
                prod[10] or "-",# codigo_barras
                "Activo" if prod[11] == 1 else "Inactivo"  # estado
            ]
            
            self.tabla.insert("", tk.END, values=valores, tags=tags)  # <-- valores ya está definido
        
        # Configurar colores para estado
        self.tabla.tag_configure('inactivo', foreground='#bf616a')

    def _aplicar_filtros(self, event=None):
        """Aplica los filtros activos"""
        categoria = self.combo_categorias.get()
        busqueda = self.entrada_busqueda.get().strip().lower()
        
        filtrados = []
        for p in self.productos:
            # Filtro de categoría
            cumple_categoria = (
                categoria == "Todas las categorías" or 
                (p[2] and p[2].lower() == categoria.lower())
            )
            
            # Filtro de búsqueda
            cumple_busqueda = (
                not busqueda or
                busqueda in str(p[0]).lower() or    # ID
                busqueda in p[1].lower() or         # Nombre
                (p[2] and busqueda in p[2].lower()) or  # Categoría
                (p[9] and busqueda in str(p[9]).lower()) or  # SKU 
                (p[10] and busqueda in str(p[10]).lower())   # Código de Barras
            )
            
            if cumple_categoria and cumple_busqueda:
                filtrados.append(p)
        
        self._actualizar_tabla(filtrados)


    def _actualizar_lista_productos(self, event=None):
        """Actualiza la lista de productos según la búsqueda"""
        busqueda = self.busqueda_producto.get().strip().lower()
        self.lista_productos.delete(0, tk.END)
        
        for p in self.productos:
            match = (
                busqueda in str(p[0]).lower() or     # ID
                busqueda in p[1].lower() or          # Nombre
                (p[9] and busqueda in p[9].lower()) or  # SKU
                (p[10] and busqueda in p[10].lower())   # Código Barras
            )
            if match:
                self.lista_productos.insert(tk.END, f"{p[0]} - {p[1]}")

    def _abrir_dialogo_movimiento(self):
        DialogoMovimiento(self, self.productos, self._cargar_datos)

    if __name__ == "__main__":
        root = tk.Tk()
        app = PantallaInventario(root)
        root.mainloop()