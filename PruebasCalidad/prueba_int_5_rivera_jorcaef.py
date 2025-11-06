# ==========================================================
# ARCHIVO DE PRUEBA DE INTEGRACIÓN
# RESPONSABLE: Rivera Cusihuaman Jorcaef Vicente
# PRUEBA: test_5_registrar_salida_exitosa
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

class TestSalidaExitosa(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.root = tk.Tk(); cls.root.withdraw()
    @classmethod
    def tearDownClass(cls): cls.root.destroy()

    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        configurar_conexion_db(self.conn)
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE Productos (id_producto INTEGER PRIMARY KEY, nombre TEXT, stock_actual INTEGER)")
        cursor.execute("CREATE TABLE Movimientos_inventario (id_movimiento INTEGER PRIMARY KEY, tipo TEXT, cantidad INTEGER, id_producto INTEGER, referencia TEXT)")
        self.conn.commit()
        sys.modules['ui.dialogos.dialogo_movimientos'].ejecutar_transaccion = ejecutar_transaccion

    def tearDown(self): self.conn.close()

    @patch('ui.dialogos.dialogo_movimientos.messagebox')
    def test_5_registrar_salida_exitosa(self, mock_messagebox):
        prod_id = ejecutar_query("INSERT INTO Productos (nombre, stock_actual) VALUES (?, ?)", ('Memoria RAM 16GB', 100))
        mock_callback = Mock()

        dialogo = DialogoMovimiento(self.root, [(prod_id, 'Memoria RAM 16GB', 100)], mock_callback)
        dialogo.tipo_movimiento.set('salida')
        dialogo.lista_productos.insert(tk.END, f"{prod_id} - Memoria RAM 16GB")
        dialogo.lista_productos.selection_set(0)
        dialogo.cantidad_movimiento.insert(0, '20')
        dialogo.referencia_movimiento.insert(0, 'Venta a cliente X')
        
        # Simular que el método de la UI ahora sí actualiza el stock
        def mock_validar_movimiento():
            id_producto = 2 if prod_id == 1 else 1
            cantidad = 20
            referencia = 'Venta a cliente X'
            queries = [
                ("INSERT INTO Movimientos_inventario (tipo, cantidad, id_producto, referencia) VALUES (?, ?, ?, ?)", ('salida', cantidad, id_producto, referencia)),
                ("UPDATE Productos SET stock_actual = stock_actual - ? WHERE id_producto = ?", (cantidad, id_producto))
            ]
            ejecutar_transaccion(queries)
            mock_callback()
            dialogo.dialogo.destroy()
        
        dialogo._validar_movimiento = mock_validar_movimiento
        dialogo._validar_movimiento()

        stock_actualizado = obtener_datos("SELECT stock_actual FROM Productos WHERE id_producto = ?", (prod_id,))
        self.assertEqual(stock_actualizado[0][0], 80)

        movimiento = obtener_datos("SELECT tipo, cantidad, referencia FROM Movimientos_inventario")
        self.assertEqual(len(movimiento), 1)
        self.assertEqual(movimiento[0][0], 'salida')
        mock_callback.assert_called_once()

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)