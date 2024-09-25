import requests
from requests.auth import HTTPBasicAuth
import json
import configparser
import re
import sys
import xml.etree.ElementTree as ET
from monitor import BambooBuildMonitor
from requests.exceptions import RequestException
from utils import capture_screenshots_with_cookies
from utils import kill_edge_processes
from upload_file import upload_files_to_jira

# Consulta JQL
URL_PATTERN_BITBUCKET = r'https://bitbucket\.org/[^\s"\'{}]+'
URL_PATTERN_BAMBOO = r'http://bamboo\.afphabitat\.net:8085/[^\s"\'{}]+'

JQL_QUERY = 'status in ("Por Hacer QAT","Por Hacer QAT PROD","Por Revisar QAT") ' \
            'and project not in ("Proyecto para Pruebas y Capacitacion")'

JQL_QUERY = 'issue in('+ sys.argv[1] +')'


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


def search_issues(jira_url, jira_token, jira_email):
    """Realiza la consulta JQL y devuelve una lista de issues."""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    params = {
        "jql": JQL_QUERY,
        "maxResults": 100  # Limita el número de resultados por petición
    }

    try:
        response = requests.get(
            f"{jira_url}/search",
            headers=headers,
            params=params,
            auth=HTTPBasicAuth(jira_email, jira_token)
        )

        response.raise_for_status()

        return response.json().get('issues', [])

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")
    
    return []

def transition_issue(issue_key, jira_url, jira_token, jira_email):
    """Cambia el estado de un issue utilizando la transición especificada."""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    def attempt_transition(transition_id):
        data = {
            "transition": {
                "id": transition_id
            }
        }
        try:
            response = requests.post(
                f"{jira_url}/issue/{issue_key}/transitions",
                headers=headers,
                data=json.dumps(data),
                auth=HTTPBasicAuth(jira_email, jira_token)
            )

            response.raise_for_status()
            print(f"Issue {issue_key} transitioned successfully with ID {transition_id}.")
            return True  # Transición exitosa

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred with ID {transition_id}: {http_err}")
            return False  # Intento fallido
    
    # Intentar con la primera ID
    if not attempt_transition("91"):
        # Si falla, intentar con la segunda ID
        attempt_transition("641")


# Función para limpiar y eliminar URLs duplicadas
def clean_and_remove_duplicates(urls, url_pattern):
    # Expresión regular para encontrar URLs válidas
    
    seen_urls = set()
    cleaned_urls = []

    for url in urls:
        # Buscar y limpiar la URL
        match = re.search(url_pattern, url)

        if match:
            url = match.group()
            # Añadir a la lista solo si no está ya en el conjunto de URLs vistas
            if url not in seen_urls:
                seen_urls.add(url)
                cleaned_urls.append(url)
    
    return cleaned_urls

def transform_pr_to_api(list_url):
    new_list = []
    for api_url in list_url:
        url = api_url.split('/')
        url_api = f'https://api.bitbucket.org/2.0/repositories/{url[3]}/{url[4]}/pullrequests/{url[6]}'
        new_list.append(url_api)
    return new_list

def get_url_plan_bamboo(issue_key, jira_url, jira_token, jira_email):
    """Lista todos las url de los planes bamboo para analisar y automatizar la revision de una pauta."""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(
            f"{jira_url}/issue/{issue_key}",
            headers=headers,
            auth=HTTPBasicAuth(jira_email, jira_token)
        )
        response.raise_for_status()
        json_data = response.json().get('fields', {}).get('customfield_10084')
        texts = []
        def extract_text(content):
            """Función recursiva para extraer texto de la estructura JSON"""
            if isinstance(content, dict):
                if content.get('type') == 'text':
                    texts.append(content.get('text', ''))
                for value in content.values():
                    extract_text(value)
            elif isinstance(content, list):
                for item in content:
                    extract_text(item)
        
        extract_text(json_data)
        json_text = ' '.join(texts)
        json_text = json_text.replace('\n', ' ')
        json_text = json_text.replace('\r', ' ')
        json_text = ' '.join(json_text.split())  # Limpia espacios redundantes

        #print(json_text)
        # Buscar todas las URLs en el texto
        urls = re.findall(URL_PATTERN_BAMBOO, json_text)
        cleaned_urls = clean_and_remove_duplicates(urls, URL_PATTERN_BAMBOO)
        # Imprimir URLs limpias y únicas
        for url in cleaned_urls:
            print(url)

        return cleaned_urls
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")

