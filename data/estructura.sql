-- Tabla Categorias
CREATE TABLE Categorias (
    id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    descripcion TEXT
);

-- Tabla Clientes
CREATE TABLE Clientes (
    id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
    nombres TEXT NOT NULL,
    apellido_p TEXT,
    apellido_m TEXT,
    rfc TEXT,
    curp TEXT,
    correo TEXT,
    telefono TEXT,
    tipo_persona TEXT NOT NULL,
    regimen_fiscal TEXT,
    fecha_registro TEXT,
    estado INTEGER
);

-- Tabla Detalle_transaccion
CREATE TABLE Detalle_transaccion (
    id_detalle INTEGER PRIMARY KEY AUTOINCREMENT,
    id_transaccion INTEGER,
    id_producto INTEGER,
    cantidad INTEGER NOT NULL,
    precio_unitario REAL NOT NULL,
    descuento REAL,
    iva_aplicado REAL,
    FOREIGN KEY(id_transaccion) REFERENCES Transacciones(id_transaccion) ON DELETE CASCADE,
    FOREIGN KEY(id_producto) REFERENCES Productos(id_producto)
);

-- Tabla Direcciones
CREATE TABLE Direcciones (
    id_direccion INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente INTEGER,
    calle TEXT,
    numero_domicilio TEXT,
    colonia TEXT,
    ciudad TEXT,
    entidad TEXT,
    codigo_postal TEXT,
    referencias TEXT,
    tipo TEXT NOT NULL,
    principal INTEGER,
    FOREIGN KEY(id_cliente) REFERENCES Clientes(id_cliente) ON DELETE CASCADE
);

-- Tabla Facturas
CREATE TABLE Facturas (
    id_factura INTEGER PRIMARY KEY AUTOINCREMENT,
    id_transaccion INTEGER,
    id_direccion_fiscal INTEGER,
    uuid TEXT,
    serie TEXT,
    folio TEXT,
    fecha_emision TEXT,
    lugar_expedicion TEXT,
    forma_pago TEXT,
    metodo_pago TEXT,
    uso_cfdi TEXT,
    nombre_cliente TEXT,
    rfc_cliente TEXT,
    subtotal REAL NOT NULL,
    iva REAL,
    total REAL NOT NULL,
    xml TEXT,
    pdf BLOB,
    estado TEXT NOT NULL,
    FOREIGN KEY(id_transaccion) REFERENCES Transacciones(id_transaccion),
    FOREIGN KEY(id_direccion_fiscal) REFERENCES Direcciones(id_direccion)
);

-- Tabla Medios_pago
CREATE TABLE Medios_pago (
    id_medio_pago INTEGER PRIMARY KEY AUTOINCREMENT,
    clave_sat TEXT NOT NULL,
    nombre TEXT NOT NULL,
    descripcion TEXT
);

-- Tabla Movimientos
CREATE TABLE Movimientos (
    id_movimiento INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    fecha TEXT,
    cantidad INTEGER NOT NULL,
    id_producto INTEGER,
    id_usuario INTEGER,
    referencia TEXT,
    FOREIGN KEY(id_producto) REFERENCES Productos(id_producto),
    FOREIGN KEY(id_usuario) REFERENCES Usuarios(id_usuario)
);

-- Tabla Productos
CREATE TABLE Productos (
    id_producto INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    descripcion TEXT,
    precio_venta REAL NOT NULL,
    costo REAL NOT NULL,
    codigo_barras TEXT,
    sku TEXT,
    stock_minimo INTEGER,
    stock_maximo INTEGER,
    stock_actual INTEGER,
    id_categoria INTEGER,
    id_proveedor INTEGER,
    fecha_creacion TEXT,
    estado INTEGER,
    FOREIGN KEY(id_categoria) REFERENCES Categorias(id_categoria),
    FOREIGN KEY(id_proveedor) REFERENCES Proveedores(id_proveedor)
);

-- Tabla Proveedores
CREATE TABLE Proveedores (
    id_proveedor INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    rfc TEXT,
    calle TEXT,
    numero_domicilio TEXT,
    colonia TEXT,
    ciudad TEXT,
    entidad TEXT,
    codigo_postal TEXT,
    telefono TEXT,
    correo TEXT,
    fecha_registro TEXT,
    estado INTEGER
);

-- Tabla Transacciones
CREATE TABLE Transacciones (
    id_transaccion INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    fecha TEXT,
    id_cliente INTEGER,
    id_usuario INTEGER,
    id_medio_pago INTEGER,
    subtotal REAL NOT NULL,
    impuestos REAL,
    total REAL NOT NULL,
    moneda TEXT,
    tipo_cambio REAL,
    estado TEXT NOT NULL,
    FOREIGN KEY(id_cliente) REFERENCES Clientes(id_cliente),
    FOREIGN KEY(id_medio_pago) REFERENCES Medios_pago(id_medio_pago),
    FOREIGN KEY(id_usuario) REFERENCES Usuarios(id_usuario)
);

-- Tabla Usuarios
CREATE TABLE Usuarios (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nombres TEXT NOT NULL,
    apellido_p TEXT,
    apellido_m TEXT,
    puesto TEXT,
    correo TEXT NOT NULL,
    contrasena_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    telefono TEXT,
    fecha_registro TEXT,
    ultimo_login TEXT,
    permisos TEXT,
    estado INTEGER
);
