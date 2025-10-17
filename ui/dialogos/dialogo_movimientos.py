import tkinter as tk
from tkinter import ttk, messagebox
from db.db import ejecutar_query, obtener_datos, ejecutar_transaccion
from ui.dialogos.dialogo_producto import DialogoProducto

class DialogoMovimiento:
    """
    Diálogo para registrar movimientos de inventario con validaciones
    
    Atributos:
        parent (tk.Widget): Ventana padre del diálogo
        productos (list): Lista de productos disponibles
        callback_actualizar (function): Función para actualizar la vista principal
        dialogo (tk.Toplevel): Ventana del diálogo
    """
    
    TIPOS_MOVIMIENTO = ['entrada', 'salida', 'transferencia']
    
    def __init__(self, parent, productos, callback_actualizar):
        """
        Inicializa el diálogo de movimientos
        
        Args:
            parent (tk.Widget): Ventana padre
            productos (list): Lista de productos para búsqueda
            callback_actualizar (function): Callback para actualizar datos
        """
        self.parent = parent
        self.productos = productos
        self.callback_actualizar = callback_actualizar
        
        self._configurar_ventana()
        self._crear_widgets()
        
    def _configurar_ventana(self):
        """Configura las propiedades de la ventana"""
        self.dialogo = tk.Toplevel(self.parent)
        self.dialogo.title("Registrar Movimiento")
        self.dialogo.geometry("400x350") 
        self.dialogo.grab_set()
        self.dialogo.protocol("WM_DELETE_WINDOW", self._cerrar_dialogo)

    def _crear_widgets(self):
        """Construye todos los elementos de la interfaz"""
        contenido = ttk.Frame(self.dialogo, padding=10)
        contenido.pack(fill=tk.BOTH, expand=True)
        
        # Configuración del grid
        contenido.columnconfigure(1, weight=1)
        
        # Tipo de movimiento
        self._crear_campo(contenido, "Tipo de Movimiento:", 0, 'combobox')
        
        # Búsqueda de producto
        self._crear_campo(contenido, "Buscar Producto:", 1, 'entry', 
                        evento_busqueda=self._actualizar_lista_productos)
        
        # Lista de productos
        self.lista_productos = tk.Listbox(contenido, height=5)
        self.lista_productos.grid(row=2, column=0, columnspan=2, 
                                sticky=tk.EW, pady=5, padx=5)
        self._actualizar_lista_productos()
        
        # Cantidad
        self._crear_campo(contenido, "Cantidad:", 3, 'entry')
        
        # Referencia
        self._crear_campo(contenido, "Referencia:", 4, 'entry')
        
        # Botones
        self._crear_botones(contenido, 5)

    def _crear_campo(self, padre, etiqueta, fila, tipo, evento_busqueda=None):
        """
        Crea un campo del formulario con su etiqueta
        
        Args:
            padre (tk.Widget): Contenedor padre
            etiqueta (str): Texto de la etiqueta
            fila (int): Fila del grid
            tipo (str): Tipo de widget ('entry' o 'combobox')
            evento_busqueda (function): Función para manejar búsquedas
        """
        ttk.Label(padre, text=etiqueta).grid(row=fila, column=0, sticky=tk.W)
        
        if tipo == 'combobox':
            widget = ttk.Combobox(
                padre,
                values=self.TIPOS_MOVIMIENTO,
                state="readonly"
            )
            widget.current(0)
        else:
            widget = ttk.Entry(padre)
            if evento_busqueda:
                widget.bind("<KeyRelease>", evento_busqueda)
        
        widget.grid(row=fila, column=1, sticky=tk.EW, pady=5)
        
        # Asignar a atributos según el tipo de campo
        if "Tipo" in etiqueta:
            self.tipo_movimiento = widget
        elif "Buscar" in etiqueta:
            self.busqueda_producto = widget
        elif "Cantidad" in etiqueta:
            self.cantidad_movimiento = widget
        else:
            self.referencia_movimiento = widget

    def _crear_botones(self, padre, fila):
        """Crea la sección de botones"""
        btn_frame = ttk.Frame(padre)
        btn_frame.grid(row=fila, column=0, columnspan=2, pady=10, sticky=tk.E)
        
        ttk.Button(
            btn_frame,
            text="➕ Nuevo Producto",
            style="Secondary.TButton",
            command=self._abrir_dialogo_nuevo_producto
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Cancelar",
            style="Secondary.TButton",
            command=self._cerrar_dialogo
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="Guardar",
            style="Primary.TButton",
            command=self._validar_movimiento
        ).pack(side=tk.RIGHT, padx=5)

    def _actualizar_lista_productos(self, event=None):
        """
        Actualiza la lista de productos según el texto de búsqueda
        
        Args:
            event (tk.Event): Evento de teclado opcional
        """
        busqueda = self.busqueda_producto.get().strip().lower()
        self.lista_productos.delete(0, tk.END)
        
        # Búsqueda en múltiples campos: ID, nombre, SKU y código de barras
        for producto in self.productos:
            texto_match = (
                busqueda in str(producto[0]).lower() or       # ID
                busqueda in producto[1].lower() or           # Nombre
                (producto[9] and busqueda in producto[9].lower()) or  # SKU
                (producto[10] and busqueda in producto[10].lower()))    # Código
                
            if texto_match:
                self.lista_productos.insert(tk.END, f"{producto[0]} - {producto[1]}")

    def _abrir_dialogo_nuevo_producto(self):
        """Abre el diálogo para crear nuevos productos"""
        DialogoProducto(self.dialogo, self.callback_actualizar)

    def _validar_movimiento(self):
        """Ejecuta todas las validaciones antes de guardar"""
        try:
            # Validación de selección de producto
            seleccion = self.lista_productos.curselection()
            if not seleccion:
                raise ValueError("Debe seleccionar un producto de la lista")
            
            # Validación de cantidad
            cantidad = self._validar_cantidad()
            
            # Validación de stock disponible para salidas
            if self.tipo_movimiento.get() in ['salida', 'transferencia']:
                self._validar_stock_disponible(cantidad)
            
            # Si pasa todas las validaciones, guardar
            self._guardar_movimiento()
            
        except ValueError as e:
            messagebox.showerror("Error de validación", str(e), parent=self.dialogo)
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado:\n{str(e)}", parent=self.dialogo)

    def _validar_cantidad(self):
        """Valida que la cantidad sea un número entero positivo"""
        try:
            cantidad = int(self.cantidad_movimiento.get())
            if cantidad <= 0:
                raise ValueError("La cantidad debe ser mayor a cero")
            return cantidad
        except ValueError:
            raise ValueError("La cantidad debe ser un número entero válido")

    def _validar_stock_disponible(self, cantidad_solicitada):
        """
        Valida que haya suficiente stock para salidas/transferencias
        
        Args:
            cantidad_solicitada (int): Cantidad a descontar
            
        Raises:
            ValueError: Si no hay suficiente stock
        """
        producto_str = self.lista_productos.get(self.lista_productos.curselection())
        id_producto = int(producto_str.split(" - ")[0])
        
        stock_actual = obtener_datos(
            "SELECT stock_actual FROM Productos WHERE id_producto = ?",
            (id_producto,)
        )[0][0]
        
        if stock_actual < cantidad_solicitada:
            raise ValueError(
                f"Stock insuficiente. Disponible: {stock_actual}\n"
                f"Solicitado: {cantidad_solicitada}"
            )

    def _guardar_movimiento(self):
        """Ejecuta las operaciones de base de datos para guardar el movimiento"""
        try:
            # Obtener datos del formulario
            producto_str = self.lista_productos.get(self.lista_productos.curselection())
            id_producto = int(producto_str.split(" - ")[0])
            tipo = self.tipo_movimiento.get()
            cantidad = int(self.cantidad_movimiento.get())
            referencia = self.referencia_movimiento.get().strip()
            
            # Ajustar cantidad según tipo de movimiento
            cantidad_ajustada = -cantidad if tipo in ['salida', 'transferencia'] else cantidad
            
            # Transacción en base de datos
            queries = [
                (
                    """INSERT INTO Movimientos (
                        tipo, fecha, cantidad, id_producto, referencia
                    ) VALUES (?, datetime('now'), ?, ?, ?)""",
                    (tipo, cantidad_ajustada, id_producto, referencia)
                ),
                (
                    """UPDATE Productos 
                    SET stock_actual = stock_actual + ? 
                    WHERE id_producto = ?""",
                    (cantidad_ajustada, id_producto)
                )
            ]
            
            # Ejecutar transacción atómica
            ejecutar_transaccion(queries)
                
            messagebox.showinfo(
                "Éxito", 
                "Movimiento registrado correctamente", 
                parent=self.dialogo
            )
            self.callback_actualizar()
            self._cerrar_dialogo()
            
        except Exception as e:
            messagebox.showerror(
                "Error", 
                f"Error al guardar movimiento:\n{str(e)}",  # Corregir paréntesis si es necesario
                parent=self.dialogo
            )
    
    def _cerrar_dialogo(self):
        """Cierra la ventana y libera recursos"""
        self.dialogo.destroy()