def get_pull_request_paths(issue_key, jira_url, jira_token, jira_email):
    """Lista todos los pull request para analisar y automatizar la revision de una pauta."""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(
            f"{jira_url}/issue/{issue_key}",
            headers=headers,
            auth=HTTPBasicAuth(jira_email, jira_token)
        )
        response.raise_for_status()
        json_data = response.json().get('fields', {}).get('customfield_10064')
        json_text = json.dumps(json_data)

        urls = re.findall(URL_PATTERN_BITBUCKET, json_text)
        cleaned_urls = clean_and_remove_duplicates(urls, URL_PATTERN_BITBUCKET)
        # Imprimir URLs limpias y únicas
        for url in cleaned_urls:
            print(url)

        return cleaned_urls
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")


def list_subtasks(issue_key, jira_url, jira_token, jira_email):
    """Lista todas las subtareas asociadas a un issue principal."""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(
            f"{jira_url}/issue/{issue_key}",
            headers=headers,
            auth=HTTPBasicAuth(jira_email, jira_token)
        )

        response.raise_for_status()

        # Obtener las subtareas
        subtasks = response.json().get('fields', {}).get('subtasks', [])

        matching_subtasks = []

        if subtasks:
            print(f"Se encontraron {len(subtasks)} subtareas para el issue {issue_key}:")
            for subtask in subtasks:
                key = subtask.get('key')
                summary = subtask.get('fields', {}).get('summary')
                status_id = subtask.get('fields', {}).get('status', {}).get('id')

                if status_id == "10047":
                    paths = subtask.get('fields', {}).get('status', {}).get('name')
                    print(f"-A procesar {key}: {summary} {status_name}")
                    matching_subtasks.append(key)
        else:
            print(f"No se encontraron subtareas para el issue {issue_key}.")
        
        return matching_subtasks

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")

        return []

def clasificar_componente(component):
    """
    Clasifica un componente basado en la URL del pull request.
    """
    # Extraer la parte relevante de la URL
    try:
        # Clasificación basada en palabras clave
        
        if any(keyword in component for keyword in ['config', 'properties', 'customizationfile']):
            return 'config'
        elif 'back' in component:
            return 'back'
        elif any(keyword in component for keyword in ['front', 'afph-paet-auth']):
            return 'front'
        else:
            return 'back'  # O un tipo por defecto si no coincide con ninguna clasificación
    except IndexError:
        return 'invalid'  # Manejar el caso donde la URL no tenga la estructura esperada
    except Exception as e:
        print(f"Error inesperado: {e}")
        return 'error'  # Manejar otros errores inesperados

def get_info_pull_requests(url_pull_requests, bitbucket_token):
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {bitbucket_token}"
    }
    
    results = []
    
    for url_pull_request in url_pull_requests:
        try:
            response = requests.get(url_pull_request, headers=headers)
            response.raise_for_status()  # Lanza un error para códigos de estado HTTP 4xx/5xx
            
            # Intenta obtener el JSON
            try:
                
                component = url_pull_request.split('/')[6]
                tipo = clasificar_componente(component)
                pr_info = response.json()
                source_branch = pr_info['source']['branch']['name']
                state = pr_info['state']
                results.append({
                    'url_pull_request': url_pull_request,
                    'source_branch': source_branch,
                    'state': state,
                    'tipo': tipo,
                    'component': component
                })
            except requests.exceptions.JSONDecodeError:
                results.append({
                    'url_pull_request': url_pull_request,
                    'error': 'Error al decodificar la respuesta JSON.'
                })
        
        except requests.exceptions.HTTPError as http_err:
            results.append({
                'url_pull_request': url_pull_request,
                'error': f'Error HTTP: {http_err}'
            })
        except requests.exceptions.RequestException as req_err:
            results.append({
                'url_pull_request': url_pull_request,
                'error': f'Error en la solicitud: {req_err}'
            })
    
    return results

