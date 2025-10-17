import tkinter as tk
from tkinter import ttk
from db.db import obtener_datos, ejecutar_query
from ui.styles import AppTheme
from utils import helpers


class PantallaMovimientos(ttk.Frame):
    COLUMNAS = {
        'Principal': [
            ('id_movimiento', 'ID', 60),
            ('tipo', 'Tipo', 100),
            ('fecha', 'Fecha', 120),
            ('cantidad', 'Cantidad', 80),
            ('producto', 'Producto', 150),
            ('usuario', 'Usuario', 150),
            ('referencia', 'Referencia', 200)
        ]
    }

    def __init__(self, parent):
        super().__init__(parent)
        self.theme = AppTheme()
        self.datos = []
        self.sort_column = 'm.id_movimiento'
        self.sort_ascending = False

        self._crear_widgets()
        self._cargar_datos()
        self._actualizar_tabla()

    def _cargar_datos(self):
        query = """
            SELECT 
                m.id_movimiento,
                m.tipo,
                strftime('%d/%m/%Y %H:%M', m.fecha) as fecha_formateada,
                m.cantidad,
                p.nombre AS producto,
                COALESCE(u.nombres || ' ' || u.apellido_p, 'Sistema') AS usuario,
                m.referencia
            FROM Movimientos m
            LEFT JOIN Productos p ON m.id_producto = p.id_producto
            LEFT JOIN Usuarios u ON m.id_usuario = u.id_usuario
            ORDER BY {} {}
        """.format(
            self.sort_column, 
            'ASC' if self.sort_ascending else 'DESC'
        )
        self.datos = obtener_datos(query)

    def _ordenar_por_columna(self, columna):
        # Mapeo de columnas virtuales a campos reales
        column_map = {
            'id_movimiento': 'm.id_movimiento',
            'tipo': 'm.tipo',
            'fecha': 'm.fecha',
            'cantidad': 'm.cantidad',
            'producto': 'p.nombre',
            'usuario': 'u.nombres',
            'referencia': 'm.referencia'
        }
        
        if self.sort_column == column_map.get(columna):
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column_map[columna]
            self.sort_ascending = True

        self._cargar_datos()
        self._aplicar_filtros()

    def _aplicar_filtros(self, event=None):
        filtro = self.entrada_busqueda.get().strip().lower()
        datos_filtrados = []
        
        for row in self.datos:
            # Buscar en todos los campos relevantes
            match = any(
                filtro in str(value).lower()
                for value in (
                    row[0],  # ID
                    row[1],  # Tipo
                    row[2],  # Fecha
                    abs(row[3]),  # Cantidad (valor absoluto)
                    row[4],  # Producto
                    row[5],  # Usuario
                    row[6]   # Referencia
                )
            )
            if match:
                datos_filtrados.append(row)
        
        self._actualizar_tabla(datos_filtrados)

    def _actualizar_tabla(self, datos=None):
        self.tabla.delete(*self.tabla.get_children())
        for item in (datos or self.datos):
            # Formatear cantidad con signo
            cantidad = item[3]
            cantidad_formateada = f"+{cantidad}" if cantidad > 0 else str(cantidad)
            
            # Crear nueva tupla con los valores formateados
            valores = (
                item[0],  # ID
                item[1].capitalize(),  # Tipo
                item[2],  # Fecha
                cantidad_formateada,
                item[4] or "N/A",  # Producto
                item[5],  # Usuario
                item[6]   # Referencia
            )
            self.tabla.insert("", tk.END, values=valores)

    def _crear_widgets(self):
        # Controles superiores
        controles_frame = ttk.Frame(self)
        controles_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(controles_frame, text="Buscar:").pack(side=tk.LEFT)
        self.entrada_busqueda = ttk.Entry(controles_frame)
        self.entrada_busqueda.pack(side=tk.LEFT, padx=5)
        self.entrada_busqueda.bind("<KeyRelease>", self._aplicar_filtros)

        # Tabla de datos
        self._configurar_tabla()

    def _configurar_tabla(self):
        self.tabla_frame = ttk.Frame(self)
        self.tabla_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = ttk.Scrollbar(self.tabla_frame, orient=tk.VERTICAL)

        self.tabla = ttk.Treeview(
            self.tabla_frame,
            columns=[col[0] for col in self.COLUMNAS['Principal']],
            show="headings",
            yscrollcommand=scrollbar.set,
            selectmode="browse"
        )

        for col in self.COLUMNAS['Principal']:
            self.tabla.heading(col[0], text=col[1],
                               command=lambda c=col[0]: self._ordenar_por_columna(c))
            self.tabla.column(col[0], width=col[2], anchor=tk.CENTER)

        scrollbar.config(command=self.tabla.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tabla.pack(fill=tk.BOTH, expand=True)

    def _ordenar_por_columna(self, columna):
        if self.sort_column == columna:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = columna
            self.sort_ascending = True

        # Mapeo de columnas virtuales
        alias_map = {
            'producto': 'p.nombre',
            'usuario': 'u.nombre'
        }
        self.sort_column = alias_map.get(columna, f"m.{columna}")

        self._cargar_datos()
        self._aplicar_filtros()

    def _abrir_dialogo_nuevo(self):
        # Método pendiente: puedes abrir un diálogo para crear un nuevo movimiento
        helpers.mostrar_info("Función no implementada", "Aquí se abriría el diálogo para crear un nuevo movimiento.")


# Solo para pruebas fuera del sistema principal
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Pantalla de Movimientos")
    root.geometry("1000x600")
    app = PantallaMovimientos(root)
    app.pack(fill=tk.BOTH, expand=True)
    root.mainloop()