import tkinter as tk
import unittest
from unittest.mock import patch, Mock, ANY

# Importamos las clases de los diálogos que vamos a probar
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
        cls.root.withdraw()  # Ocultamos la ventana principal

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
        # Configuración del Mock de la base de datos
        mock_obtener_datos.side_effect = [
            [(1, 'Electrónica')],  # Categorías
            [(1, 'Proveedor A')],  # Proveedores
            [(0,)],  # Validación de unicidad de SKU (devuelve 0, no existe)
            [(0,)]   # Validación de unicidad de código de barras
        ]
        mock_callback = Mock()

        # Acción: Crear el diálogo y simular la entrada del usuario
        dialogo = DialogoProducto(self.root, mock_callback)
        
        # Llenar el formulario
        dialogo.entries['nombre'].insert(0, 'Laptop Gamer')
        dialogo.entries['precio_venta'].insert(0, '1500.00')
        dialogo.entries['costo'].insert(0, '1000.00')
        dialogo.entries['stock_minimo'].insert(0, '5')
        dialogo.entries['stock_maximo'].insert(0, '20')
        dialogo.entries['stock_actual'].insert(0, '10')
        dialogo.entries['sku'].insert(0, 'LP-GAM-001')

        # Simular clic en el botón de guardar
        dialogo._validar_formulario()

        # Aserciones (Verificaciones)
        # 1. Verificar que se consultó la unicidad del SKU
        mock_obtener_datos.assert_any_call("SELECT COUNT(*) FROM Productos WHERE sku = ?", ('LP-GAM-001',))
        
        # 2. Verificar que la inserción se ejecutó con los datos correctos
        mock_ejecutar_query.assert_called_once()
        args, _ = mock_ejecutar_query.call_args
        self.assertIn("INSERT INTO Productos", args[0])
        self.assertEqual(args[1][0], 'Laptop Gamer') # Nombre
        self.assertEqual(args[1][5], 'LP-GAM-001')  # SKU

        # 3. Verificar que se mostró un mensaje de éxito
        mock_messagebox.showinfo.assert_called_with("Éxito", "Producto creado exitosamente")

        # 4. Verificar que la función de callback fue llamada
        mock_callback.assert_called_once()
        
        dialogo.dialogo.destroy()

    @patch('ui.dialogos.dialogo_producto.messagebox')
    @patch('ui.dialogos.dialogo_producto.obtener_datos')
    def test_crear_producto_falla_sku_duplicado(self, mock_obtener_datos, mock_messagebox):
        """
        Prueba que el sistema previene la creación de un producto con un SKU que ya existe.
        """
        # Configuración: SKU ya existe en la DB
        mock_obtener_datos.side_effect = [
            [], [], # Categorías y proveedores
            [(1,)] # El SKU 'EXISTE-001' ya existe
        ]
        mock_callback = Mock()

        # Acción
        dialogo = DialogoProducto(self.root, mock_callback)
        dialogo.entries['nombre'].insert(0, 'Producto Repetido')
        dialogo.entries['precio_venta'].insert(0, '100')
        dialogo.entries['costo'].insert(0, '80')
        dialogo.entries['stock_minimo'].insert(0, '1')
        dialogo.entries['stock_maximo'].insert(0, '10')
        dialogo.entries['stock_actual'].insert(0, '5')
        dialogo.entries['sku'].insert(0, 'EXISTE-001')
        
        dialogo._validar_formulario()
        
        # Aserciones
        # 1. Verificar que se mostró el error correcto
        mock_messagebox.showerror.assert_not_called() # No usa messagebox, muestra error en label
        self.assertEqual(dialogo.errores['sku'].cget("text"), "Este sku ya existe")

        # 2. Verificar que no se llamó a la función de callback
        mock_callback.assert_not_called()
        
        dialogo.dialogo.destroy()

    # --- Pruebas para DialogoMovimiento ---

    @patch('ui.dialogos.dialogo_movimiento.messagebox')
    @patch('ui.dialogos.dialogo_movimiento.ejecutar_transaccion')
    @patch('ui.dialogos.dialogo_movimiento.obtener_datos')
    def test_registrar_salida_stock_insuficiente(self, mock_obtener_datos, mock_ejecutar_transaccion, mock_messagebox):
        """
        Prueba que no se puede registrar una salida si el stock actual es menor
        a la cantidad solicitada.
        """
        # Configuración
        mock_productos = [(1, 'Teclado Mecánico', 10)] # id, nombre, stock
        mock_obtener_datos.return_value = [[5]] # El stock actual es 5
        mock_callback = Mock()

        # Acción
        dialogo = DialogoMovimiento(self.root, mock_productos, mock_callback)
        dialogo.tipo_movimiento.set('salida')
        dialogo.lista_productos.insert(tk.END, f"{mock_productos[0][0]} - {mock_productos[0][1]}")
        dialogo.lista_productos.selection_set(0) # Seleccionar el producto
        dialogo.cantidad_movimiento.insert(0, '10') # Intentar sacar 10
        
        dialogo._validar_movimiento()

        # Aserciones
        # 1. Verificar que se consultó el stock del producto
        mock_obtener_datos.assert_called_with(
            "SELECT stock_actual FROM Productos WHERE id_producto = ?", (1,)
        )
        
        # 2. Verificar que se mostró el mensaje de error de stock
        mock_messagebox.showerror.assert_called_with(
            "Error de validación",
            "Stock insuficiente. Disponible: 5\nSolicitado: 10",
            parent=ANY
        )

        # 3. Verificar que no se ejecutó la transacción
        mock_ejecutar_transaccion.assert_not_called()

        dialogo.dialogo.destroy()

    @patch('ui.dialogos.dialogo_movimiento.messagebox')
    @patch('ui.dialogos.dialogo_movimiento.ejecutar_transaccion')
    def test_registrar_entrada_exitosa(self, mock_ejecutar_transaccion, mock_messagebox):
        """
        Prueba el flujo exitoso de registrar una entrada de inventario.
        Verifica que la transacción se ejecute con una cantidad positiva.
        """
        # Configuración
        mock_productos = [(2, 'Mouse Inalámbrico', 20)]
        mock_callback = Mock()

        # Acción
        dialogo = DialogoMovimiento(self.root, mock_productos, mock_callback)
        dialogo.tipo_movimiento.set('entrada')
        dialogo.lista_productos.insert(tk.END, f"{mock_productos[0][0]} - {mock_productos[0][1]}")
        dialogo.lista_productos.selection_set(0)
        dialogo.cantidad_movimiento.insert(0, '15') # Añadir 15 unidades
        dialogo.referencia_movimiento.insert(0, 'Compra a Proveedor B')

        dialogo._validar_movimiento()

        # Aserciones
        # 1. Verificar que se ejecutó la transacción
        mock_ejecutar_transaccion.assert_called_once()
        
        # 2. Inspeccionar los datos enviados a la transacción
        args, _ = mock_ejecutar_transaccion.call_args
        queries = args[0]
        
        # Query de inserción en Movimientos
        insert_query_params = queries[0][1]
        self.assertEqual(insert_query_params[0], 'entrada') # tipo
        self.assertEqual(insert_query_params[1], 15)        # cantidad (positiva)
        self.assertEqual(insert_query_params[2], 2)         # id_producto

        # Query de actualización en Productos
        update_query_params = queries[1][1]
        self.assertEqual(update_query_params[0], 15)        # cantidad a sumar (positiva)
        self.assertEqual(update_query_params[1], 2)         # id_producto
        
        # 3. Verificar que el callback fue llamado
        mock_callback.assert_called_once()

        dialogo.dialogo.destroy()

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)