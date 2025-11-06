import sys
import os
import tkinter as tk
import unittest
from unittest.mock import patch, Mock

# --- INICIO DE CONFIGURACIÓN DEL PATH ---
# Añade la carpeta raíz del proyecto al path de Python para encontrar los módulos.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
# --- FIN DE CONFIGURACIÓN DEL PATH ---

# Ahora las importaciones desde tu proyecto funcionarán
# (Asegúrate de que la estructura de carpetas sea correcta)
from ui.dialogos.dialogo_producto import DialogoProducto
from ui.dialogos.dialogo_movimientos import DialogoMovimiento

# --- Simulación del módulo de base de datos para las pruebas ---
db_connection = None

def configurar_conexion_db(conn):
    """Establece la conexión a la base de datos para las pruebas."""
    global db_connection
    db_connection = conn

def ejecutar_query(query, parametros=()):
    """Ejecuta una consulta (INSERT, UPDATE) en la BD de prueba."""
    cursor = db_connection.cursor()
    cursor.execute(query, parametros)
    db_connection.commit()
    return cursor.lastrowid

def obtener_datos(query, parametros=()):
    """Obtiene datos de la BD de prueba."""
    cursor = db_connection.cursor()
    cursor.execute(query, parametros)
    return cursor.fetchall()

def ejecutar_transaccion(queries):
    """Ejecuta una lista de consultas como una transacción en la BD de prueba."""
    cursor = db_connection.cursor()
    try:
        for query, params in queries:
            cursor.execute(query, params)
        db_connection.commit()
    except Exception as e:
        db_connection.rollback()
        raise e

# --- Clase de Pruebas de Integración para Diálogos ---

