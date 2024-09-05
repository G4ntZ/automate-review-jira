import xmltodict
import configparser
import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException
import re
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

def load_config(config_file='config.ini'):
    """Carga la configuración desde un archivo INI."""
    config = configparser.ConfigParser()
    config.read(config_file)
    
    jira_url = config.get('jira', 'url')
    jira_token = config.get('jira', 'token')
    jira_email = config.get('jira', 'email')
    bitbucket_token = config.get('bitbucket', 'token')
    bamboo_user = config.get('bamboo', 'user')
    bamboo_password = config.get('bamboo', 'password')
    edge_driver_path = config.get('edge', 'edge_driver_path')
    edge_user_data_dir = config.get('edge', 'edge_user_data_dir')
    edge_profile_directory = config.get('edge', 'edge_profile_directory')


    return jira_url, jira_token, jira_email, bitbucket_token, bamboo_user, bamboo_password, edge_driver_path, edge_user_data_dir, edge_profile_directory

def xml_to_json(xml_data):
    try:
        # Convertir XML a un diccionario de Python
        dict_data = xmltodict.parse(xml_data)
        
        return dict_data
    except Exception as e:
        return f'Error: {e}'
    
def get_sonar_urls(results_plan, bamboo_user, bamboo_password):
    sonar_base_url="http://sonar.afphabitat.net:9000/dashboard"
    sonar_urls = []
    for result in results_plan:
        descript = result.split('-')
        codi = f'{descript[0]}-{descript[1]}'
        num = f'{descript[2]}'
        url = f'http://bamboo.afphabitat.net:8085/download/{codi}-SON/build_logs/{codi}-SON-{num}.log'
        try:
            response = requests.get(url, auth=HTTPBasicAuth(bamboo_user, bamboo_password))
            if response.status_code == 200:
                # Buscar las URLs que comienzan con la base de Sonar
                sonar_urls_in_log = re.findall(rf"{re.escape(sonar_base_url)}\S+", response.text)
                
                # Agregar las URLs encontradas a la lista general
                sonar_urls.extend(sonar_urls_in_log)
            else:
                print(f"No se encontro job sonar para el resultado {url} correspondiente a la ejecion {result}")
        except RequestException as e:
            print(f"Excepción durante la solicitud HTTP para {url}: {e}")
    return sonar_urls


jira_url, jira_token, jira_email, bitbucket_token, bamboo_user, bamboo_password, edge_driver_path, edge_user_data_dir, edge_profile_directory = load_config()
results_plan = ["SBPP-PADNBQA1-11",
"SBPP-POPANBQA0-9",
"SBPP-PENACNBQA1-27",
"SBPP-PCCNBQA1-20",
"SBPP-PMLNBQA1-7",
"SBPP-PMACNBQA0-13",
"SBPP-PAINBQA1-11",
"SBPP-PALNBQA1-7",
"SBPP-PCRNBQA1-13"]


sonar_urls = get_sonar_urls(results_plan, bamboo_user, bamboo_password)
capture_screenshots_with_cookies(edge_driver_path, edge_user_data_dir, edge_profile_directory, sonar_urls)