import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from db.db import ejecutar_query, obtener_datos
from ui.dialogos.dialogo_proveedor import DialogoProveedor
from ui.dialogos.dialogo_categoria import DialogoCategoria

class DialogoProducto:
    """
    Diálogo para la creación y edición de productos con validación avanzada
    
    Atributos:
        parent (tk.Widget): Ventana padre del diálogo
        callback_actualizar (function): Función para actualizar la lista principal después de guardar
        categorias (list): Lista de tuplas (id, nombre) de categorías disponibles
        proveedores (list): Lista de tuplas (id, nombre) de proveedores disponibles
        entries (dict): Diccionario con los widgets de entrada del formulario
        errores (dict): Diccionario con las etiquetas de error para cada campo
    """
    
    def __init__(self, parent, callback_actualizar):
        """Inicializa el diálogo y carga datos necesarios"""
        self.parent = parent
        self.callback_actualizar = callback_actualizar
        self.categorias = []
        self.proveedores = []
        
        self._cargar_datos_soporte()  # Carga datos relacionales
        self._crear_dialogo()         # Configura la ventana
        self._crear_widgets()         # Construye la interfaz

    def _cargar_datos_soporte(self):
        """Carga datos de catálogos para los combobox (categorías y proveedores)"""
        self.categorias = obtener_datos(
            "SELECT id_categoria, nombre FROM Categorias ORDER BY nombre"
        )
        self.proveedores = obtener_datos(
            "SELECT id_proveedor, nombre FROM Proveedores ORDER BY nombre"
        )

    def _crear_dialogo(self):
        """Configura las propiedades básicas de la ventana de diálogo"""
        self.dialogo = tk.Toplevel(self.parent)
        self.dialogo.title("Nuevo Producto")
        self.dialogo.geometry("600x750") 
        self.dialogo.grab_set()  # Modal: bloquea interacción con otras ventanas
        self.dialogo.protocol("WM_DELETE_WINDOW", self._cerrar_dialogo)

    def _crear_widgets(self):
        """Construye todos los elementos de la interfaz gráfica"""
        contenido = ttk.Frame(self.dialogo, padding=15)
        contenido.pack(fill=tk.BOTH, expand=True)
        
        # Configurar expansión de columnas
        contenido.columnconfigure(0, weight=1)
        contenido.columnconfigure(1, weight=1)
        
        # Definición de campos del formulario:
        # (campo_id, etiqueta, requerido, tipo_widget)
        campos = [
            ('nombre', 'Nombre:', True, 'text'),
            ('descripcion', 'Descripción:', False, 'text'),
            ('precio_venta', 'Precio Venta ($):', True, 'number'),
            ('costo', 'Costo ($):', True, 'number'),
            ('codigo_barras', 'Código Barras:', False, 'text'),
            ('sku', 'SKU:', False, 'text'),
            ('stock_minimo', 'Stock Mínimo:', True, 'integer'),
            ('stock_maximo', 'Stock Máximo:', True, 'integer'),
            ('stock_actual', 'Stock Inicial:', True, 'integer'),
            ('categoria', 'Categoría:', False, 'combo'),
            ('proveedor', 'Proveedor:', False, 'combo')
        ]
        
        self.entries = {}  # Almacena referencias a los widgets de entrada
        self.errores = {}  # Almacena etiquetas para mensajes de error
        
        # Crear dinámicamente cada fila del formulario
        for i, (campo_id, etiqueta, requerido, tipo) in enumerate(campos):
            self._crear_fila_formulario(contenido, i * 2, campo_id, etiqueta, requerido, tipo)
        
        self._crear_botones(contenido, len(campos))

    def _crear_fila_formulario(self, padre, fila, campo_id, etiqueta, requerido, tipo):
        """Crea una fila del formulario con su widget y etiqueta de error"""
        # Marco contenedor para alinear elementos
        frame = ttk.Frame(padre)
        frame.grid(row=fila, column=0, columnspan=2, sticky=tk.EW, pady=5)
        
        # Etiqueta del campo
        lbl_text = f"{etiqueta}{' *' if requerido else ''}"
        lbl = ttk.Label(frame, text=lbl_text)
        lbl.pack(side=tk.LEFT, anchor=tk.W)
        
        # Widget de entrada
        entry = self._crear_widget_entrada(frame, campo_id, tipo)
        entry.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        self.entries[campo_id] = entry
        
        # Etiqueta de error (debajo del campo)
        self.errores[campo_id] = ttk.Label(
            padre, 
            foreground='red',
            font=('Helvetica', 8)
        )
        self.errores[campo_id].grid(row=fila + 1, column=0, columnspan=2, sticky=tk.W)

    def _crear_widget_entrada(self, frame, campo_id, tipo):
        """Crea el widget de entrada apropiado según el tipo especificado"""
        if tipo == 'combo':
            return self._crear_combobox(frame, campo_id)
        
        # Para campos numéricos, podríamos añadir validación input
        return ttk.Entry(frame)

    def _crear_combobox(self, frame, campo_id):
        """Crea un combobox con valores según categorías o proveedores"""
        combo = ttk.Combobox(frame, state="readonly")
        valores = ["Seleccionar..."]  # Valor por defecto
        
        if campo_id == 'categoria':
            valores += [c[1] for c in self.categorias]
        else:
            valores += [p[1] for p in self.proveedores]
        
        combo['values'] = valores
        combo.current(0)
        return combo

    def _actualizar_combobox(self, campo, datos):
        """Actualiza los valores de un combobox específico"""
        combo = self.entries[campo]
        current_value = combo.get()
        
        # Generar nuevos valores
        nuevos_valores = ["Seleccionar..."] + [item[1] for item in datos]
        combo['values'] = nuevos_valores
        
        # Restaurar selección previa si existe
        if current_value in nuevos_valores:
            combo.set(current_value)
        else:
            combo.current(0)

    def _crear_botones(self, padre, ultima_fila):
        """Crea la sección de botones con nuevas opciones"""
        btn_frame = ttk.Frame(padre)
        btn_frame.grid(row=ultima_fila * 2 + 2, column=0, columnspan=2, pady=15, sticky=tk.EW)
        
        # Botones de adición rápida (izquierda)
        ttk.Button(
            btn_frame,
            text="➕ Proveedor",
            style="Secondary.TButton",
            command=self._abrir_dialogo_proveedor
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            btn_frame,
            text="➕ Categoría",
            style="Secondary.TButton",
            command=self._abrir_dialogo_categoria
        ).pack(side=tk.LEFT, padx=2)
        
        # Botones principales (derecha)
        ttk.Button(
            btn_frame,
            text="Cancelar",
            style="Secondary.TButton",
            command=self._cerrar_dialogo
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Guardar Producto",
            style="Primary.TButton",
            command=self._validar_formulario
        ).pack(side=tk.RIGHT, padx=5)

    def _abrir_dialogo_proveedor(self):
        """Abre diálogo para nuevo proveedor y actualiza datos"""
        DialogoProveedor(
            parent=self.dialogo,
            callback_actualizar=self._actualizar_lista_proveedores
        )
    
    def _abrir_dialogo_categoria(self):
        """Abre diálogo para nueva categoría y actualiza datos"""
        DialogoCategoria(
            parent=self.dialogo,
            callback_actualizar=self._actualizar_lista_categorias
        )

    def _actualizar_lista_proveedores(self):
        """Recarga proveedores y actualiza combobox"""
        self._cargar_datos_soporte()
        self._actualizar_combobox('proveedor', self.proveedores)

    def _actualizar_lista_categorias(self):
        """Recarga categorías y actualiza combobox"""
        self._cargar_datos_soporte()
        self._actualizar_combobox('categoria', self.categorias)

    def _validar_formulario(self):
        """
        Coordina el proceso de validación completo:
        1. Campos requeridos
        2. Formatos numéricos
        3. Lógica de negocio
        4. Unicidad de SKU/código de barras
        """
        validado = True
        self._limpiar_errores()
        
        # Validación básica de campos requeridos
        validado &= self._validar_requeridos()
        
        # Validación de formatos numéricos
        validado &= self._validar_campos_numericos()
        
        # Validación de reglas de negocio
        if validado:
            validado &= self._validar_stocks()
            validado &= self._validar_precio_costo()
        
        # Validación de unicidad
        validado &= self._validar_unicidad()
        
        if validado:
            self._confirmar_guardado()

    def _limpiar_errores(self):
        """Restablece todos los mensajes de error"""
        for error in self.errores.values():
            error.config(text="")

    def _validar_requeridos(self):
        """Verifica campos obligatorios no vacíos"""
        validado = True
        for campo in ['nombre', 'precio_venta', 'costo', 
                    'stock_minimo', 'stock_maximo', 'stock_actual']:
            valor = self.entries[campo].get().strip()
            if not valor:
                self._mostrar_error(campo, "Este campo es requerido")
                validado = False
        return validado

    def _validar_campos_numericos(self):
        """Valida formato correcto para campos numéricos"""
        return (
            self._validar_numero('precio_venta', decimal=True) and
            self._validar_numero('costo', decimal=True) and
            self._validar_numero('stock_minimo') and
            self._validar_numero('stock_maximo') and
            self._validar_numero('stock_actual')
        )

    def _validar_numero(self, campo, decimal=False):
        """
        Valida que el valor sea un número válido
        Args:
            campo (str): ID del campo a validar
            decimal (bool): Indica si acepta decimales
        Returns:
            bool: True si es válido, False si no
        """
        try:
            valor = self.entries[campo].get().strip()
            if not valor:
                return False  # Ya validado en requeridos
            
            if decimal:
                num = float(valor)
                if num <= 0:
                    raise ValueError("Debe ser mayor a 0")
            else:
                num = int(valor)
                if num < 0:
                    raise ValueError("No puede ser negativo")
            
            return True
        except ValueError as e:
            self._mostrar_error(campo, str(e))
            return False

    def _validar_stocks(self):
        """Valida coherencia entre stock mínimo y máximo"""
        stock_min = int(self.entries['stock_minimo'].get())
        stock_max = int(self.entries['stock_maximo'].get())
        
        if stock_min > stock_max:
            self._mostrar_error('stock_maximo', 
                "El stock máximo no puede ser menor al mínimo")
            return False
        return True

    def _validar_precio_costo(self):
        """Confirma si el precio es menor al costo (requiere confirmación)"""
        precio = float(self.entries['precio_venta'].get())
        costo = float(self.entries['costo'].get())
        
        if precio < costo:
            return messagebox.askyesno(
                "Confirmar", 
                "¡El precio es menor al costo! ¿Desea continuar?"
            )
        return True

    def _validar_unicidad(self):
        """Valida que SKU y código de barras sean únicos (si se proporcionan)"""
        validado = True
        sku = self.entries['sku'].get().strip()
        codigo = self.entries['codigo_barras'].get().strip()
        
        if sku:
            validado &= self._validar_unico('sku', sku)
        
        if codigo:
            validado &= self._validar_unico('codigo_barras', codigo)
        
        return validado

    def _validar_unico(self, campo, valor):
        """
        Verifica en la base de datos si el valor ya existe
        Args:
            campo (str): Nombre de la columna en la base de datos
            valor (str): Valor a verificar
        Returns:
            bool: True si es único, False si existe duplicado
        """
        query = f"SELECT COUNT(*) FROM Productos WHERE {campo} = ?"
        existe = obtener_datos(query, (valor,))[0][0] > 0
        
        if existe:
            self._mostrar_error(campo, f"Este {campo.replace('_', ' ')} ya existe")
            return False
        return True

    def _mostrar_error(self, campo, mensaje):
        """Muestra un mensaje de error debajo del campo correspondiente"""
        self.errores[campo].config(text=mensaje)

    def _obtener_id_seleccion(self, tipo, valor):
        """
        Convierte el nombre seleccionado en un combo al ID correspondiente
        Args:
            tipo (str): 'categoria' o 'proveedor'
            valor (str): Nombre mostrado en el combo
        Returns:
            int/None: ID correspondiente o None si no se seleccionó
        """
        if valor == "Seleccionar...":
            return None
        
        datos = self.categorias if tipo == 'categoria' else self.proveedores
        for item in datos:
            if item[1] == valor:
                return item[0]
        return None  # No encontrado (no debería ocurrir pero por alguna razon paso xd)

    def _confirmar_guardado(self):
        """Recolecta datos validados y ejecuta el guardado final"""
        try:
            datos = self._preparar_datos()
            self._guardar_en_db(datos)
            self._cerrar_dialogo()
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar:\n{str(e)}")

    def _preparar_datos(self):
        """Empaqueta los datos del formulario en un diccionario para la DB"""
        return {
            'nombre': self.entries['nombre'].get().strip(),
            'descripcion': self.entries['descripcion'].get().strip() or None,
            'precio_venta': float(self.entries['precio_venta'].get()),
            'costo': float(self.entries['costo'].get()),
            'codigo_barras': self.entries['codigo_barras'].get().strip() or None,
            'sku': self.entries['sku'].get().strip() or None,
            'stock_minimo': int(self.entries['stock_minimo'].get()),
            'stock_maximo': int(self.entries['stock_maximo'].get()),
            'stock_actual': int(self.entries['stock_actual'].get()),
            'id_categoria': self._obtener_id_seleccion(
                'categoria', 
                self.entries['categoria'].get()
            ),
            'id_proveedor': self._obtener_id_seleccion(
                'proveedor', 
                self.entries['proveedor'].get()
            )
        }

    def _guardar_en_db(self, datos):
        """Ejecuta la inserción en la base de datos"""
        ejecutar_query(
            """INSERT INTO Productos (
                nombre, descripcion, precio_venta, costo,
                codigo_barras, sku, stock_minimo, stock_maximo, stock_actual,
                id_categoria, id_proveedor, fecha_creacion, estado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), 1)""",
            tuple(datos.values())
        )
        messagebox.showinfo("Éxito", "Producto creado exitosamente")
        self.callback_actualizar()

    def _cerrar_dialogo(self):
        """Cierra la ventana y libera recursos"""
        self.dialogo.destroy()