import xmltodict
import sys
import configparser
import requests
from requests.auth import HTTPBasicAuth

def load_config(config_file='config.ini'):
    """Carga la configuración desde un archivo INI."""
    config = configparser.ConfigParser()
    config.read(config_file)
    
    jira_url = config.get('jira', 'url')
    jira_token = config.get('jira', 'token')
    jira_email = config.get('jira', 'email')
    bitbucket_app_password = config.get('bitbucket', 'app_password')
    bitbucket_token = config.get('bitbucket', 'token')
    bamboo_user = config.get('bamboo', 'user')
    bamboo_password = config.get('bamboo', 'password')

    return jira_url, jira_token, jira_email, bitbucket_app_password, bitbucket_token, bamboo_user, bamboo_password

def xml_to_json(xml_data):
    try:
        # Convertir XML a un diccionario de Python
        dict_data = xmltodict.parse(xml_data)
        
        return dict_data
    except Exception as e:
        return f'Error: {e}'

jira_url, jira_token, jira_email, bitbucket_app_password, bitbucket_token, bamboo_user, bamboo_password = load_config()
url = sys.argv[1]
response = requests.get(url, auth=HTTPBasicAuth(bamboo_user, bamboo_password))

if xml_to_json(response.content)['result']['buildState'] == 'Unknown':
    print(xml_to_json(response.content)['result']['progress']['percentageCompletedPretty'])
else:
    print(xml_to_json(response.content)['result']['buildState'])
