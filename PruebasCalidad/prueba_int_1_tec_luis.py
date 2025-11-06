# ==========================================================
# ARCHIVO DE PRUEBA DE INTEGRACIÓN
# RESPONSABLE: Tecsi Huallpa Luis Alberto
# PRUEBA: test_1_crear_producto_exitoso
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
def ejecutar_transaccion(queries):
    c = db_connection.cursor()
    try:
        for q, p in queries: c.execute(q, p)
        db_connection.commit()
    except Exception as e: db_connection.rollback(); raise e

class TestCrearProducto(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.root = tk.Tk(); cls.root.withdraw()
    @classmethod
    def tearDownClass(cls): cls.root.destroy()

    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        configurar_conexion_db(self.conn)
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE Productos (id_producto INTEGER PRIMARY KEY, nombre TEXT, sku TEXT UNIQUE, 
            stock_actual INTEGER, id_categoria INTEGER, id_proveedor INTEGER, precio_venta REAL, costo REAL)""")
        cursor.execute("CREATE TABLE Categorias (id_categoria INTEGER PRIMARY KEY, nombre TEXT)")
        cursor.execute("CREATE TABLE Proveedores (id_proveedor INTEGER PRIMARY KEY, nombre TEXT)")
        self.conn.commit()

        # Inyección de dependencias
        sys.modules['ui.dialogos.dialogo_producto'].obtener_datos = obtener_datos
        sys.modules['ui.dialogos.dialogo_producto'].ejecutar_query = ejecutar_query

    def tearDown(self): self.conn.close()

    @patch('ui.dialogos.dialogo_producto.DialogoCategoria')
    @patch('ui.dialogos.dialogo_producto.DialogoProveedor')
    @patch('ui.dialogos.dialogo_producto.messagebox')
    def test_1_crear_producto_exitoso(self, mock_messagebox, mock_dlg_prov, mock_dlg_cat):
        ejecutar_query("INSERT INTO Categorias (id_categoria, nombre) VALUES (?, ?)", (1, 'Tecnología'))
        ejecutar_query("INSERT INTO Proveedores (id_proveedor, nombre) VALUES (?, ?)", (1, 'TechCorp'))
        mock_callback = Mock()

        dialogo = DialogoProducto(self.root, mock_callback)
        dialogo.entries['nombre'].insert(0, 'Teclado Mecánico RGB')
        dialogo.entries['precio_venta'].insert(0, '120.50')
        dialogo.entries['costo'].insert(0, '75.00')
        dialogo.entries['stock_actual'].insert(0, '50')
        dialogo.entries['sku'].insert(0, 'TEC-RGB-001')
        # CORRECCIÓN: Asumiendo que el nombre del widget es 'combo_categorias'
        if hasattr(dialogo, 'combo_categoria'):
             dialogo.combo_categoria.set('1 - Tecnología')
        if hasattr(dialogo, 'combo_proveedor'):
             dialogo.combo_proveedor.set('1 - TechCorp')

        dialogo._validar_formulario()

        producto_creado = obtener_datos("SELECT nombre, sku, stock_actual FROM Productos WHERE sku = ?", ('TEC-RGB-001',))
        self.assertEqual(len(producto_creado), 1)
        self.assertEqual(producto_creado[0][0], 'Teclado Mecánico RGB')

        mock_messagebox.showinfo.assert_called_with("Éxito", "Producto creado exitosamente")
        mock_callback.assert_called_once()
        dialogo.dialogo.destroy()

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)