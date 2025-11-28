import unittest
import subprocess
import sys
import os
import time
import pyautogui

class TestVentaScript(unittest.TestCase):
    process = None

    @classmethod
    def setUpClass(cls):
        cls.current_dir = os.path.dirname(os.path.abspath(__file__))
        cls.project_root = os.path.dirname(cls.current_dir)
        cls.main_script = os.path.join(cls.project_root, "main.py")
        
        # Configuración "Script Rápido"
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.4  # Pausa breve entre comandos para estabilidad

    def setUp(self):
        print("\n⚡ EJECUTANDO PRUEBA DE VENTA (MODO SCRIPT)...")
        self.process = subprocess.Popen(
            [sys.executable, self.main_script],
            cwd=self.project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(3) # Esperar carga del Login

    def tearDown(self):
        if self.process:
            self.process.terminate()

    def get_pos(self, rel_x, rel_y):
        """Calcula la coordenada absoluta basada en la ventana centrada (1200x800)"""
        w, h = pyautogui.size()
        x_origen = (w - 1200) // 2
        y_origen = (h - 800) // 2
        return x_origen + rel_x, y_origen + rel_y

    def test_flujo_teclado_clicks(self):
        try:
            # 1. LOGIN (Puro Teclado)
            print("1. Login...")
            pyautogui.write('admin')
            pyautogui.press('tab')
            pyautogui.write('1234')
            pyautogui.press('enter')
            
            time.sleep(2) # Esperar Dashboard

            # 2. ENTRAR A VENTAS (Clic Instantáneo)
            print("2. Accediendo a POS...")
            # Coordenada del botón verde
            x, y = self.get_pos(400, 350)
            pyautogui.click(x, y) 
            time.sleep(1)

            # 3. BUSCAR PRODUCTO (Clic + Teclado)
            print("3. Buscando 'mouse'...")
            # Clic en caja de búsqueda
            x, y = self.get_pos(250, 160)
            pyautogui.click(x, y)
            pyautogui.write('mouse')
            time.sleep(0.5)

            # 4. SELECCIONAR PRODUCTO (Doble Clic Instantáneo)
            print("4. Seleccionando...")
            # Clic en el primer resultado de la lista
            x, y = self.get_pos(300, 280)
            pyautogui.doubleClick(x, y)
            time.sleep(0.5)

            # 5. CANTIDAD (Teclado)
            print("5. Cantidad...")
            # El popup tiene el foco automático
            pyautogui.write('5')
            pyautogui.press('enter')
            time.sleep(0.5)

            # 6. CLIENTE (Clic Instantáneo + Teclado)
            print("6. Cliente...")
            # Clic en combo clientes
            x, y = self.get_pos(950, 180)
            pyautogui.click(x, y)
            pyautogui.press('down')
            pyautogui.press('enter')

            # 7. PAGO (Clic Instantáneo + Teclado)
            print("7. Medio de Pago...")
            # Clic en combo pagos
            x, y = self.get_pos(950, 600)
            pyautogui.click(x, y)
            pyautogui.press('down')
            pyautogui.press('enter')

            # 8. PAGAR (Clic Instantáneo)
            print("8. Pagando...")
            # Clic en botón gigante
            x, y = self.get_pos(950, 750)
            pyautogui.click(x, y)

            # 9. FINALIZAR
            print("9. Validando...")
            time.sleep(3) # Esperar PDF
            
            # Cerrar mensaje de éxito con teclado
            pyautogui.press('right') # Mover a "No"
            pyautogui.press('enter')

            print("\n✅ PRUEBA EXITOSA: Flujo completado sin navegación visual.")

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            self.fail("La prueba falló.")

if __name__ == "__main__":
    unittest.main()

    