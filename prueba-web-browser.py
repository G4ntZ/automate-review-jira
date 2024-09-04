

import webbrowser
import time
from PIL import ImageGrab

# URL que deseas abrir
url = "http://bamboo.afphabitat.net:8085/browse/WRELCLI-OCQA0-3"
webbrowser.open_new_tab(url)
time.sleep(4)

# Toma una captura de pantalla de toda la pantalla
screenshot = ImageGrab.grab()
screenshot.save("screenshot.png")
# Abrir una nueva pestaña en el navegador predeterminado
