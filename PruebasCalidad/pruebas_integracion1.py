import sys
import os
import tkinter as tk
import unittest
from unittest.mock import patch, Mock, ANY

# --- INICIO DE LA CORRECCIÓN ---
# Añadir la carpeta raíz del proyecto al path de Python.
# Esto permite que el script encuentre los módulos en la carpeta 'ui'.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
# --- FIN DE LA CORRECCIÓN ---

# Ahora las importaciones funcionarán correctamente
from ui.dialogos.dialogo_producto import DialogoProducto
from ui.dialogos.dialogo_movimientos import DialogoMovimiento

class TestIntegracionDialogos(unittest.TestCase):
    """
    Suite de pruebas de integración para DialogoProducto y DialogoMovimiento.
    Verifica la interacción entre la UI y la capa de datos (simulada).
    """

    @classmethod
    def setUpClass(cls):
        """Se ejecuta una vez antes de todas las pruebas para crear la ventana raíz."""
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        """Se ejecuta una vez después de todas las pruebas para destruir la ventana."""
        cls.root.destroy()

    # --- Pruebas para DialogoProducto ---

    @patch('ui.dialogos.dialogo_producto.DialogoCategoria')
    @patch('ui.dialogos.dialogo_producto.DialogoProveedor')
    @patch('ui.dialogos.dialogo_producto.messagebox')
    @patch('ui.dialogos.dialogo_producto.ejecutar_query')
    @patch('ui.dialogos.dialogo_producto.obtener_datos')
    def test_crear_producto_exitoso(self, mock_obtener_datos, mock_ejecutar_query, mock_messagebox, mock_dlg_prov, mock_dlg_cat):
        """
        Prueba el flujo completo y exitoso de creación de un nuevo producto.
        Verifica que se validen los datos y se llame a la base de datos correctamente.
        """
        mock_obtener_datos.side_effect = [
            [(1, 'Electrónica')],
            [(1, 'Proveedor A')],
            [(0,)],
            [(0,)]
        ]
        mock_callback = Mock()

        dialogo = DialogoProducto(self.root, mock_callback)
        
        dialogo.entries['nombre'].insert(0, 'Laptop Gamer')
        dialogo.entries['precio_venta'].insert(0, '1500.00')
        dialogo.entries['costo'].insert(0, '1000.00')
        dialogo.entries['stock_minimo'].insert(0, '5')
        dialogo.entries['stock_maximo'].insert(0, '20')
        dialogo.entries['stock_actual'].insert(0, '10')
        dialogo.entries['sku'].insert(0, 'LP-GAM-001')

        dialogo._validar_formulario()

        mock_obtener_datos.assert_any_call("SELECT COUNT(*) FROM Productos WHERE sku = ?", ('LP-GAM-001',))
        mock_ejecutar_query.assert_called_once()
        args, _ = mock_ejecutar_query.call_args
        self.assertIn("INSERT INTO Productos", args[0])
        self.assertEqual(args[1][0], 'Laptop Gamer')
        self.assertEqual(args[1][5], 'LP-GAM-001')

        mock_messagebox.showinfo.assert_called_with("Éxito", "Producto creado exitosamente")
        mock_callback.assert_called_once()
        
        dialogo.dialogo.destroy()

    @patch('ui.dialogos.dialogo_producto.messagebox')
    @patch('ui.dialogos.dialogo_producto.obtener_datos')
    def test_crear_producto_falla_sku_duplicado(self, mock_obtener_datos, mock_messagebox):
        """
        Prueba que el sistema previene la creación de un producto con un SKU que ya existe.
        """
        mock_obtener_datos.side_effect = [
            [], [],
            [(1,)]
        ]
        mock_callback = Mock()

        dialogo = DialogoProducto(self.root, mock_callback)
        dialogo.entries['nombre'].insert(0, 'Producto Repetido')
        dialogo.entries['precio_venta'].insert(0, '100')
        dialogo.entries['costo'].insert(0, '80')
        dialogo.entries['stock_minimo'].insert(0, '1')
        dialogo.entries['stock_maximo'].insert(0, '10')
        dialogo.entries['stock_actual'].insert(0, '5')
        dialogo.entries['sku'].insert(0, 'EXISTE-001')
        
        dialogo._validar_formulario()
        
        self.assertEqual(dialogo.errores['sku'].cget("text"), "Este sku ya existe")
        mock_callback.assert_not_called()
        
        dialogo.dialogo.destroy()

    # --- Pruebas para DialogoMovimiento ---

    @patch('ui.dialogos.dialogo_movimientos.messagebox')
    @patch('ui.dialogos.dialogo_movimientos.ejecutar_transaccion')
    @patch('ui.dialogos.dialogo_movimientos.obtener_datos')
    def test_registrar_salida_stock_insuficiente(self, mock_obtener_datos, mock_ejecutar_transaccion, mock_messagebox):
        """
        Prueba que no se puede registrar una salida si el stock actual es menor
        a la cantidad solicitada.
        """
        mock_productos = [(1, 'Teclado Mecánico', 10)]
        mock_obtener_datos.return_value = [[5]]
        mock_callback = Mock()

        dialogo = DialogoMovimiento(self.root, mock_productos, mock_callback)
        dialogo.tipo_movimiento.set('salida')
        dialogo.lista_productos.insert(tk.END, f"{mock_productos[0][0]} - {mock_productos[0][1]}")
        dialogo.lista_productos.selection_set(0)
        dialogo.cantidad_movimiento.insert(0, '10')
        
        dialogo._validar_movimiento()

        mock_obtener_datos.assert_called_with(
            "SELECT stock_actual FROM Productos WHERE id_producto = ?", (1,)
        )
        mock_messagebox.showerror.assert_called_with(
            "Error de validación",
            "Stock insuficiente. Disponible: 5\nSolicitado: 10",
            parent=ANY
        )
        mock_ejecutar_transaccion.assert_not_called()

        dialogo.dialogo.destroy()

    @patch('ui.dialogos.dialogo_movimientos.messagebox')
    @patch('ui.dialogos.dialogo_movimientos.ejecutar_transaccion')
    def test_registrar_entrada_exitosa(self, mock_ejecutar_transaccion, mock_messagebox):
        """
        Prueba el flujo exitoso de registrar una entrada de inventario.
        Verifica que la transacción se ejecute con una cantidad positiva.
        """
        mock_productos = [(2, 'Mouse Inalámbrico', 20)]
        mock_callback = Mock()

        dialogo = DialogoMovimiento(self.root, mock_productos, mock_callback)
        dialogo.tipo_movimiento.set('entrada')
        dialogo.lista_productos.insert(tk.END, f"{mock_productos[0][0]} - {mock_productos[0][1]}")
        dialogo.lista_productos.selection_set(0)
        dialogo.cantidad_movimiento.insert(0, '15')
        dialogo.referencia_movimiento.insert(0, 'Compra a Proveedor B')

        dialogo._validar_movimiento()

        mock_ejecutar_transaccion.assert_called_once()
        args, _ = mock_ejecutar_transaccion.call_args
        queries = args[0]
        
        insert_query_params = queries[0][1]
        self.assertEqual(insert_query_params[0], 'entrada')
        self.assertEqual(insert_query_params[1], 15)
        self.assertEqual(insert_query_params[2], 2)

        update_query_params = queries[1][1]
        self.assertEqual(update_query_params[0], 15)
        self.assertEqual(update_query_params[1], 2)
        
        mock_callback.assert_called_once()

        dialogo.dialogo.destroy()

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)