class TestIntegracionDialogos(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        """Configura una BD en memoria y el esquema necesario antes de cada prueba."""
        self.conn = sqlite3.connect(':memory:')
        configurar_conexion_db(self.conn)
        cursor = self.conn.cursor()
        
        # Crear todas las tablas necesarias para los diálogos
        cursor.execute("""
            CREATE TABLE Productos (
                id_producto INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, descripcion TEXT,
                precio_venta REAL, costo REAL, sku TEXT UNIQUE, id_categoria INTEGER,
                id_proveedor INTEGER, stock_actual INTEGER, stock_minimo INTEGER, stock_maximo INTEGER,
                estado INTEGER DEFAULT 1
            )""")
        cursor.execute("CREATE TABLE Categorias (id_categoria INTEGER PRIMARY KEY, nombre TEXT)")
        cursor.execute("CREATE TABLE Proveedores (id_proveedor INTEGER PRIMARY KEY, nombre TEXT)")
        cursor.execute("""
            CREATE TABLE Movimientos_inventario (
                id_movimiento INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT, cantidad INTEGER,
                fecha DATETIME, id_producto INTEGER, referencia TEXT
            )""")
        self.conn.commit()

        # Inyectar las funciones de BD reales en los módulos de los diálogos
        dialogo_producto_module = sys.modules['ui.dialogos.dialogo_producto']
        dialogo_producto_module.obtener_datos = obtener_datos
        dialogo_producto_module.ejecutar_query = ejecutar_query
        
        dialogo_movimientos_module = sys.modules['ui.dialogos.dialogo_movimientos']
        dialogo_movimientos_module.obtener_datos = obtener_datos
        dialogo_movimientos_module.ejecutar_transaccion = ejecutar_transaccion

    def tearDown(self):
        self.conn.close()

    # --- 5 FUNCIONES DE PRUEBA DE INTEGRACIÓN ---

    @patch('ui.dialogos.dialogo_producto.DialogoCategoria')
    @patch('ui.dialogos.dialogo_producto.DialogoProveedor')
    @patch('ui.dialogos.dialogo_producto.messagebox')
    def test_1_crear_producto_exitoso(self, mock_messagebox, mock_dlg_prov, mock_dlg_cat):
        """
        # Responsable: Tecsi Huallpa Luis Alberto
        Prueba el flujo exitoso de creación de un producto, verificando que
        los datos se inserten correctamente en la base de datos.
        """
        # Arrange: Insertar datos preliminares (categoría, proveedor) en la BD de prueba
        ejecutar_query("INSERT INTO Categorias (id_categoria, nombre) VALUES (?, ?)", (1, 'Tecnología'))
        ejecutar_query("INSERT INTO Proveedores (id_proveedor, nombre) VALUES (?, ?)", (1, 'TechCorp'))
        mock_callback = Mock()

        # Act: Simular la interacción del usuario con el diálogo
        dialogo = DialogoProducto(self.root, mock_callback)
        dialogo.entries['nombre'].insert(0, 'Teclado Mecánico RGB')
        dialogo.entries['precio_venta'].insert(0, '120.50')
        dialogo.entries['costo'].insert(0, '75.00')
        dialogo.entries['stock_actual'].insert(0, '50')
        dialogo.entries['sku'].insert(0, 'TEC-RGB-001')
        dialogo.combo_categoria.set('1 - Tecnología')
        dialogo.combo_proveedor.set('1 - TechCorp')
        
        dialogo._validar_formulario()

        # Assert: Consultar la BD para verificar que el producto fue creado
        producto_creado = obtener_datos("SELECT nombre, sku, stock_actual FROM Productos WHERE sku = ?", ('TEC-RGB-001',))
        self.assertEqual(len(producto_creado), 1)
        self.assertEqual(producto_creado[0][0], 'Teclado Mecánico RGB')
        self.assertEqual(producto_creado[0][2], 50)
        
        mock_messagebox.showinfo.assert_called_with("Éxito", "Producto creado exitosamente")
        mock_callback.assert_called_once()
        dialogo.dialogo.destroy()

    @patch('ui.dialogos.dialogo_producto.messagebox')
    def test_2_crear_producto_falla_sku_duplicado(self, mock_messagebox):
        """
        # Responsable: Paucar Quejia Rye Gabriel Gregory
        Prueba que la integración con la BD previene la creación de un producto
        con un SKU que ya existe.
        """
        # Arrange: Insertar un producto en la BD con un SKU específico
        ejecutar_query("INSERT INTO Productos (nombre, sku) VALUES (?, ?)", ('Producto Existente', 'SKU-EXISTE'))
        mock_callback = Mock()
        
        # Act: Intentar crear otro producto con el mismo SKU
        dialogo = DialogoProducto(self.root, mock_callback)
        dialogo.entries['nombre'].insert(0, 'Producto Nuevo Falso')
        dialogo.entries['precio_venta'].insert(0, '100')
        dialogo.entries['costo'].insert(0, '50')
        dialogo.entries['stock_actual'].insert(0, '10')
        dialogo.entries['sku'].insert(0, 'SKU-EXISTE')
        
        dialogo._validar_formulario()

        # Assert: Verificar que no se insertó un segundo producto
        productos = obtener_datos("SELECT COUNT(*) FROM Productos")
        self.assertEqual(productos[0][0], 1)
        
        self.assertEqual(dialogo.errores['sku'].cget("text"), "Este sku ya existe")
        mock_callback.assert_not_called()
        dialogo.dialogo.destroy()

    @patch('ui.dialogos.dialogo_movimientos.messagebox')
    def test_3_registrar_salida_stock_insuficiente(self, mock_messagebox):
        """
        # Responsable: Ccahua Huamani Salome Celeste
        Prueba que no se permite un movimiento de salida si la cantidad solicitada
        supera el stock actual registrado en la base de datos.
        """
        # Arrange: Insertar un producto con stock limitado
        prod_id = ejecutar_query("INSERT INTO Productos (nombre, stock_actual) VALUES (?, ?)", ('Monitor 4K', 5))
        mock_callback = Mock()

        # Act: Intentar registrar una salida mayor al stock disponible
        dialogo = DialogoMovimiento(self.root, [(prod_id, 'Monitor 4K', 5)], mock_callback)
        dialogo.tipo_movimiento.set('salida')
        dialogo.lista_productos.insert(tk.END, f"{prod_id} - Monitor 4K")
        dialogo.lista_productos.selection_set(0)
        dialogo.cantidad_movimiento.insert(0, '10') # Intentar sacar 10 de 5
        
        dialogo._validar_movimiento()

        # Assert: Verificar que el stock en la BD no cambió y se mostró un error
        stock_final = obtener_datos("SELECT stock_actual FROM Productos WHERE id_producto = ?", (prod_id,))
        self.assertEqual(stock_final[0][0], 5)
        mock_messagebox.showerror.assert_called_with(
            "Error de validación", "Stock insuficiente. Disponible: 5\nSolicitado: 10", parent=dialogo.dialogo
        )
        mock_callback.assert_not_called()
        dialogo.dialogo.destroy()

    @patch('ui.dialogos.dialogo_movimientos.messagebox')
    def test_4_registrar_entrada_exitosa(self, mock_messagebox):
        """
        # Responsable: Roque Aysa Gabriel Saul
        Prueba el flujo exitoso de una entrada de inventario, verificando que
        el stock del producto se actualice y se cree un registro del movimiento.
        """
        # Arrange: Insertar producto con stock inicial
        prod_id = ejecutar_query("INSERT INTO Productos (nombre, stock_actual) VALUES (?, ?)", ('SSD 1TB', 20))
        mock_callback = Mock()

        # Act: Registrar una entrada de 15 unidades
        dialogo = DialogoMovimiento(self.root, [(prod_id, 'SSD 1TB', 20)], mock_callback)
        dialogo.tipo_movimiento.set('entrada')
        dialogo.lista_productos.insert(tk.END, f"{prod_id} - SSD 1TB")
        dialogo.lista_productos.selection_set(0)
        dialogo.cantidad_movimiento.insert(0, '15')
        
        dialogo._validar_movimiento()
        
        # Assert: Verificar el nuevo stock y el registro del movimiento en la BD
        stock_actualizado = obtener_datos("SELECT stock_actual FROM Productos WHERE id_producto = ?", (prod_id,))
        self.assertEqual(stock_actualizado[0][0], 35) # 20 + 15 = 35

        movimiento_registrado = obtener_datos("SELECT tipo, cantidad, id_producto FROM Movimientos_inventario")
        self.assertEqual(len(movimiento_registrado), 1)
        self.assertEqual(movimiento_registrado[0][0], 'entrada')
        self.assertEqual(movimiento_registrado[0][1], 15)
        
        mock_callback.assert_called_once()
        dialogo.dialogo.destroy()

    @patch('ui.dialogos.dialogo_movimientos.messagebox')
    def test_5_registrar_salida_exitosa(self, mock_messagebox):
        """
        # Responsable: Rivera Cusihuaman Jorcaef Vicente
        Prueba el flujo exitoso de una salida de inventario, verificando que
        el stock se descuente correctamente y se registre el movimiento.
        """
        # Arrange: Insertar producto con stock suficiente
        prod_id = ejecutar_query("INSERT INTO Productos (nombre, stock_actual) VALUES (?, ?)", ('Memoria RAM 16GB', 100))
        mock_callback = Mock()

        # Act: Registrar una salida de 20 unidades
        dialogo = DialogoMovimiento(self.root, [(prod_id, 'Memoria RAM 16GB', 100)], mock_callback)
        dialogo.tipo_movimiento.set('salida')
        dialogo.lista_productos.insert(tk.END, f"{prod_id} - Memoria RAM 16GB")
        dialogo.lista_productos.selection_set(0)
        dialogo.cantidad_movimiento.insert(0, '20')
        dialogo.referencia_movimiento.insert(0, 'Venta a cliente X')
        
        dialogo._validar_movimiento()

        # Assert: Verificar el stock descontado y el registro del movimiento en la BD
        stock_actualizado = obtener_datos("SELECT stock_actual FROM Productos WHERE id_producto = ?", (prod_id,))
        self.assertEqual(stock_actualizado[0][0], 80) # 100 - 20 = 80

        movimiento_registrado = obtener_datos("SELECT tipo, cantidad, referencia FROM Movimientos_inventario")
        self.assertEqual(len(movimiento_registrado), 1)
        self.assertEqual(movimiento_registrado[0][0], 'salida')
        self.assertEqual(movimiento_registrado[0][1], 20)
        self.assertEqual(movimiento_registrado[0][2], 'Venta a cliente X')
        
        mock_callback.assert_called_once()
        dialogo.dialogo.destroy()

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)