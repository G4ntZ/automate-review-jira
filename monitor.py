import requests
import time
import threading
import xmltodict
import requests
import time
import threading
from requests.auth import HTTPBasicAuth

class BambooBuildMonitor:
    def __init__(self, api_urls, bamboo_user, bamboo_passowrd,  check_interval=10):
        """
        Inicializa el monitor de construcción de Bamboo para una lista de URLs.
        
        :param api_urls: Lista de URLs de la API de Bamboo para monitorear.
        :param check_interval: Intervalo de tiempo en segundos entre cada consulta.
        """
        self.bamboo_user = bamboo_user
        self.bamboo_password = bamboo_passowrd
        self.api_urls = api_urls
        self.check_interval = check_interval
        self.build_states = {url: None for url in api_urls}
        self.monitor_threads = []

    def _check_build_state(self, api_url):
        """
        Realiza la consulta a la API de Bamboo y actualiza el estado de la construcción.
        
        :param api_url: URL específica del plan de Bamboo.
        """
        try:
            response = requests.get(api_url, auth=HTTPBasicAuth(self.bamboo_user, self.bamboo_password))
            response.raise_for_status()
            build_info = xmltodict.parse(response.content)
            build_state = build_info['result']['buildState']
            self.build_states[api_url] = build_state
            print(f"Estado actual del build en {api_url}: {build_state}")
        except requests.exceptions.RequestException as e:
            print(f"Error al consultar la API para {api_url}: {e}")
            self.build_states[api_url] = "Error"

    def _monitor_build(self, api_url):
        """
        Monitorea el estado de la construcción hasta que sea 'Failed' o 'Successful'.
        
        :param api_url: URL específica del plan de Bamboo.
        """
        while self.build_states[api_url] not in ['Failed', 'Successful', 'Error']:
            self._check_build_state(api_url)
            if self.build_states[api_url] not in ['Failed', 'Successful', 'Error']:
                time.sleep(self.check_interval)

    def start_monitoring(self):
        """
        Inicia la monitorización de todos los builds en hilos separados.
        """
        for api_url in self.api_urls:
            monitor_thread = threading.Thread(target=self._monitor_build, args=(api_url,))
            self.monitor_threads.append(monitor_thread)
            monitor_thread.start()
            print(f"Monitoreo iniciado para {api_url} en hilo {monitor_thread.name}")

    def wait_for_completion(self):
        """
        Espera a que todos los hilos de monitorización terminen.
        """
        for monitor_thread in self.monitor_threads:
            monitor_thread.join()

        
        return self.build_states
