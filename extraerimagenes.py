import fitz  # PyMuPDF: para manipular archivos PDF
import os   # para manejar el sistema de archivos

def extract_images_from_pdf(pdf_path, output_folder):
    print(f"Iniciando la extracción de imágenes desde el archivo: {pdf_path}")
    
    try:
        doc = fitz.open(pdf_path)  # Abrir el archivo PDF
        os.makedirs(output_folder, exist_ok=True)  # Crear carpeta de salida si no existe
        img_count = 0  # Contador de imágenes extraídas

        print(f"Analizando el archivo PDF, total de páginas: {len(doc)}")
        
        for page_num, page in enumerate(doc):
            print(f"Extrayendo imágenes de la página {page_num + 1}...")
            for img in page.get_images(full=True):  # Obtener todas las imágenes de la página
                xref = img[0]  # Referencia del objeto de imagen
                try:
                    image_bytes = doc.extract_image(xref)["image"]  # Extraer los bytes de la imagen
                    # Guardar la imagen como archivo PNG
                    image_path = os.path.join(output_folder, f"image_{img_count + 1}.png")
                    with open(image_path, "wb") as f:
                        f.write(image_bytes)
                    print(f"Imagen {img_count + 1} extraída y guardada en: {image_path}")
                    img_count += 1
                except Exception as e:
                    print(f"Error al extraer o guardar la imagen de la página {page_num + 1}: {str(e)}")

        print(f"Total de imágenes extraídas: {img_count}")
        return img_count  # Retorna la cantidad de imágenes extraídas

    except Exception as e:
        print(f"Error al procesar el archivo PDF: {str(e)}")
        return 0