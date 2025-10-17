---
Sistema de Ventas - Proyecto Académico   
---

Descripción:
------------
Aplicación de escritorio para gestión integral de ventas, inventario, clientes y operaciones comerciales. 
Desarrollada en Python con interfaz en Tkinter y base de datos SQLite.

Características Principales:
----------------------------
- Gestión de inventario avanzada con:
  Control de stock (mínimo/máximo)
  Sistema de movimientos (entradas/salidas)
  Filtros combinados (categoría + búsqueda)
  Resaltado de stock crítico
- Punto de venta dinámico con carrito
- Registro de clientes con datos fiscales
- Historial completo de transacciones
- Generación básica de facturas (XML/PDF) (No creo que hagamos esto)
- Interfaz unificada con sistema de estilos

Requisitos:
------------
- Python 3.10+ (con módulo tkinter)
- SQLite3 (incluido en Python)
- 150 MB de espacio libre
- Resolución mínima 1024x768

Instalación
--------------------------
Para Arch Linux:
--------------------------
1. Instalar dependencias:
   sudo pacman -S python tk sqlite

2. Clonar repositorio:
   git clone [url-del-repositorio]
   
3. Ejecutar aplicación:
   cd ventas/
   python main.py
---------------------------

Para Windows:
---------------------------
1. Instalar Python (3.9 o superior):
   - Descargar instalador desde https://www.python.org/downloads/
   - Durante la instalación, marcar "Add Python to PATH"

2. Instalar Git:
   - Descargar desde https://git-scm.com/download/win
   - Usar configuración predeterminada

3. Clonar repositorio (desde CMD o PowerShell):
   git clone [url-del-repositorio]
   
4. Ejecutar aplicación:
   cd ventas
   python main.py

Estructura de Directorios:
--------------------------
ventas/                              # Raíz del proyecto
├── data/                            # Datos y estructura de la base de datos
│   ├── estructura.sql               # Script SQL con esquema de la base de datos
│   └── ventas.db                    # Base de datos SQLite (binario)
│
├── db/                              
│   └── db.py                        # Módulo para conexión y operaciones con la base de datos
│
├── ui/                              # Interfaz gráfica y componentes visuales
│   ├── components/                  # Componentes UI reutilizables
│   │   └── header.py                # Barra de navegación superior
│   ├── movimientos/                 # Diálogos para operaciones de inventario
│   │   ├── dialogo_movimientos.py   # Registro de movimientos (entradas/salidas)
│   │   └── dialogo_producto.py      # Formulario para nuevos productos
│   ├── main.py                      # Configuración de ventana principal
│   ├── styles.py                    # Configuración de estilos visuales
│   ├── clientes.py                  # Gestión de clientes (CRUD)
│   ├── facturas.py                  # Módulo de facturación
│   ├── inventario.py                # Gestión de inventario principal
│   ├── movimientos.py               # Historial de movimientos de inventario
│   ├── punto_venta.py               # Pantalla principal de punto de venta (POS)
│   └── transacciones.py             # Registro de transacciones financieras
│
├── utils/
│   └── helpers.py                   # Funciones utilitarias (formateo, cálculos)
│
├── main.py                          # Punto de entrada principal de la aplicación
└── README.txt                       # Instrucciones de instalación y uso

Relaciones clave:
- inventario.py usa diálogos de movimientos/ para operaciones
- header.py provee navegación a todas las pantallas
- db.py es utilizado por todos los módulos para acceso a datos
- styles.py centraliza la configuración visual de la UI

Datos Incluidos:
- Todos los datos son ficticios (generados para pruebas académicas). 

Notas:
-------
- La base de datos inicial se genera en data/ventas.db
- No modificar manualmente tablas SQLite
- Testeado en Arch Linux, Windows 10/11 y macOS 12+
- Requiere permisos de escritura en el directorio

Licencia:
---------
GNU General Public License v3.0 (GPL-3.0)




 

Estado Actual:
--------------
- Base de datos: Tablas creadas, sin datos de prueba.  
- Menú Principal: Botones funcionales para abrir módulos (ventanas vacías por ahora).  
- Gestor de inventario: Tabla con todos los productos, con apartado para realizar movimientos de inventario y nuevos productos.
X Módulos: Falta implementar lógica e integración de los modulos: Clientes, Movimientos, Transacciones, Facturas, Punto de venta

Requisitos Funcionales Pendientes:
----------------------------------
Prioridad Alta (MVP): 
1. Módulo de Punto de Venta (`ui/punto_venta.py`):  
   - Búsqueda de productos por código/nombre (SQL: `LIKE`).  
   - Carrito dinámico con cantidad, precio unitario y descuentos.  
   - Cálculo automático de subtotal, IVA (16%) y total.  
   - Guardar transacción en `Transacciones` y actualizar `stock_actual` en `Productos`.  

2. Módulo de Inventario (`ui/inventario.py`):  (Ya esta)
   - Tabla con todos los productos (`ttk.Treeview`).  
   - Filtros por categoría y búsqueda por nombre/SKU.  
   - Botón para registrar movimientos de entrada/salida (`Movimientos`).  

Prioridad Media: 
3. Módulo de Clientes (`ui/clientes.py`):  
   - CRUD completo con validación de RFC y CURP.  
   - Integración con direcciones fiscales (`Direcciones`).

Requisitos funcionales por pantalla:
------------------------------------
1. main.py
    Ventana principal con botones para abrir cada sección (Tkinter).
    Cierra con confirmación.

2. punto_venta.py
    Búsqueda de producto por código/nombre.
    Agregar al carrito.
    Mostrar totales, IVA.
    Selección rápida de cliente y medio de pago.
    Guardar como transacción venta + insertar en Detalle_transaccion.
    Actualizar stock_actual.

3. inventario.py
    Tabla con todos los productos (Productos).
    Filtros por categoría o búsqueda.
    Botón para realizar entradas o salidas de inventario.
    Botón para agregar productos

4. movimientos.py
    Tabla de Movimientos (fecha, producto, tipo, cantidad, referencia).
    Filtro por producto o fecha.

5. transacciones.py
    Tabla con Transacciones recientes.
    Filtros por cliente, fecha, tipo (venta, compra, etc).
    Detalle al seleccionar (mostrar productos vendidos).

6. clientes.py
    Tabla con todos los Clientes.
    Agregar nuevo cliente (formulario).
    Editar o eliminar cliente.

7. facturas.py
    Tabla de Facturas.
    Botón para ver XML o descargar PDF (si existen).
    Mostrar resumen: subtotal, impuestos, total.  

