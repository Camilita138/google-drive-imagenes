from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from autenticacion import authenticate
import os
import time

PARENT_FOLDER_ID = '1qq-fmDrV_i2YqkfHwiQcYoxPSe4u4SrW'  # ID de la carpeta en Google Drive (Shared Drive)
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
MAX_RETRIES = 3  # Número máximo de intentos

def is_valid_image(filename):
    return os.path.splitext(filename.lower())[1] in IMAGE_EXTENSIONS

def upload_images_to_drive(output_folder):
    print(f"Iniciando la subida de imágenes desde: {output_folder}")
    creds = authenticate()
    drive_service = build('drive', 'v3', credentials=creds)

    image_urls = []
    image_names = []

    for filename in os.listdir(output_folder):
        print(f"Revisando archivo: {filename}")
        if not is_valid_image(filename):
            print(f"Ignorado: no es una imagen válida -> {filename}")
            continue

        file_path = os.path.join(output_folder, filename)
        if not os.path.isfile(file_path):
            print(f"Omitido: no es un archivo -> {file_path}")
            continue

        retries = 0
        success = False

        while retries < MAX_RETRIES and not success:
            try:
                ext = os.path.splitext(filename)[1].lstrip(".")
                media = MediaFileUpload(file_path, mimetype=f'image/{ext}', resumable=True)

                print(f"Subiendo: {filename}")
                uploaded_file = drive_service.files().create(
                    body={'name': filename, 'parents': [PARENT_FOLDER_ID]},
                    media_body=media,
                    fields='id, name, webViewLink',
                    supportsAllDrives=True  # Soporte para Shared Drives
                ).execute()

                drive_service.permissions().create(
                    fileId=uploaded_file['id'],
                    body={'type': 'anyone', 'role': 'reader'},
                    supportsAllDrives=True  # Soporte para Shared Drives
                ).execute()

                url = f"https://drive.google.com/uc?export=view&id={uploaded_file['id']}"
                image_names.append(filename)
                image_urls.append(url)

                print(f"Imagen subida correctamente: {filename}")
                print(f"URL generada: {url}")

                success = True  # Marca como exitoso

            except Exception as e:
                retries += 1
                print(f"Error al subir {filename}: {str(e)}")
                if retries < MAX_RETRIES:
                    print(f"Reintentando... (Intento {retries + 1}/{MAX_RETRIES})")
                    time.sleep(2)  # Espera 2 segundos antes de reintentar

        if not success:
            print(f"Falló la subida de {filename} después de {MAX_RETRIES} intentos")

    print(f"Total de imágenes subidas: {len(image_urls)}")
    return image_urls, image_names
