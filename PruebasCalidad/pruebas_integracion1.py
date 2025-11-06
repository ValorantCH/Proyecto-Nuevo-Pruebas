import unittest
import tkinter as tk
import sqlite3
from datetime import datetime
from unittest.mock import patch

# --- Suposiciones sobre la estructura de tu proyecto ---
# Para que estas importaciones funcionen, este archivo de prueba
# debe estar en un lugar desde donde Python pueda encontrar los módulos 'ui' y 'db'.
# Por ejemplo:
# tu_proyecto/
# ├── ui/
# │   └── ... (aquí tus clases de UI como clientes.py)
# ├── db/
# │   └── db.py
# └── pruebas/
#     └── pruebas_integracion.py

from clientes import PantallaClientes
from transacciones import PantallaTransacciones

# --- Simulación del módulo de base de datos para las pruebas ---
# Estas funciones se conectarán a nuestra base de datos de prueba en memoria.

db_connection = None

def configurar_conexion_db(conn):
    """Establece la conexión a la base de datos para las pruebas."""
    global db_connection
    db_connection = conn

def ejecutar_query(query, parametros=()):
    """Ejecuta una consulta (INSERT, UPDATE, DELETE) en la BD de prueba."""
    cursor = db_connection.cursor()
    cursor.execute(query, parametros)
    db_connection.commit()
    return cursor.lastrowid

def obtener_datos(query, parametros=()):
    """Obtiene datos de la BD de prueba."""
    cursor = db_connection.cursor()
    cursor.execute(query, parametros)
    return cursor.fetchall()

# --- Clase de Pruebas de Integración ---

