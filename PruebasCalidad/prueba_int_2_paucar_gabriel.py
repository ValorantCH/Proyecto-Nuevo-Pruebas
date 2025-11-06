# ==========================================================
# ARCHIVO DE PRUEBA DE INTEGRACIÓN
# RESPONSABLE: Paucar Quejia Rye Gabriel Gregory
# PRUEBA: test_2_crear_producto_falla_sku_duplicado
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

# --- Helpers de Base de Datos (replicados para independencia) ---
db_connection = None
def configurar_conexion_db(conn): global db_connection; db_connection = conn
def ejecutar_query(q, p=()): c = db_connection.cursor(); c.execute(q, p); db_connection.commit(); return c.lastrowid
def obtener_datos(q, p=()): c = db_connection.cursor(); c.execute(q, p); return c.fetchall()

class TestSkuDuplicado(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.root = tk.Tk(); cls.root.withdraw()
    @classmethod
    def tearDownClass(cls): cls.root.destroy()

    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        configurar_conexion_db(self.conn)
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE Productos (id_producto INTEGER PRIMARY KEY, nombre TEXT, sku TEXT UNIQUE, precio_venta REAL, costo REAL, stock_actual INTEGER)")
        self.conn.commit()
        sys.modules['ui.dialogos.dialogo_producto'].obtener_datos = obtener_datos
        sys.modules['ui.dialogos.dialogo_producto'].ejecutar_query = ejecutar_query

    def tearDown(self): self.conn.close()

    @patch('ui.dialogos.dialogo_producto.messagebox')
    def test_2_crear_producto_falla_sku_duplicado(self, mock_messagebox):
        ejecutar_query("INSERT INTO Productos (nombre, sku) VALUES (?, ?)", ('Producto Existente', 'SKU-EXISTE'))
        mock_callback = Mock()
        
        dialogo = DialogoProducto(self.root, mock_callback)
        dialogo.entries['nombre'].insert(0, 'Producto Nuevo Falso')
        dialogo.entries['precio_venta'].insert(0, '100')
        dialogo.entries['costo'].insert(0, '50')
        dialogo.entries['stock_actual'].insert(0, '10')
        dialogo.entries['sku'].insert(0, 'SKU-EXISTE')
        
        dialogo._validar_formulario()

        productos = obtener_datos("SELECT COUNT(*) FROM Productos")
        self.assertEqual(productos[0][0], 1)
        self.assertEqual(dialogo.errores['sku'].cget("text"), "Este sku ya existe")
        mock_callback.assert_not_called()
        dialogo.dialogo.destroy()

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)