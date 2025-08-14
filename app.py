import os
import traceback
import sys
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from extraerimagenes import extract_images_from_pdf
from subirfotos import upload_images_to_drive
from excel import update_sheet_with_links
import webbrowser

# Función para obtener la ruta correcta de los archivos, tanto en desarrollo como empaquetados
def resource_path(relative_path):
    """Obtiene la ruta correcta de un archivo cuando la app es empaquetada o no."""
    try:
        # Si estamos ejecutando desde un archivo empaquetado con PyInstaller
        if getattr(sys, 'frozen', False):
            # Si está empaquetado con PyInstaller, buscar archivos en la ruta del ejecutable
            base_path = sys._MEIPASS
        else:
            # Si estamos ejecutando desde el código fuente
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
    except Exception as e:
        print(f"Error obteniendo la ruta del recurso: {e}")
        return relative_path

# Inicializa la aplicación Flask usando las rutas correctas
app = Flask(__name__, 
            template_folder=resource_path('templates'), 
            static_folder=resource_path('static'))

UPLOAD_FOLDER = 'static/uploads'
EXTRACTION_FOLDER = os.path.join(UPLOAD_FOLDER, 'imagenes_extraidas')
ALLOWED_EXTENSIONS = {'pdf'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

HOJAS_DISPONIBLES = [
    "bulco", "martin", "diego", "kdelacruz", "ncruz", "ccastro", "jbernal",
    "aguevara", "dbenitez", "dregalado", "mmoran", "evacacela", "jcarpio",
    "nmejia", "kprocel", "kvivas", "scachiguango", "talvarez"
]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def clean_folder(folder_path):
    for f in os.listdir(folder_path):
        file_to_delete = os.path.join(folder_path, f)
        if os.path.isfile(file_to_delete):
            os.unlink(file_to_delete)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            print("\n[PASO 1] Recibiendo archivo y hoja...")
            file = request.files.get('pdf_file')
            sheet_name = request.form.get('sheet_name')
            print(f"Archivo recibido: {file.filename if file else 'Ninguno'}")
            print(f"Hoja seleccionada: {sheet_name}")

            if not file or not allowed_file(file.filename):
                print("Archivo inválido.")
                return "Archivo no válido. Por favor, sube un archivo PDF.", 400

            if not sheet_name or sheet_name.strip() == "":
                print("No se seleccionó hoja.")
                return "Debes seleccionar una hoja para actualizar.", 400

            os.makedirs(EXTRACTION_FOLDER, exist_ok=True)

            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            print(f"Archivo guardado en: {file_path}")

            print("\n[PASO 2] Extrayendo imágenes...")
            extract_images_from_pdf(file_path, EXTRACTION_FOLDER)
            print("Imágenes extraídas en:", EXTRACTION_FOLDER)
            print("Contenido extraído:", os.listdir(EXTRACTION_FOLDER))

            print("\n[PASO 3] Subiendo imágenes a Google Drive...")
            image_urls, image_names = upload_images_to_drive(EXTRACTION_FOLDER)
            print("URLs de imágenes obtenidas:")
            for url in image_urls:
                print("  URL:", url)

            print("\n[PASO 4] Actualizando Google Sheet...")
            update_sheet_with_links(image_urls, image_names, sheet_name)
            print("Hoja actualizada con éxito.")

            os.remove(file_path)
            clean_folder(EXTRACTION_FOLDER)
            print("Limpieza finalizada.")

            return redirect(url_for('success', sheet_name=sheet_name))

        except Exception as e:
            error_trace = traceback.format_exc()
            print("\nERROR DETECTADO:")
            print(error_trace)  # Esto imprimirá el rastreo completo del error
            return f"<h2>Hubo un error al procesar el archivo:</h2><pre>{error_trace}</pre>", 500

    return render_template('index.html', hojas_disponibles=HOJAS_DISPONIBLES)

@app.route('/success/<sheet_name>')
def success(sheet_name):
    return f"¡Éxito! La hoja <strong>{sheet_name}</strong> ha sido actualizada con las imágenes."

if __name__ == '__main__':
    #webbrowser.open('http://localhost:5050')
    app.run(host='0.0.0.0', port=5050)