from monitor import BambooBuildMonitor
import configparser

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

if __name__ == "__main__":
    bamboo_api_urls = [
        "http://bamboo.afphabitat.net:8085/rest/api/latest/result/WL12CRT-WSSOLDSDEV-1",
        "http://bamboo.afphabitat.net:8085/rest/api/latest/result/WL12CRT-WSSOLDSDEV-5"
    ]
    jira_url, jira_token, jira_email, bitbucket_app_password, bitbucket_token, bamboo_user, bamboo_password = load_config()
    
    monitor = BambooBuildMonitor(api_urls=bamboo_api_urls, bamboo_user=bamboo_user, bamboo_passowrd=bamboo_password)
    try:
        monitor.start_monitoring()
        monitor.wait_for_completion()
    except KeyboardInterrupt:
        print("\nPrograma interrumpido manualmente. Cerrando...")