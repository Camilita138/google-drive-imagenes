# app.py
import os
import sys
import traceback
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix

from extraerimagenes import extract_images_from_pdf
from subirfotos import upload_images_to_drive
from excel import update_sheet_with_links

# ---------- Utilidad de rutas (funciona igual empaquetado o en código fuente) ----------
def resource_path(relative_path: str) -> str:
    """
    Devuelve la ruta absoluta a un recurso tanto en desarrollo como cuando se empaqueta con PyInstaller.
    """
    try:
        if getattr(sys, "frozen", False):
            base_path = sys._MEIPASS  # type: ignore[attr-defined]
        else:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
    except Exception as e:
        print(f"[resource_path] Error: {e}")
        return relative_path

# ---------- App Flask ----------
app = Flask(
    __name__,
    template_folder=resource_path("templates"),
    static_folder=resource_path("static"),
)

# ProxyFix para respetar cabeceras de IIS/ARR (host, esquema, IP cliente)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1)  # type: ignore
app.config["PREFERRED_URL_SCHEME"] = "https"

# (opcional) limitar tamaño de subida (ej: 20 MB)
# app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

# ---------- Config ----------
ALLOWED_EXTENSIONS = {"pdf"}
UPLOAD_FOLDER = resource_path("static/uploads")
EXTRACTION_FOLDER = os.path.join(UPLOAD_FOLDER, "imagenes_extraidas")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Crear carpetas necesarias
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACTION_FOLDER, exist_ok=True)

# Lista de hojas disponibles
HOJAS_DISPONIBLES = [
    "bulco", "martin", "diego", "kdelacruz", "ncruz", "ccastro", "jbernal",
    "aguevara", "dbenitez", "dregalado", "mmoran", "evacacela", "jcarpio",
    "nmejia", "kprocel", "kvivas", "scachiguango", "talvarez"
]

# ---------- Helpers ----------
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def clean_folder(folder_path: str) -> None:
    if not os.path.isdir(folder_path):
        return
    for name in os.listdir(folder_path):
        p = os.path.join(folder_path, name)
        if os.path.isfile(p):
            try:
                os.unlink(p)
            except Exception as e:
                print(f"[clean_folder] No se pudo borrar {p}: {e}")

def extract_id_from_url(u: str) -> str:
    """Fallback: obtiene el fileId de una URL tipo ...uc?export=view&id=FILE_ID"""
    if not u:
        return ""
    if "id=" in u:
        return u.split("id=", 1)[1].split("&", 1)[0]
    return ""

# ---------- Rutas de diagnóstico ----------
@app.get("/health")
def health():
    return "ok", 200

@app.get("/debug/headers")
def debug_headers():
    from flask import request
    return {
        "url": request.url,
        "url_root": request.url_root,
        "host": request.host,
        "scheme": request.scheme,
        "remote_addr": request.remote_addr,
        "X-Forwarded-For": request.headers.get("X-Forwarded-For"),
        "X-Forwarded-Proto": request.headers.get("X-Forwarded-Proto"),
        "X-Forwarded-Host": request.headers.get("X-Forwarded-Host"),
    }, 200

# ---------- App principal ----------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            print("\n[PASO 1] Recibiendo archivo y hoja...")
            file = request.files.get("pdf_file")
            sheet_name = request.form.get("sheet_name")
            print(f"Archivo: {file.filename if file else 'Ninguno'} | Hoja: {sheet_name}")

            if not file or not allowed_file(file.filename):
                return "Archivo no válido. Sube un PDF.", 400
            if not sheet_name or not sheet_name.strip():
                return "Debes seleccionar una hoja para actualizar.", 400

            # Guardar PDF
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)
            print(f"[OK] Guardado en: {file_path}")

            # Extraer imágenes
            print("\n[PASO 2] Extrayendo imágenes...")
            extract_images_from_pdf(file_path, EXTRACTION_FOLDER)
            print("[OK] Extraídas en:", EXTRACTION_FOLDER)

            # Subir a Drive
            print("\n[PASO 3] Subiendo imágenes a Google Drive...")
            result = upload_images_to_drive(EXTRACTION_FOLDER)

            # Soporta versiones que devuelven 3 valores (urls, names, ids) o 2 (urls, names)
            if isinstance(result, tuple) and len(result) == 3:
                image_urls, image_names, image_ids = result
            else:
                image_urls, image_names = result
                image_ids = [extract_id_from_url(u) for u in image_urls]
                print("[INFO] upload_images_to_drive devolvió 2 valores; IDs extraídos de las URLs.")

            print(f"[OK] Subidas: {len(image_urls)}")

            # Actualizar Google Sheet
            print("\n[PASO 4] Actualizando Google Sheet...")
            update_sheet_with_links(image_urls, image_names, image_ids, sheet_name)
            print("[OK] Hoja actualizada.")

            # Limpieza
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"[WARN] No se pudo borrar PDF temporal: {e}")
            clean_folder(EXTRACTION_FOLDER)
            print("[OK] Limpieza finalizada.")

            return redirect(url_for("success", sheet_name=sheet_name))

        except Exception:
            error_trace = traceback.format_exc()
            print("\n[ERROR]\n" + error_trace)
            return f"<h2>Ocurrió un error:</h2><pre>{error_trace}</pre>", 500

    # GET
    return render_template("index.html", hojas_disponibles=HOJAS_DISPONIBLES)

@app.route("/success/<sheet_name>")
def success(sheet_name: str):
    return f"¡Éxito! La hoja <strong>{sheet_name}</strong> ha sido actualizada con las imágenes."

# ---------- Entrada local (dev) ----------
if __name__ == "__main__":
    # En prod usa un WSGI server (Waitress, Gunicorn, etc.)
    # Ejemplo Waitress:
    #   python -m waitress --listen=127.0.0.1:5051 app:app
    app.run(host="0.0.0.0", port=5050, debug=True)