def get_url_bamboo_rama_origen(plan_key, branch_name):
    #http://bamboo.afphabitat.net:8085/browse/WL12CRT-OSDQA

    url = f"http://bamboo.afphabitat.net:8085/rest/api/latest/plan/{plan_key}/branch"
    
    # Hacemos la solicitud HTTP GET
    response = requests.get(url)
    
    if response.status_code != 200:
        raise Exception(f"Error al obtener los datos de Bamboo: {response.status_code}")
    
    # Parseamos el XML de la respuesta
    root = ET.fromstring(response.content)
    
    # Iteramos sobre los elementos <branch> para encontrar el que coincide con el shortName
    for branch in root.findall(".//branch"):
        short_name = branch.get('shortName')
        if short_name == branch_name:
            # Obtenemos el valor del atributo href dentro del elemento <link>
            link_element = branch.find(".//link[@rel='self']")
            if link_element is not None:
                return link_element.get('href')
    
    return None



def extraer_short_name(plan_key, bamboo_user, bamboo_password):
    """
    Extrae el shortName de un plan Bamboo a partir de datos XML.
    """
    try:
        response = requests.get(
            f"http://bamboo.afphabitat.net:8085/rest/api/latest/plan/{plan_key}",
            auth=HTTPBasicAuth(bamboo_user, bamboo_password)
            )
        response.raise_for_status()

        response_text = response.text

        try:
            # Parsear el XML desde la cadena
            root = ET.fromstring(response_text)
            
            # Extraer el atributo shortName del elemento <plan>
            short_name = root.attrib.get('shortName')
            short_name = short_name.split(' ')[0]

            # Verificar si shortName está presente
            if short_name:
                return short_name
            else:
                return 'shortName no encontrado'
        
        except ET.ParseError as parse_err:
            print(f"Error al parsear el XML: {parse_err}")
            return 'error en el XML'
        except Exception as err:
            print(f"Error inesperado: {err}")
            return 'error inesperado'

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")

def obtener_url_rama_bamboo(plan_key, branch_name, bamboo_user, bamboo_password):
    url = f"http://bamboo.afphabitat.net:8085/rest/api/latest/plan/{plan_key}/branch"
    
    # Hacemos la solicitud HTTP GET
    response = requests.get(url, auth=HTTPBasicAuth(bamboo_user, bamboo_password))
    
    if response.status_code != 200:
        raise Exception(f"Error al obtener los datos de Bamboo: {response.status_code}")
    
    # Parseamos el XML de la respuesta
    root = ET.fromstring(response.content)
    
    # Iteramos sobre los elementos <branch> para encontrar el que coincide con el shortName
    for branch in root.findall(".//branch"):
        short_name = branch.get('shortName')
        #print(f'{short_name} {branch_name}')
        if short_name == branch_name.replace('/','-'):
            branch_key = branch.get('key')
            if branch_key is not None:
                return branch_key
            # Obtenemos el valor del atributo href dentro del elemento <link>
            #link_element = branch.find(".//link[@rel='self']")
            #if link_element is not None:
            #    return link_element.get('href')
    
    return None  

def ejecutar_plan_bamboo(plan_key, branch_name, bamboo_user, bamboo_password):
    #http://bamboo.afphabitat.net:8085/rest/api/latest/queue/WL12CRT-WSDQA0?executeAllStages=true&bamboo.branch=bugfix-migracion-2.0.0
    url = f"http://bamboo.afphabitat.net:8085/rest/api/latest/queue/{plan_key}?executeAllStages=true&bamboo.branch={branch_name.replace('/','-')}"
    
    # Hacemos la solicitud HTTP GET
    response = requests.post(url, auth=HTTPBasicAuth(bamboo_user, bamboo_password))
    
    if response.status_code != 200:
        raise Exception(f"Error al obtener los datos de Bamboo: {response.status_code}")
    
    try:
        # Parsear el XML
        root = ET.fromstring(response.content)
        
        # Buscar el elemento 'link'
        link_element = root.find('link')
        
        # Verificar si el elemento 'link' existe y tiene el atributo 'href'
        if link_element is not None and 'href' in link_element.attrib:
            return link_element.attrib['href']
        else:
            return 'Error: No se encontró el atributo href en el elemento link.'
    
    except ET.ParseError:
        return 'Error: El XML no es válido.'

