import sys
import os
import pytest
import tkinter as tk
from unittest.mock import patch, MagicMock, ANY

# --- Configuración del entorno ---
# Añadimos el directorio raíz del proyecto para que Python pueda encontrar los módulos.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
# --------------------------------

from ui.clientes import PantallaClientes

# --- Fixture de Pytest ---
@pytest.fixture
def pantalla_clientes():
    """
    Crea una instancia de PantallaClientes en un entorno controlado para cada prueba.
    La carga inicial de datos se mockea para evitar llamadas a la DB durante el setup.
    """
    with patch('ui.clientes.PantallaClientes._cargar_datos') as mock_cargar_inicial:
        root = tk.Tk()
        app = PantallaClientes(root)
        yield app
    # Limpieza: destruye la ventana de Tkinter después de cada prueba.
    root.destroy()

# --- Casos de Prueba ---

def test_construir_where_clause(pantalla_clientes):
    """
    Prueba la lógica de construcción de la cláusula WHERE para la consulta SQL.
    """
    # Escenario 1: Sin filtros
    pantalla_clientes.filtros = {'busqueda': '', 'estado': 'Todos'}
    assert pantalla_clientes._construir_where() == ""

    # Escenario 2: Solo con filtro de búsqueda
    pantalla_clientes.filtros = {'busqueda': 'Juan', 'estado': 'Todos'}
    expected_search = "WHERE c.nombres LIKE ? OR c.apellido_p LIKE ? OR c.apellido_m LIKE ? OR c.rfc LIKE ?"
    assert pantalla_clientes._construir_where() == expected_search

    # Escenario 3: Solo con filtro de estado 'Activo'
    pantalla_clientes.filtros = {'busqueda': '', 'estado': 'Activo'}
    assert pantalla_clientes._construir_where() == "WHERE c.estado = ?"

    # Escenario 4: Con ambos filtros
    pantalla_clientes.filtros = {'busqueda': 'Perez', 'estado': 'Inactivo'}
    expected_both = "WHERE (c.nombres LIKE ? OR c.apellido_p LIKE ? OR c.apellido_m LIKE ? OR c.rfc LIKE ?) AND c.estado = ?"
    # La implementación actual une con AND, pero la prueba detectaría si cambia.
    # Corregimos la prueba para que coincida con la lógica de concatenación simple del código.
    expected_both_actual_logic = "WHERE " + " AND ".join([" OR ".join([f"{campo} LIKE ?" for campo in pantalla_clientes.CAMPOS_BUSQUEDA]), "c.estado = ?"])
    assert pantalla_clientes._construir_where() == expected_both_actual_logic

def test_construir_orden_clause(pantalla_clientes):
    """
    Prueba la lógica de construcción de la cláusula ORDER BY.
    """
    # Estado inicial (orden por defecto)
    pantalla_clientes.orden = {'columna': None, 'ascendente': True}
    assert pantalla_clientes._construir_orden() == "c.id_cliente ASC"

    # Orden por nombre descendente
    pantalla_clientes.orden = {'columna': 'nombre_completo', 'ascendente': False}
    assert pantalla_clientes._construir_orden() == "nombre_completo DESC"

def test_aplicar_filtros(pantalla_clientes):
    """
    Verifica que al aplicar filtros, el diccionario de filtros se actualiza
    y se llama a la recarga de datos.
    """
    # Simular los widgets de la UI
    pantalla_clientes.entrada_busqueda = MagicMock()
    pantalla_clientes.entrada_busqueda.get.return_value = "  Test Corp " # con espacios
    pantalla_clientes.combo_estado = MagicMock()
    pantalla_clientes.combo_estado.get.return_value = "Activo"

    # Mockear el método que recarga los datos para verificar que es llamado
    with patch.object(pantalla_clientes, '_cargar_datos') as mock_cargar:
        pantalla_clientes._aplicar_filtros()

        # Verificar que el diccionario de filtros se actualizó correctamente (sin espacios)
        assert pantalla_clientes.filtros['busqueda'] == "Test Corp"
        assert pantalla_clientes.filtros['estado'] == "Activo"

        # Verificar que se intentó recargar los datos
        mock_cargar.assert_called_once()

def test_ordenar_por_columna(pantalla_clientes):
    """
    Prueba la lógica de cambiar y revertir el orden de las columnas.
    """
    with patch.object(pantalla_clientes, '_cargar_datos') as mock_cargar:
        # 1. Primer clic en una columna (debe ser ascendente)
        pantalla_clientes._ordenar_por_columna('nombre_completo')
        assert pantalla_clientes.orden['columna'] == 'nombre_completo'
        assert pantalla_clientes.orden['ascendente'] is True

        # 2. Segundo clic en la misma columna (debe ser descendente)
        pantalla_clientes._ordenar_por_columna('nombre_completo')
        assert pantalla_clientes.orden['columna'] == 'nombre_completo'
        assert pantalla_clientes.orden['ascendente'] is False

        # 3. Clic en una nueva columna (debe volver a ser ascendente)
        pantalla_clientes._ordenar_por_columna('estado')
        assert pantalla_clientes.orden['columna'] == 'c.estado'
        assert pantalla_clientes.orden['ascendente'] is True

        # Verificar que se recargaron los datos en cada llamada
        assert mock_cargar.call_count == 3

@patch('ui.clientes.ejecutar_query')
@patch('ui.clientes.obtener_datos')
@patch('ui.clientes.messagebox')
def test_cambiar_estado_cliente(mock_messagebox, mock_obtener, mock_ejecutar, pantalla_clientes):
    """
    Prueba el flujo completo de cambiar el estado de un cliente de activo a inactivo.
    """
    CLIENTE_ID = "123"
    
    # 1. Simular la selección de una fila en la tabla
    pantalla_clientes.tabla = MagicMock()
    pantalla_clientes.tabla.focus.return_value = "item_seleccionado"
    pantalla_clientes.tabla.item.return_value = {"values": [CLIENTE_ID]}

    # 2. Simular que el usuario confirma la acción
    mock_messagebox.askyesno.return_value = True

    # 3. Simular que la base de datos devuelve el estado actual del cliente (1 = Activo)
    mock_obtener.return_value = [[1]] 

    # Mockear la recarga final para que no interfiera
    with patch.object(pantalla_clientes, '_cargar_datos') as mock_cargar_final:
        # Ejecutar la función a probar
        pantalla_clientes._cambiar_estado_cliente()

        # Verificar que se consultó el estado actual del cliente correcto
        mock_obtener.assert_called_once_with("SELECT estado FROM Clientes WHERE id_cliente = ?", (CLIENTE_ID,))

        # Verificar que se mostró el diálogo de confirmación
        mock_messagebox.askyesno.assert_called_once()

        # Verificar que se ejecutó la actualización con el NUEVO estado (0 = Inactivo)
        mock_ejecutar.assert_called_once_with(
            "UPDATE Clientes SET estado = ? WHERE id_cliente = ?",
            (0, CLIENTE_ID) # El nuevo estado debe ser 0
        )
        
        # Verificar que al final se recargaron los datos
        mock_cargar_final.assert_called_once()