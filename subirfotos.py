# subirfotos.py
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from autenticacion import authenticate
import os, time, mimetypes

PARENT_FOLDER_ID = '1qq-fmDrV_i2YqkfHwiQcYoxPSe4u4SrW'  # tu carpeta de Drive
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
MAX_RETRIES = 3

def is_valid_image(filename):
    return os.path.splitext(filename.lower())[1] in IMAGE_EXTENSIONS

def upload_images_to_drive(output_folder):
    print(f"Iniciando la subida de imágenes desde: {output_folder}")
    creds = authenticate()
    drive_service = build('drive', 'v3', credentials=creds)

    image_urls, image_names, image_ids = [], [], []

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
        while retries < MAX_RETRIES:
            try:
                mime, _ = mimetypes.guess_type(file_path)
                if not mime:
                    ext = os.path.splitext(filename)[1].lstrip(".").lower()
                    mime = f"image/{'jpeg' if ext == 'jpg' else ext}"

                media = MediaFileUpload(file_path, mimetype=mime, resumable=True)
                uploaded_file = drive_service.files().create(
                    body={'name': filename, 'parents': [PARENT_FOLDER_ID]},
                    media_body=media,
                    fields='id,name,webViewLink',
                    supportsAllDrives=True
                ).execute()

                file_id = uploaded_file['id']

                # Permiso público
                drive_service.permissions().create(
                    fileId=file_id,
                    body={'type': 'anyone', 'role': 'reader'},
                    supportsAllDrives=True
                ).execute()

                url = f"https://drive.google.com/uc?export=view&id={file_id}"
                image_names.append(filename)
                image_urls.append(url)
                image_ids.append(file_id)

                print(f"Imagen subida correctamente: {filename}")
                print(f"URL generada: {url}")
                break
            except Exception as e:
                retries += 1
                print(f"Error al subir {filename}: {e}")
                if retries < MAX_RETRIES:
                    print(f"Reintentando... (Intento {retries + 1}/{MAX_RETRIES})")
                    time.sleep(2)
                else:
                    print(f"Falló la subida de {filename} después de {MAX_RETRIES} intentos")

    print(f"Total de imágenes subidas: {len(image_urls)}")
    print("DEBUG return -> 3 valores (urls, names, ids)")
    return image_urls, image_names, image_ids