def main():
    """Función principal para buscar issues y cambiar el estado del primero encontrado."""
    jira_url, jira_token, jira_email, bitbucket_app_password, bitbucket_token, bamboo_user, bamboo_password = load_config()
    
    issues = search_issues(jira_url, jira_token, jira_email)

    if issues:
        print(f"Se encontraron {len(issues)} issues:")
        for issue in issues:
            key = issue.get('key')
            summary = issue.get('fields', {}).get('summary')
            print(f"- {key}: {summary}")
        
        # Cambiar el estado del primer issue encontrado
        first_issue_key = issues[0].get('key')
        transition_issue(first_issue_key, jira_url, jira_token, jira_email)  
        list_subtasks_por_hacer = list_subtasks(first_issue_key, jira_url, jira_token, jira_email)
        
    else:
        print("No se encontraron issues que coincidan con la consulta JQL.")

def print_build_states(build_states):
    print("Monitoreo finalizado. Estados finales:")
    for url, state in build_states.items():
        print(f"{url}: {state}")

def print_bamboo_url_states(build_states):
    print("URL bamboo de estados finales:")
    for url, state in build_states.items():
        n_url = url.split('/')
        print(f"http://bamboo.afphabitat.net:8085/browse/{n_url[7]}")

def get_sonar_urls(results_plan, bamboo_user, bamboo_password):
    sonar_base_url="http://sonar.afphabitat.net:9000/dashboard"
    sonar_urls = []
    for result in results_plan:
        n_url = result.split('/')
        result = n_url[7]
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

def print_sonar_url(sonar_urls):
    for sonar_url in sonar_urls:
        print(sonar_url)

def is_branch_enabled(bamboo_user, bamboo_password, plan_key, branch_name):
        """
        Verifica si una rama está habilitada en Bamboo para un plan específico.
        
        :param plan_key: Clave del plan de Bamboo (ej. PROJ-PLAN).
        :param branch_name: Nombre de la rama que deseas verificar.
        :return: True si la rama está habilitada, False en caso contrario.
        """
        try:
            # URL para obtener las ramas de un plan
            url = f"http://bamboo.afphabitat.net:8085/rest/api/latest/plan/{plan_key}/branch.json"
            response = requests.get(url, auth=HTTPBasicAuth(bamboo_user, bamboo_password))
            response.raise_for_status()

            branches_info = response.json()

            # Recorremos las ramas y verificamos si el nombre coincide
            branch_name = branch_name.replace('/','-')
            for branch in branches_info['branches']['branch']:
                #print(f'{branch['shortName']} == {branch_name}')
                if branch['shortName'] == branch_name:
                    print(f"Rama '{branch_name}' encontrada en el plan '{plan_key}'.")
                    return branch['enabled']

            print(f"Rama '{branch_name}' no encontrada en el plan '{plan_key}'.")
            return False  # Si no se encuentra la rama, consideramos que no está habilitada.

        except requests.exceptions.RequestException as e:
            print(f"Error al consultar las ramas del plan {plan_key}: {e}")
            return False

def enable_branch(bamboo_user, bamboo_password, plan_key, branch_name):
        """
        Habilita una nueva rama en Bamboo para un plan específico.
        
        :param plan_key: Clave del plan de Bamboo (ej. PROJ-PLAN).
        :param branch_name: Nombre de la rama a habilitar.
        :return: True si la rama fue habilitada exitosamente, False en caso de error.
        """
        try:
            branch_name = branch_name.replace('/','-')
            # URL para crear una nueva rama en un plan
            # http://bamboo.afphabitat.net:8085/rest/api/latest/plan/NSWSB-CFQA/branch/bugfix-bps-merge?vcsBranch=bugfix-bps-merge.json
            url = f"http://bamboo.afphabitat.net:8085/rest/api/latest/plan/{plan_key}/branch/{branch_name}?vcsBranch={branch_name}"


            response = requests.put(url, auth=HTTPBasicAuth(bamboo_user, bamboo_password))
            response.raise_for_status()

            if response.status_code == 200:
                print(f"Rama '{branch_name}' habilitada exitosamente en el plan '{plan_key}'.")
                return True
            else:
                print(f"Error al habilitar la rama '{branch_name}' en el plan '{plan_key}'. Código de estado: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Error al intentar habilitar la rama '{branch_name}' en el plan {plan_key}: {e}")
            return False
        
