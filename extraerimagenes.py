# extraerimagenes.py
import fitz  # PyMuPDF
import os

def extract_images_from_pdf(pdf_path, output_folder, zoom=2.0, alpha=False):
    """
    Extrae imágenes respetando rotaciones / flips aplicados en el PDF.
    Prioriza el nombre de imagen (image name) para obtener el bbox;
    si falla, usa get_image_rects(xref); como último recurso, extrae el bitmap crudo.
    """
    print(f"Iniciando la extracción respetando transformaciones: {pdf_path}")
    os.makedirs(output_folder, exist_ok=True)

    doc = fitz.open(pdf_path)
    img_count = 0

    for pno, page in enumerate(doc, start=1):
        print(f"Página {pno}: buscando imágenes…")
        images = page.get_images(full=True)  # [(xref, smask, w, h, bpc, cs, alt, name, ...)]
        for i, img in enumerate(images, start=1):
            xref = img[0]
            imname = img[7] if len(img) > 7 else None

            # 1) Intento con image name (respeta CTM: rotación/flip)
            rect = None
            if imname:
                try:
                    rect = page.get_image_bbox(imname)  # <- AQUÍ la diferencia
                except Exception as e:
                    print(f"  name {imname} (xref {xref}): bbox por nombre falló: {e}")

            # 2) Fallback: rectángulos por xref
            if rect is None:
                rects = page.get_image_rects(xref)
                if rects:
                    rect = rects[0]  # si se dibuja varias veces, toma la primera

            try:
                if rect:
                    # Renderiza el recorte ya transformado
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat, clip=rect, alpha=alpha)
                    out_path = os.path.join(output_folder, f"image_{img_count+1}.png")
                    pix.save(out_path)
                    img_count += 1
                    print(f"  -> guardada {out_path}")
                else:
                    # 3) Último recurso: bitmap crudo (podría salir invertido)
                    raw = doc.extract_image(xref)
                    if not raw:
                        print(f"  xref {xref}: sin datos extraíbles; se omite.")
                        continue
                    out_path = os.path.join(output_folder, f"image_{img_count+1}.png")
                    with open(out_path, "wb") as f:
                        f.write(raw["image"])
                    img_count += 1
                    print(f"  -> guardada (bitmap crudo) {out_path}")
            except Exception as e:
                print(f"  xref {xref}: error al guardar: {e}")

    print(f"Total de imágenes extraídas: {img_count}")
    return img_count
