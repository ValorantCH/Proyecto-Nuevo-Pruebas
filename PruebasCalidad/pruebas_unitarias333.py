import sys
import os
import pytest
import tkinter as tk
from unittest.mock import patch, MagicMock

# --- Configuración del entorno ---
# Se asegura de que Python pueda encontrar el módulo 'ui.clientes'.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from ui.clientes import PantallaClientes

# --- Fixture de Pytest ---
@pytest.fixture
def pantalla_clientes():
    """
    Crea una instancia limpia de PantallaClientes para cada prueba.
    Simula (_mocks_) la inicialización completa de la UI y la carga de datos.
    """
    # Usamos la ruta correcta 'ui.clientes' para que patch encuentre los métodos a simular.
    with patch('ui.clientes.PantallaClientes._inicializar_ui'), \
         patch('ui.clientes.PantallaClientes._cargar_datos'):
        root = tk.Tk()
        root.withdraw()
        app = PantallaClientes(root)
        app.tabla = MagicMock()
        app.btn_estado = MagicMock()
        yield app
    root.destroy()

# --- Casos de Prueba ---

def test_actualizar_boton_estado_segun_seleccion_en_tabla(pantalla_clientes):
    """
    PRUEBA 1: Verifica la lógica de la UI para habilitar/deshabilitar el botón de estado.
    Esta prueba ahora pasa exitosamente.
    """
    # Escenario 1: No hay ningún ítem seleccionado.
    pantalla_clientes.tabla.focus.return_value = ''
    pantalla_clientes._actualizar_boton_estado()
    pantalla_clientes.btn_estado.config.assert_called_once_with(state="disabled")

    pantalla_clientes.btn_estado.config.reset_mock()

    # Escenario 2: Un ítem es seleccionado.
    pantalla_clientes.tabla.focus.return_value = 'I001'

    # ### CORRECCIÓN ###
    # El método .item(..., "values") devuelve una TUPLA, no un diccionario.
    # Se ajusta el mock para que devuelva una tupla de valores simulados.
    pantalla_clientes.tabla.item.return_value = ('10', 'Ana', 'Física', 'Calle Falsa 123')

    pantalla_clientes._actualizar_boton_estado()

    # La lógica del método _actualizar_boton_estado solo verifica si "valores" no es vacío,
    # por lo que ahora funciona correctamente y habilita el botón.
    pantalla_clientes.btn_estado.config.assert_called_once_with(state="normal")