def validate_branch(bamboo_user, bamboo_password, plan_key, source_branch):
    is_enabled = is_branch_enabled(bamboo_user, bamboo_password, plan_key, source_branch)

    if not is_enabled:
        print(f"La rama '{source_branch}' no está habilitada. Intentando habilitarla...")
        # Intentar habilitar la rama si no está habilitada
        success = enable_branch(bamboo_user, bamboo_password, plan_key, source_branch)
        if success:
            print(f"Rama '{source_branch}' habilitada exitosamente.")
        else:
            print(f"Fallo al habilitar la rama '{source_branch}'.")
    else:
        print(f"La rama '{source_branch}' ya está habilitada.")    

def main_test():
    """Función principal para buscar issues y cambiar el estado del primero encontrado."""
    jira_url, jira_token, jira_email, bitbucket_token, bamboo_user, bamboo_password, edge_driver_path, edge_user_data_dir, edge_profile_directory = load_config()
    
    issues = search_issues(jira_url, jira_token, jira_email)

    if issues:
        for issue in issues:
            key = issue.get('key')
            pull_requests = get_pull_request_paths(key, jira_url, jira_token, jira_email)
            api_prs = transform_pr_to_api(pull_requests)
            info_pull_requests = get_info_pull_requests(api_prs, bitbucket_token)
            urls_plan_bamboo = get_url_plan_bamboo(key, jira_url, jira_token, jira_email)
            pipelines_back_list = []
            for info_pull_request in info_pull_requests:
                url_pull_request = info_pull_request['url_pull_request']
                source_branch = info_pull_request['source_branch']
                tipo = info_pull_request['tipo']
                state = info_pull_request['state']
                component = info_pull_request['component']
                print(f'{url_pull_request} {source_branch} {tipo} {state}')

                if tipo == 'back' or tipo == 'front':
                    for url_plan_bamboo in urls_plan_bamboo:
                        plan_key = url_plan_bamboo.split('/')[4]
                        plan_desde_pauta = extraer_short_name(plan_key, bamboo_user, bamboo_password)
                        if plan_desde_pauta.lower() == component.lower():

                            validate_branch(bamboo_user, bamboo_password, plan_key, source_branch)

                            plan_key_branch = obtener_url_rama_bamboo(plan_key, source_branch, bamboo_user, bamboo_password)
                            print(f"Añadiendo a lista de ejecucion: {component} {plan_key_branch}")
                            pipelines_back_list.append({
                                'component': component,
                                'plan_key_branch': plan_key_branch,
                                'source_branch': source_branch,
                                'tipo': tipo
                            })
            queued_build_list = []
            if len(pipelines_back_list) > 0:
                for pipelines_back in pipelines_back_list:
                    print(f'{pipelines_back['plan_key_branch']} {pipelines_back['source_branch']}')
                    #
                    queued_build = ejecutar_plan_bamboo(pipelines_back['plan_key_branch'], pipelines_back['source_branch'], bamboo_user, bamboo_password)
                    queued_build_list.append(queued_build)
            else:
                print("No hay planes back por ejecutar")

            monitor = BambooBuildMonitor(api_urls=queued_build_list, bamboo_user=bamboo_user, bamboo_passowrd=bamboo_password)
            try:
                monitor.start_monitoring()
                monitor.wait_for_completion()
                build_states = monitor.build_states
                print_build_states(build_states=build_states)
                print_bamboo_url_states(build_states=build_states)
                sonar_urls = get_sonar_urls(build_states, bamboo_user, bamboo_password)
                print_sonar_url(sonar_urls)
                kill_edge_processes()
                temp_dir = capture_screenshots_with_cookies(edge_driver_path, edge_user_data_dir, edge_profile_directory, sonar_urls)
                upload_files_to_jira(jira_url, key, jira_email, jira_token, temp_dir)
                    
            except KeyboardInterrupt:
                print("\nPrograma interrumpido manualmente. Cerrando...")
            

    
    else:
        print("No se encontraron issues que coincidan con la consulta JQL.")

if __name__ == "__main__":
    main_test()
