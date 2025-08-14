import gspread
from autenticacion import authenticate
from datetime import datetime
import time
from googleapiclient.errors import HttpError

SHEET_ID = '1pS7c5PmDUwENaY61jgHWUwSaH8Py1QeYkefoXeWl3Vo'  # ID de la hoja de cálculo

def update_sheet_with_links(image_urls, image_names, sheet_name):
    retries = 0
    while retries < 3:
        try:
            print(f"Intentando autenticar con Google API...")  # Debugging
            creds = authenticate()  # Autenticación con Google API
            client = gspread.authorize(creds)  # Autorizar cliente de gspread
            print(f"Autenticación exitosa. Accediendo a la hoja '{sheet_name}'...")  # Debugging
            worksheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)  # Acceder a la hoja específica

            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Timestamp actual
            start_row = len(worksheet.col_values(1)) + 1  # Primera fila vacía en la columna A
            print(f"Primera fila vacía en la columna A: {start_row}")  # Debugging

            def extract_number(name):
                """Extraer el número de la imagen desde su nombre."""
                numbers = ''.join(filter(str.isdigit, name))  # Extraer solo los dígitos
                return int(numbers) if numbers else 0  # Devolver el número o 0 si no se encuentra

            # Ordenar las imágenes por número en el nombre del archivo
            combined = list(zip(image_names, image_urls))
            combined.sort(key=lambda x: extract_number(x[0]))  # Ordenar por número en el nombre
            image_names, image_urls = zip(*combined)
            print(f"Imágenes ordenadas correctamente.")  # Debugging

            # Crear datos para las columnas A-D
            rows = []
            for name, url in zip(image_names, image_urls):
                if not name or not url:
                    continue
                rows.append([name, url, "", current_time])  # A-D

            # Insertar en bloque en las columnas A-D
            if rows:
                end_row = start_row + len(rows) - 1
                range_ad = f"A{start_row}:D{end_row}"
                print(f"Insertando datos en el rango {range_ad}...")  # Debugging
                worksheet.update(range_ad, rows)

                # Crear fórmulas IMAGE en la columna E
                formula_cells = []
                for i, url in enumerate(image_urls):
                    cell = gspread.Cell(row=start_row + i, col=5, 
                        value=f'=IMAGE("https://drive.google.com/uc?export=view&id={url.split("/")[-2]}")')
                    formula_cells.append(cell)
                
                # Actualizar celdas con las fórmulas
                print(f"Actualizando fórmulas en las celdas de la columna E...")  # Debugging
                worksheet.update_cells(formula_cells, value_input_option='USER_ENTERED')

                # Escribir "LOGO" y "FIRMA" en la columna F
                worksheet.update_cell(start_row, 6, "LOGO")
                if end_row != start_row:
                    worksheet.update_cell(end_row, 6, "FIRMA")
                print(f"Columna F actualizada con 'LOGO' y 'FIRMA'.")  # Debugging

            break  # Salir del ciclo si todo ha ido bien

        except HttpError as e:
            if e.resp.status == 429:  # Error por demasiadas solicitudes
                retries += 1
                print("Demasiadas solicitudes. Intentando de nuevo...")  # Debugging
                time.sleep(5)
            else:
                print(f"Error HTTP: {e}")  # Debugging
                break
        except Exception as e:
            print(f"Error desconocido: {e}")  # Debugging
            break