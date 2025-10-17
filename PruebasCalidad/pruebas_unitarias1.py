import sys
import os
import pytest
import tkinter as tk
from unittest.mock import patch, MagicMock

# --- Configuraci�n del entorno ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)
# --------------------------------

from ui.movimientos import PantallaMovimientos

# --- Datos de Prueba ---
# SE ELIMIN� EL ACENTO para evitar cualquier error de codificaci�n.
DATOS_MOCK = [
    (1, 'ENTRADA', '15/10/2025 10:00', 10, 'Laptop Modelo X', 'Admin User', 'Compra a proveedor A'),
    (2, 'SALIDA', '15/10/2025 11:30', -5, 'Mouse Inalambrico', 'Vendedor 1', 'Venta a cliente B'),
    (3, 'ENTRADA', '16/10/2025 09:00', 20, 'Teclado Mecanico', 'Admin User', 'Recepcion de stock'),
]

# --- Fixture de Pytest ---
@pytest.fixture
def pantalla_movimientos():
    """
    Crea una instancia de PantallaMovimientos en un entorno controlado para cada prueba.
    """
    root = tk.Tk()
    with patch('ui.movimientos.obtener_datos', return_value=DATOS_MOCK):
        app = PantallaMovimientos(root)
        yield app
    root.destroy()

# --- Casos de Prueba ---

def test_carga_inicial_de_datos(pantalla_movimientos):
    """
    Verifica que los datos se cargan correctamente al inicializar el componente.
    """
    assert pantalla_movimientos.datos == DATOS_MOCK
    
    with patch('ui.movimientos.obtener_datos') as mock_obtener_datos:
        pantalla_movimientos.sort_column = 'm.id_movimiento'
        pantalla_movimientos.sort_ascending = False
        
        pantalla_movimientos._cargar_datos()
        mock_obtener_datos.assert_called_once()
        
        query_base = """
            SELECT 
                m.id_movimiento,
                m.tipo,
                strftime('%d/%m/%Y %H:%M', m.fecha) as fecha_formateada,
                m.cantidad,
                p.nombre AS producto,
                COALESCE(u.nombres || ' ' || u.apellido_p, 'Sistema') AS usuario,
                m.referencia
            FROM Movimientos m
            LEFT JOIN Productos p ON m.id_producto = p.id_producto
            LEFT JOIN Usuarios u ON m.id_usuario = u.id_usuario
            ORDER BY {} {}
        """
        query_esperada = query_base.format(
            pantalla_movimientos.sort_column, 
            'ASC' if pantalla_movimientos.sort_ascending else 'DESC'
        )

        args, _ = mock_obtener_datos.call_args
        query_real = args[0]
        
        assert ' '.join(query_real.split()) == ' '.join(query_esperada.split())


def test_aplicar_filtros(pantalla_movimientos):
    """
    Prueba la l�gica de filtrado de datos seg�n el texto de b�squeda.
    """
    pantalla_movimientos.datos = DATOS_MOCK
    pantalla_movimientos._actualizar_tabla = MagicMock()

    # Probamos con un filtro que no tenga acento.
    pantalla_movimientos.entrada_busqueda.insert(0, "mouse")
    pantalla_movimientos._aplicar_filtros()
    
    args, _ = pantalla_movimientos._actualizar_tabla.call_args
    datos_filtrados = args[0]
    
    assert len(datos_filtrados) == 1
    assert datos_filtrados[0][4] == "Mouse Inalambrico"

def test_ordenar_por_columna(pantalla_movimientos):
    """
    Verifica que las propiedades de ordenaci�n cambian correctamente al llamar al m�todo.
    """
    with patch.object(pantalla_movimientos, '_cargar_datos') as mock_cargar, \
         patch.object(pantalla_movimientos, '_aplicar_filtros') as mock_filtrar:

        pantalla_movimientos._ordenar_por_columna('producto')
        assert pantalla_movimientos.sort_column == 'p.nombre'
        assert pantalla_movimientos.sort_ascending is True

        pantalla_movimientos._ordenar_por_columna('producto')
        assert pantalla_movimientos.sort_ascending is False

        pantalla_movimientos._ordenar_por_columna('fecha')
        assert pantalla_movimientos.sort_column == 'm.fecha'
        assert pantalla_movimientos.sort_ascending is True

        assert mock_cargar.call_count == 3
        assert mock_filtrar.call_count == 3

def test_formato_cantidad_en_actualizar_tabla(pantalla_movimientos):
    """
    Verifica que la cantidad se formatea con un signo '+' para valores positivos.
    """
    pantalla_movimientos.tabla.insert = MagicMock()
    pantalla_movimientos._actualizar_tabla(DATOS_MOCK)

    llamadas = pantalla_movimientos.tabla.insert.call_args_list
    valores_pasados = [c.kwargs['values'] for c in llamadas]
    
    assert valores_pasados[0][3] == "+10"
    assert valores_pasados[1][3] == "-5"
    assert valores_pasados[2][3] == "+20"   