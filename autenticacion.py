# autenticacion.py
import os
import sys
from google.oauth2 import service_account

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def resource_path(relative_path):
    """Obtiene la ruta absoluta, incluso dentro del .exe empaquetado."""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

def authenticate():
    service_file_path = resource_path("keys.json")
    print(f"Ruta del archivo de claves: {service_file_path}")  # Debugging
    if not os.path.exists(service_file_path):
        print(f"ERROR: El archivo de claves no se encuentra en la ruta especificada: {service_file_path}")  # Debugging
        return None

    try:
        creds = service_account.Credentials.from_service_account_file(service_file_path, scopes=SCOPES)
        print("Autenticación exitosa con Google API.")  # Debugging
        return creds
    except Exception as e:
        print(f"Error al autenticar: {e}")  # Debugging
        return None