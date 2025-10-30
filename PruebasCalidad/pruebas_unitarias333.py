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


@patch('ui.clientes.obtener_datos')
@patch('ui.clientes.ejecutar_query')
@patch('ui.clientes.messagebox')
def test_cambiar_estado_cliente_cuando_no_se_encuentra_en_db(mock_messagebox, mock_ejecutar_query, mock_obtener_datos, pantalla_clientes):
    """
    PRUEBA 2: Verifica el manejo de errores si un cliente no se encuentra en la BD.
    Esta prueba ahora pasa exitosamente tras corregir el KeyError.
    """
    # 1. Configuración (Arrange)
    cliente_id_fantasma = "999"
    pantalla_clientes.tabla.focus.return_value = 'I001'

    # ### CORRECCIÓN CLAVE ###
    # La causa del error 'KeyError: 0' era que el mock devolvía un diccionario.
    # El código real `self.tabla.item(..., "values")[0]` espera una tupla o lista.
    # Corregimos el mock para que devuelva una tupla, simulando el comportamiento real.
    pantalla_clientes.tabla.item.return_value = (cliente_id_fantasma, 'Nombre Falso', 'Tipo Falso')

    # La DB devuelve una lista vacía, indicando que no encontró al cliente.
    mock_obtener_datos.return_value = []

    # También es necesario añadir esta línea para que el flujo continúe
    #mock_messagebox.askyesno.return_value = True

    # 2. Acción (Act)
    # Ahora esta llamada no lanzará un KeyError.
    pantalla_clientes._cambiar_estado_cliente()

    # 3. Verificación (Assert)
    # Las verificaciones siguen siendo las mismas y ahora se alcanzarán correctamente.
    mock_obtener_datos.assert_called_once_with(
        "SELECT estado FROM Clientes WHERE id_cliente = ?",
        (cliente_id_fantasma,)
    )
    mock_messagebox.showerror.assert_called_once_with("Error", "Cliente no encontrado")
    mock_ejecutar_query.assert_not_called()