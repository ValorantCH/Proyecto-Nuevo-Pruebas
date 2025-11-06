import pyautogui
import time
import subprocess
import random

# ==============================================================================
# --- CONFIGURACIÓN DE LA PRUEBA ---
# ==============================================================================

# El archivo principal que inicia tu aplicación
APP_MAIN_FILE = "main.py" 

# El título exacto de la ventana de tu aplicación
WINDOW_TITLE = "Gestor de Ventas"

# Cuántos clics aleatorios se realizarán
NUMBER_OF_CLICKS = 30

# El tiempo de espera (en un rango aleatorio) entre cada clic
DELAY_BETWEEN_CLICKS = (0.1, 0.2) # Espera entre 0.5 y 1.5 segundos

# --- RESTRICCIÓN DEL ÁREA DE CLICS (PADDING EN PÍXELES) ---
# Define un margen interno para evitar clics en los bordes o en el encabezado.
# Para permitir clics en TODA la ventana, pon todos los valores a 0.
CLICK_AREA_PADDING = {
    "top": 100,   # No hacer clic en los primeros 100 píxeles (para evitar el header)
    "bottom": 400, # No hacer clic en los últimos 20 píxeles (barra de estado, etc.)
    "left": 20,
    "right": 20
}

# ==============================================================================

# ¡CUIDADO! Este script tomará el control de tu ratón.
# Para detenerlo de emergencia, mueve el ratón rápidamente a una de las
# esquinas de la pantalla. Esta es una función de seguridad de PyAutoGUI.

app_process = None
try:
    # 1. Lanzar la aplicación en un proceso separado
    print(f"Lanzando la aplicación desde '{APP_MAIN_FILE}'...")
    app_process = subprocess.Popen(['python', APP_MAIN_FILE])
    
    # 2. Esperar y encontrar la ventana
    print(f"Buscando la ventana con el título: '{WINDOW_TITLE}'...")
    app_window = None
    timeout = 15 # Esperar hasta 15 segundos para que aparezca la ventana
    start_time = time.time()
    while time.time() - start_time < timeout:
        # getWindowsWithTitle devuelve una lista, tomamos el primer resultado
        windows = pyautogui.getWindowsWithTitle(WINDOW_TITLE)
        if windows:
            app_window = windows[0]
            print("¡Ventana encontrada!")
            break
        time.sleep(0.5)

    if not app_window:
        raise Exception(f"No se pudo encontrar la ventana '{WINDOW_TITLE}' después de {timeout} segundos.")

    # Traer la ventana al frente para asegurarse de que es visible
    app_window.activate()
    time.sleep(1) # Pequeña pausa para que la ventana se active completamente

    # 3. Calcular el área de clic restringida
    # Obtenemos las dimensiones de la ventana encontrada
    win_left, win_top, win_width, win_height = app_window.left, app_window.top, app_window.width, app_window.height
    
    # Aplicamos el padding para definir los límites de los clics
    min_x = win_left + CLICK_AREA_PADDING["left"]
    max_x = win_left + win_width - CLICK_AREA_PADDING["right"]
    min_y = win_top + CLICK_AREA_PADDING["top"]
    max_y = win_top + win_height - CLICK_AREA_PADDING["bottom"]

    # Comprobación de seguridad: asegurarse de que el área sea válida
    if min_x >= max_x or min_y >= max_y:
        raise ValueError("El padding es demasiado grande y no deja área para hacer clic.")

    print(f"Ventana encontrada en: (L:{win_left}, T:{win_top}, W:{win_width}, H:{win_height})")
    print(f"Área de clic restringida a: X({min_x} a {max_x}), Y({min_y} a {max_y})")
    print("\nIniciando clics aleatorios en 3 segundos...")
    time.sleep(3)

    # 4. Bucle de clics aleatorios
    for i in range(NUMBER_OF_CLICKS):
        # Generar coordenadas aleatorias dentro del área restringida
        rand_x = random.randint(min_x, max_x)
        rand_y = random.randint(min_y, max_y)

        # Mover y hacer clic
        pyautogui.moveTo(rand_x, rand_y, duration=0.25) # Mover suavemente
        pyautogui.click()

        print(f"Clic #{i + 1}/{NUMBER_OF_CLICKS} en la posición: ({rand_x}, {rand_y})")
        
        # Esperar un tiempo aleatorio antes del siguiente clic
        time.sleep(random.uniform(DELAY_BETWEEN_CLICKS[0], DELAY_BETWEEN_CLICKS[1]))

    print("\n--- PRUEBA DE CLICS ALEATORIOS COMPLETADA EXITOSAMENTE ---")

except Exception as e:
    print(f"\n--- LA PRUEBA FALLÓ: {e} ---")

finally:
    # 5. Asegurarse de cerrar la aplicación al final
    if app_process:
        print("Cerrando la aplicación...")
        app_process.terminate()