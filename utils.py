import time
import os
import random
import string
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
import tempfile
import psutil

def kill_edge_processes():
    """
    Verifica si el proceso msedge.exe (Microsoft Edge) está en ejecución.
    Si está corriendo, lo termina.
    """
    edge_process_name = "msedge.exe"
    edge_processes = []
    
    # Buscar todos los procesos activos
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            # Si el proceso es msedge.exe, lo agrega a la lista
            if proc.info['name'] == edge_process_name:
                edge_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    if edge_processes:
        print(f"Se encontraron {len(edge_processes)} procesos de Microsoft Edge. Finalizando procesos...")
        for proc in edge_processes:
            try:
                proc.terminate()  # Intentar finalizar el proceso de forma educada
                proc.wait(timeout=3)  # Esperar hasta 3 segundos para que termine
                print(f"Proceso {proc.pid} ({proc.name()}) finalizado.")
            except (psutil.NoSuchProcess, psutil.TimeoutExpired, psutil.AccessDenied) as e:
                print(f"No se pudo finalizar el proceso {proc.pid}: {e}")
    else:
        print("No se encontraron procesos de Microsoft Edge en ejecución.")

def generate_random_folder_name(length=8):
    """Genera un nombre aleatorio para la carpeta."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def capture_screenshots_with_cookies(edge_driver_path, edge_user_data_dir, edge_profile_directory, urls):
    """
    Abre cada URL en Microsoft Edge utilizando el perfil de usuario para cargar las cookies.
    Toma capturas de pantalla de las URLs después de iniciar sesión automáticamente mediante las cookies.

    :param edge_driver_path: Ruta al archivo ejecutable de EdgeDriver.
    :param edge_user_data_dir: Ruta al directorio de datos del usuario de Edge.
    :param edge_profile_directory: Nombre del directorio del perfil de usuario en Edge.
    :param urls: Lista de URLs para abrir y capturar.
    """
    # Directorio temporal para almacenar las capturas de pantalla
    temp_dir = os.path.join(tempfile.gettempdir(), generate_random_folder_name())
    os.makedirs(temp_dir, exist_ok=True)

    edge_options = Options()
    edge_options.add_argument(f'user-data-dir={edge_user_data_dir}')
    edge_options.add_argument(f'profile-directory={edge_profile_directory}')
    edge_options.add_argument('--headless')  # Ejecutar en modo headless (sin interfaz gráfica)

    service = Service(executable_path=edge_driver_path)

    try:
        driver = webdriver.Edge(service=service, options=edge_options)
    except Exception as e:
        print(f"Error al iniciar EdgeDriver: {e}")
        return

    for url in urls:
        driver.get(url)
        print(f"Abriendo {url} con sesión existente")
        time.sleep(10)  # Esperar para que la página cargue completamente


        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_filename = f"screenshot_{timestamp}.png"
        screenshot_path = os.path.join(temp_dir, screenshot_filename)

        driver.save_screenshot(screenshot_path)
        print(f"Captura de pantalla guardada en: {screenshot_path}")

        time.sleep(2)

    driver.quit()
    return temp_dir