class TestIntegracion(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Se ejecuta una vez al inicio de todas las pruebas."""
        cls.root = tk.Tk()
        cls.root.withdraw() # Ocultar la ventana principal de Tkinter

    @classmethod
    def tearDownClass(cls):
        """Se ejecuta una vez al final de todas las pruebas."""
        cls.root.destroy()

    def setUp(self):
        """
        Configura un entorno limpio para CADA prueba: una base de datos en memoria,
        el esquema de tablas y las instancias de las pantallas.
        """
        # 1. Crear una base de datos SQLite en memoria
        self.conn = sqlite3.connect(':memory:')
        configurar_conexion_db(self.conn)

        # 2. Crear las tablas necesarias
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE Clientes (
                id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
                nombres TEXT, apellido_p TEXT, apellido_m TEXT, tipo_persona TEXT,
                correo TEXT, telefono TEXT, rfc TEXT, fecha_registro TEXT, estado INTEGER
            )
        """)
        cursor.execute("""
             CREATE TABLE Medios_pago (
                id_medio_pago INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE Transacciones (
                id_transaccion INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT, tipo TEXT, id_cliente INTEGER, id_medio_pago INTEGER,
                subtotal REAL, impuestos REAL, total REAL, estado TEXT,
                FOREIGN KEY (id_cliente) REFERENCES Clientes(id_cliente),
                FOREIGN KEY (id_medio_pago) REFERENCES Medios_pago(id_medio_pago)
            )
        """)
        self.conn.commit()

        # 3. Inyectar nuestras funciones de BD simuladas en los módulos de la UI
        # Esto asegura que las clases de pantalla usen nuestra BD de prueba.
        # (Esto funciona si tus clases importan directamente las funciones)
        PantallaClientes.__module__.__globals__['obtener_datos'] = obtener_datos
        PantallaClientes.__module__.__globals__['ejecutar_query'] = ejecutar_query
        PantallaTransacciones.__module__.__globals__['obtener_datos'] = obtener_datos

        # 4. Crear instancias de las pantallas
        self.pantalla_clientes = PantallaClientes(self.root)
        self.pantalla_transacciones = PantallaTransacciones(self.root)

    def tearDown(self):
        """Limpia el entorno después de CADA prueba."""
        self.conn.close()

    # --- 5 FUNCIONES DE PRUEBA DE INTEGRACIÓN ---

    def test_1_cargar_transacciones_con_joins(self):
        """
        # Responsable: Tecsi Huallpa Luis Alberto
        Prueba la consulta de carga de transacciones, verificando que los
        JOIN con Clientes y Medios_pago funcionan correctamente para traer
        los nombres en lugar de solo los IDs.
        """
        # Arrange: Insertar datos relacionados en diferentes tablas
        cliente_id = ejecutar_query("INSERT INTO Clientes (nombres, apellido_p) VALUES (?, ?)", ('Ana', 'García'))
        medio_pago_id = ejecutar_query("INSERT INTO Medios_pago (nombre) VALUES (?)", ('Tarjeta de Crédito',))
        
        fecha_transaccion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ejecutar_query(
            """INSERT INTO Transacciones 
               (fecha, tipo, id_cliente, id_medio_pago, subtotal, impuestos, total, estado) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (fecha_transaccion, 'venta', cliente_id, medio_pago_id, 129.31, 20.69, 150.0, 'completada')
        )
        
        # Act: Cargar los datos en la pantalla de transacciones
        self.pantalla_transacciones._cargar_datos()
        
        # Assert: Verificar que los datos cargados contienen la información de las tablas unidas
        self.assertEqual(len(self.pantalla_transacciones.datos), 1)
        transaccion_cargada = self.pantalla_transacciones.datos[0]
        
        self.assertEqual(transaccion_cargada[3], 'Ana García') # Índice 3: 'cliente'
        self.assertEqual(transaccion_cargada[4], 'Tarjeta de Crédito') # Índice 4: 'medio_pago'
        self.assertEqual(transaccion_cargada[7], 150.0) # Índice 7: 'total'

    def test_2_filtrar_clientes_por_estado(self):
        """
        # Responsable: Paucar Quejia Rye Gabriel Gregory
        Prueba la integración del filtro de estado en PantallaClientes.
        Verifica que al seleccionar un estado, la consulta SQL se construye
        correctamente y devuelve solo los registros correspondientes.
        """
        # Arrange: Insertar dos clientes con estados diferentes
        ejecutar_query("INSERT INTO Clientes (nombres, estado) VALUES (?, ?)", ('Cliente Activo', 1))
        ejecutar_query("INSERT INTO Clientes (nombres, estado) VALUES (?, ?)", ('Cliente Inactivo', 0))

        # Act: Simular la selección del filtro "Inactivo" en el ComboBox de la UI
        self.pantalla_clientes.combo_estado.set('Inactivo')
        self.pantalla_clientes._aplicar_filtros() # Este método llama a _cargar_datos

        # Assert: Verificar que solo se cargó el cliente inactivo
        self.assertEqual(len(self.pantalla_clientes.datos), 1)
        cliente_filtrado = self.pantalla_clientes.datos[0]
        self.assertEqual(cliente_filtrado[1], 'Cliente Inactivo  ') # nombre_completo
        self.assertEqual(cliente_filtrado[7], 0) # estado

    def test_3_busqueda_cliente_por_nombre(self):
        """
        # Responsable: Ccahua Huamani Salome Celeste
        Prueba la integración de la barra de búsqueda de clientes.
        Verifica que la cláusula WHERE con LIKE se construye y ejecuta correctamente
        basado en la entrada de texto del usuario.
        """
        # Arrange: Insertar varios clientes
        ejecutar_query("INSERT INTO Clientes (nombres, apellido_p) VALUES (?, ?)", ('Ana', 'García'))
        ejecutar_query("INSERT INTO Clientes (nombres, apellido_p) VALUES (?, ?)", ('Carlos', 'Mendoza'))
        ejecutar_query("INSERT INTO Clientes (nombres, apellido_p) VALUES (?, ?)", ('Carla', 'Jiménez'))

        # Act: Simular la escritura de "Carl" en la barra de búsqueda de la UI
        self.pantalla_clientes.entrada_busqueda.insert(0, "Carl")
        self.pantalla_clientes._aplicar_filtros()

        # Assert: Verificar que se cargaron los dos clientes cuyo nombre empieza con "Carl"
        self.assertEqual(len(self.pantalla_clientes.datos), 2)
        nombres_encontrados = {cliente[1].strip() for cliente in self.pantalla_clientes.datos}
        self.assertEqual(nombres_encontrados, {'Carlos Mendoza', 'Carla Jiménez'})

    def test_4_cambiar_estado_cliente(self):
        """
        # Responsable: Roque Aysa Gabriel Saul
        Prueba el flujo completo de modificar datos: seleccionar un cliente,
        ejecutar la acción para cambiar su estado y verificar que el cambio
        se persistió correctamente en la base de datos.
        """
        # Arrange: Crear un cliente activo y "seleccionarlo" en la tabla
        cliente_id = ejecutar_query("INSERT INTO Clientes (nombres, estado) VALUES (?, ?)", ('Cliente a Cambiar', 1))
        self.pantalla_clientes._cargar_datos()
        
        # Simular la selección del item en el Treeview
        item_id = self.pantalla_clientes.tabla.get_children()[0]
        self.pantalla_clientes.tabla.focus(item_id)
        self.pantalla_clientes.tabla.selection_set(item_id)

        # Simular que el usuario hace clic en "Sí" en el cuadro de diálogo de confirmación
        with patch('tkinter.messagebox.askyesno', return_value=True):
            # Act: Llamar al método que cambia el estado
            self.pantalla_clientes._cambiar_estado_cliente()
        
        # Assert: Verificar directamente en la BD que el estado cambió a 0 (Inactivo)
        resultado = obtener_datos("SELECT estado FROM Clientes WHERE id_cliente = ?", (cliente_id,))
        self.assertEqual(resultado[0][0], 0)

    def test_5_cargar_transaccion_sin_cliente_asignado(self):
        """
        # Responsable: Rivera Cusihuaman Jorcaef Vicente
        Prueba un caso especial importante: cómo la aplicación maneja
        transacciones donde el 'id_cliente' es NULL. Verifica que la lógica
        CASE en la consulta SQL funciona como se espera, mostrando 'Sistema'.
        """
        # Arrange: Insertar una transacción con id_cliente como NULL
        ejecutar_query("""
            INSERT INTO Transacciones (fecha, tipo, id_cliente, total, estado)
            VALUES (?, ?, ?, ?, ?)
            """, (datetime.now(), 'ajuste', None, 50.0, 'completada'))

        # Act: Cargar los datos en la pantalla de transacciones
        self.pantalla_transacciones._cargar_datos()

        # Assert: Verificar que se cargó la transacción y el campo cliente es 'Sistema'
        self.assertEqual(len(self.pantalla_transacciones.datos), 1)
        transaccion_cargada = self.pantalla_transacciones.datos[0]
        
        # El índice 3 corresponde a la columna 'cliente' en la consulta
        self.assertEqual(transaccion_cargada[3], 'Sistema')

if __name__ == '__main__':
    # Esto permite ejecutar el archivo de pruebas directamente
    unittest.main(argv=['first-arg-is-ignored'], exit=False)