import os
import requests
from requests.auth import HTTPBasicAuth

def upload_files_to_jira(jira_url, jira_issue_key, username, api_token, folder_path):
    """
    Sube todos los archivos de una carpeta adjuntos a un issue en Jira.

    :param jira_url: URL de la instancia de Jira (por ejemplo, https://tudominio.atlassian.net)
    :param jira_issue_key: Clave del issue en Jira (por ejemplo, "PROJ-123")
    :param username: Nombre de usuario para autenticarse en Jira
    :param api_token: API Token para autenticarse en Jira
    :param folder_path: Ruta completa de la carpeta que contiene los archivos a subir
    :return: None
    """
    # Verificar que la carpeta existe
    if not os.path.exists(folder_path):
        print(f"Error: La carpeta {folder_path} no existe.")
        return
    
    # Listar todos los archivos en la carpeta
    files_in_folder = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    # Verificar si hay archivos en la carpeta
    if not files_in_folder:
        print(f"No se encontraron archivos en la carpeta: {folder_path}")
        return
    
    # Construir la URL de la API para subir archivos
    api_endpoint = f"{jira_url}/issue/{jira_issue_key}/attachments"
    
    # Establecer los encabezados necesarios para la subida
    headers = {
        "X-Atlassian-Token": "no-check"  # Se requiere este encabezado para subir archivos
    }
    
    # Autenticación básica usando el username y el API token
    auth = HTTPBasicAuth(username, api_token)
    
    # Iterar sobre cada archivo en la carpeta y subirlo
    for file_name in files_in_folder:
        file_path = os.path.join(folder_path, file_name)
        
        # Leer el archivo en binario para la subida
        with open(file_path, 'rb') as file:
            files = {
                'file': (file_name, file)
            }
            
            print(f"Iniciando la subida del archivo: {file_path}")
            
            # Hacer la petición POST a la API de Jira
            try:
                response = requests.post(api_endpoint, headers=headers, auth=auth, files=files)
                
                # Validar el estado de la respuesta
                if response.status_code == 200 or response.status_code == 201:
                    print(f"Subida exitosa: {file_name} ha sido adjuntado al issue {jira_issue_key}.")
                else:
                    print(f"Error en la subida de {file_name}. Código de respuesta: {response.status_code}")
                    print(f"Detalles del error: {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"Error durante la subida del archivo {file_name}: {e}")