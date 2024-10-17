from notify import show_notification

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