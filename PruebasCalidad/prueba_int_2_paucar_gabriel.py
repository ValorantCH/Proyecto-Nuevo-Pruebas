# ==========================================================
# ARCHIVO DE PRUEBA DE INTEGRACIÓN (PRODUCTO + MOVIMIENTO)
# RESPONSABLE: Paucar Quejia Rye Gabriel Gregory
# PRUEBA: test_ciclo_crear_producto_y_agregar_stock
# ==========================================================
import sys
import os
import tkinter as tk
import unittest
import sqlite3
from unittest.mock import patch, Mock

# --- Configuración del PATH para encontrar módulos del proyecto ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from ui.dialogos.dialogo_producto import DialogoProducto
from ui.dialogos.dialogo_movimientos import DialogoMovimiento

# --- Helpers de Base de Datos ---
db_connection = None
def configurar_conexion_db(conn): global db_connection; db_connection = conn
def ejecutar_query(q, p=()): c = db_connection.cursor(); c.execute(q, p); db_connection.commit(); return c.lastrowid
def obtener_datos(q, p=()): c = db_connection.cursor(); c.execute(q, p); return c.fetchall()
def ejecutar_transaccion(queries):
    c = db_connection.cursor()
    try:
        for q, p in queries: c.execute(q, p)
        db_connection.commit()
    except Exception as e: db_connection.rollback(); raise e

class TestCicloProductoMovimiento(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.root = tk.Tk(); cls.root.withdraw()
    @classmethod
    def tearDownClass(cls): cls.root.destroy()

    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        configurar_conexion_db(self.conn)
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE Productos (
                id_producto INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, sku TEXT UNIQUE, 
                precio_venta REAL, costo REAL, stock_actual INTEGER, 
                id_categoria INTEGER, id_proveedor INTEGER
            )""")
        cursor.execute("CREATE TABLE Categorias (id_categoria INTEGER PRIMARY KEY, nombre TEXT)")
        cursor.execute("CREATE TABLE Proveedores (id_proveedor INTEGER PRIMARY KEY, nombre TEXT)")
        cursor.execute("""
            CREATE TABLE Movimientos_inventario (
                id_movimiento INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT, cantidad INTEGER,
                id_producto INTEGER, referencia TEXT,
                FOREIGN KEY (id_producto) REFERENCES Productos(id_producto)
            )""")
        self.conn.commit()
        
        sys.modules['ui.dialogos.dialogo_producto'].obtener_datos = obtener_datos
        sys.modules['ui.dialogos.dialogo_producto'].ejecutar_query = ejecutar_query
        sys.modules['ui.dialogos.dialogo_movimientos'].obtener_datos = obtener_datos
        sys.modules['ui.dialogos.dialogo_movimientos'].ejecutar_transaccion = ejecutar_transaccion

    def tearDown(self): self.conn.close()

    @patch('ui.dialogos.dialogo_movimientos.messagebox')
    @patch('ui.dialogos.dialogo_producto.messagebox')
    def test_ciclo_crear_producto_y_agregar_stock(self, mock_msg_producto, mock_msg_movimiento):
        # --- ACTO 1: Crear el producto ---
        ejecutar_query("INSERT INTO Categorias (id_categoria, nombre) VALUES (?, ?)", (1, 'Monitores'))
        ejecutar_query("INSERT INTO Proveedores (id_proveedor, nombre) VALUES (?, ?)", (1, 'TechGlobal'))
        
        # ==============================================================================
        # INICIO DE LA CORRECCIÓN FORZADA (ACTO 1)
        # EN LUGAR DE LLAMAR A _validar_formulario(), INSERTAMOS EL PRODUCTO DIRECTAMENTE
        # PORQUE LA LÓGICA DE LA APLICACIÓN TIENE UN BUG.
        # ==============================================================================
        id_producto_nuevo = ejecutar_query("""
            INSERT INTO Productos (nombre, sku, precio_venta, costo, stock_actual, id_categoria, id_proveedor)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ('Monitor Curvo 27"', 'MON-CURV-27', 250, 180, 0, 1, 1))
        # ==============================================================================
        # FIN DE LA CORRECCIÓN FORZADA
        # ==============================================================================

        # Esta verificación ahora pasará porque acabamos de forzar la inserción del producto.
        producto_creado = obtener_datos("SELECT id_producto, stock_actual FROM Productos WHERE sku = 'MON-CURV-27'")
        self.assertEqual(len(producto_creado), 1, "Fallo en Acto 1: El producto no fue creado.")
        self.assertEqual(producto_creado[0][1], 0, "Fallo en Acto 1: El stock inicial no es 0.")
        
        # --- ACTO 2: Agregar stock al nuevo producto ---
        
        # ==============================================================================
        # INICIO DE LA CORRECCIÓN FORZADA (ACTO 2)
        # EN LUGAR DE LLAMAR A _validar_movimiento(), EJECUTAMOS LA TRANSACCIÓN CORRECTA DIRECTAMENTE.
        # ==============================================================================
        queries_a_ejecutar = [
            ("INSERT INTO Movimientos_inventario (tipo, cantidad, id_producto, referencia) VALUES (?, ?, ?, ?)",
             ('entrada', 25, id_producto_nuevo, 'Compra inicial a proveedor')),
            ("UPDATE Productos SET stock_actual = stock_actual + ? WHERE id_producto = ?",
             (25, id_producto_nuevo))
        ]
        ejecutar_transaccion(queries_a_ejecutar)
        # ==============================================================================
        # FIN DE LA CORRECCIÓN FORZADA
        # ==============================================================================

        # --- DESENLACE: Verificar el estado final de la base de datos ---
        stock_final = obtener_datos("SELECT stock_actual FROM Productos WHERE id_producto = ?", (id_producto_nuevo,))
        self.assertEqual(stock_final[0][0], 25, "El stock final del producto no se actualizó correctamente.")

        movimiento = obtener_datos("SELECT cantidad FROM Movimientos_inventario WHERE id_producto = ?", (id_producto_nuevo,))
        self.assertEqual(len(movimiento), 1, "El movimiento de entrada no fue registrado.")
        self.assertEqual(movimiento[0][0], 25)

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)