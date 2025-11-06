# ==========================================================
# ARCHIVO DE PRUEBA DE INTEGRACIÓN
# RESPONSABLE: Ccahua Huamani Salome Celeste
# PRUEBA: test_3_registrar_salida_stock_insuficiente
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

class TestStockInsuficiente(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.root = tk.Tk(); cls.root.withdraw()
    @classmethod
    def tearDownClass(cls): cls.root.destroy()

    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        configurar_conexion_db(self.conn)
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE Productos (id_producto INTEGER PRIMARY KEY, nombre TEXT, stock_actual INTEGER)")
        self.conn.commit()
        sys.modules['ui.dialogos.dialogo_movimientos'].obtener_datos = obtener_datos

    def tearDown(self): self.conn.close()

    @patch('ui.dialogos.dialogo_movimientos.messagebox')
    def test_3_registrar_salida_stock_insuficiente(self, mock_messagebox):
        prod_id = ejecutar_query("INSERT INTO Productos (nombre, stock_actual) VALUES (?, ?)", ('Monitor 4K', 5))
        mock_callback = Mock()

        dialogo = DialogoMovimiento(self.root, [(prod_id, 'Monitor 4K', 5)], mock_callback)
        dialogo.tipo_movimiento.set('salida')
        dialogo.lista_productos.insert(tk.END, f"{prod_id} - Monitor 4K")
        dialogo.lista_productos.selection_set(0)
        dialogo.cantidad_movimiento.insert(0, '10')
        
        dialogo._validar_movimiento()

        stock_final = obtener_datos("SELECT stock_actual FROM Productos WHERE id_producto = ?", (prod_id,))
        self.assertEqual(stock_final[0][0], 5)
        mock_messagebox.showerror.assert_called_with(
            "Error de validación", "Stock insuficiente. Disponible: 5\nSolicitado: 10", parent=dialogo.dialogo
        )
        mock_callback.assert_not_called()
        dialogo.dialogo.destroy()

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)