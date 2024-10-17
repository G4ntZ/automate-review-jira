from win10toast import ToastNotifier
import os

# Inicialización del notificador
toaster = ToastNotifier()

# Diccionario de iconos para diferentes tipos de notificación
ICON_PATHS = {
    "success": "icons/success.ico",   # Verde
    "error": "icons/error.ico",       # Rojo
    "info": "icons/info.ico"          # Azul
}

def show_notification(message: str, notification_type: str = "info"):
    """
    Muestra una notificación en Windows con base en el tipo de notificación.

    Parámetros:
    message (str): El mensaje que se mostrará en la notificación.
    notification_type (str): El tipo de notificación, puede ser 'success', 'error', o 'info'.
    """
    if notification_type not in ICON_PATHS:
        raise ValueError(f"Tipo de notificación '{notification_type}' no es válido. "
                         f"Debe ser 'success', 'error', o 'info'.")
    
    icon_path = ICON_PATHS[notification_type]
    
    # Verifica si el archivo de ícono existe
    if not os.path.exists(icon_path):
        raise FileNotFoundError(f"El archivo de ícono '{icon_path}' no se encontró.")

    # Muestra la notificación con el ícono adecuado
    toaster.show_toast(
        title=f"Notificación: {notification_type.capitalize()}",
        msg=message,
        icon_path=icon_path,
        duration=5  # Duración de 5 segundos
    )

def main():
    """
    Función principal que muestra ejemplos de notificaciones.
    """
    try:
        # Ejemplo de notificación de éxito
        show_notification("Operación completada con éxito.", "success")
        
        # Ejemplo de notificación de error
        show_notification("Ha ocurrido un error crítico.", "error")
        
        # Ejemplo de notificación informativa
        show_notification("Este es un mensaje de información.", "info")
    
    except Exception as e:
        print(f"Error mostrando la notificación: {e}")

if __name__ == "__main__":
    main()
