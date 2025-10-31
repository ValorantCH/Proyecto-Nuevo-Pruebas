# test_sistema_navegacion_inventario.py
import pyautogui
import time
import subprocess

# Desactivar el Failsafe de PyAutoGUI si es necesario (mover el ratón a una esquina para parar)
# pyautogui.FAILSAFE = False

def buscar_y_clicar_imagen(ruta_imagen, descripcion, timeout=10):
    """
    Función auxiliar que busca una imagen en la pantalla durante un tiempo determinado
    y hace clic en ella. Termina el script si no la encuentra.
    """
    print(f"Buscando '{descripcion}' en '{ruta_imagen}'...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # confidence=0.9 ayuda a encontrar imágenes aunque tengan pequeñas variaciones
            coordenadas = pyautogui.locateCenterOnScreen(ruta_imagen, confidence=0.9)
            
            if coordenadas:
                pyautogui.click(coordenadas)
                print(f"'{descripcion}' encontrado y pulsado en {coordenadas}.")
                return True
        except pyautogui.ImageNotFoundException:
            # Esto es normal, la imagen puede no estar disponible de inmediato
            time.sleep(0.5)
            continue
            
    print(f"ERROR: No se pudo encontrar '{descripcion}' después de {timeout} segundos.")
    return False

def verificar_existencia_imagen(ruta_imagen, descripcion, timeout=10):
    """
    Función auxiliar que solo verifica si una imagen aparece en la pantalla.
    """
    print(f"Verificando la existencia de '{descripcion}'...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        if pyautogui.locateOnScreen(ruta_imagen, confidence=0.9):
            print(f"'{descripcion}' encontrado en la pantalla.")
            return True
        time.sleep(0.5)
        
    print(f"ERROR: No se pudo verificar la existencia de '{descripcion}' después de {timeout} segundos.")
    return False

# --- INICIO DEL SCRIPT DE PRUEBA ---

# Nombre del archivo principal de tu aplicación
APP_MAIN_FILE = "main.py" 

app_process = None
try:
    # 1. Lanzar la aplicación en un proceso separado
    print(f"Lanzando la aplicación desde '{APP_MAIN_FILE}'...")
    app_process = subprocess.Popen(['python', APP_MAIN_FILE])
    
    # Esperar un momento para que la ventana principal se cargue
    time.sleep(5) 

    # 2. Navegar a la pantalla de inventario
    if not buscar_y_clicar_imagen('capturas_test/boton_inventario.png', 'Botón de Navegación a Inventario'):
        raise Exception("Fallo al navegar a la pantalla de inventario.")
    
    # Esperar a que la pantalla de inventario cargue sus componentes
    time.sleep(2)

    # 3. Hacer clic en el botón "Nuevo Producto"
    if not buscar_y_clicar_imagen('capturas_test/boton_nuevo_producto.png', 'Botón de Nuevo Producto'):
        raise Exception("Fallo al hacer clic en 'Nuevo Producto'.")

    # 4. Verificar que el diálogo de producto se ha abierto
    if verificar_existencia_imagen('capturas_test/titulo_dialogo_producto.png', 'Título del Diálogo de Producto'):
        print("\n--- PRUEBA PASA: El diálogo de nuevo producto se abrió correctamente. ---")
    else:
        raise Exception("La verificación del diálogo de producto falló.")

except Exception as e:
    print(f"\n--- PRUEBA FALLA: {e} ---")

finally:
    # 5. Asegurarse de cerrar la aplicación al final, sin importar si la prueba pasó o falló
    if app_process:
        print("Cerrando la aplicación...")
        app_process.terminate()