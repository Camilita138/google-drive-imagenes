# excel.py
import gspread
from autenticacion import authenticate
from datetime import datetime
import time
from googleapiclient.errors import HttpError

SHEET_ID = '1pS7c5PmDUwENaY61jgHWUwSaH8Py1QeYkefoXeWl3Vo'

def update_sheet_with_links(image_urls, image_names, image_ids, sheet_name):
    retries = 0
    while retries < 3:
        try:
            print("Intentando autenticar con Google API...")
            creds = authenticate()
            client = gspread.authorize(creds)
            print(f"Autenticación exitosa. Accediendo a la hoja '{sheet_name}'...")
            worksheet = client.open_by_key(SHEET_ID).worksheet(sheet_name)

            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            start_row = len(worksheet.col_values(1)) + 1
            print(f"Primera fila vacía en la columna A: {start_row}")

            def extract_number(name):
                digits = ''.join(filter(str.isdigit, name or ''))
                return int(digits) if digits else 0

            combined = list(zip(image_names, image_urls, image_ids))
            combined.sort(key=lambda x: extract_number(x[0]))
            if combined:
                image_names, image_urls, image_ids = zip(*combined)
            else:
                image_names, image_urls, image_ids = [], [], []

            rows = []
            for name, url in zip(image_names, image_urls):
                if not name or not url:
                    continue
                rows.append([name, url, "", current_time])  # columnas A-D

            if rows:
                end_row = start_row + len(rows) - 1
                range_ad = f"A{start_row}:D{end_row}"
                print(f"Insertando datos en el rango {range_ad}...")
                worksheet.update(range_ad, rows)

                # Fórmulas en E con el ID directo
                formula_cells = []
                for i, file_id in enumerate(image_ids):
                    formula_cells.append(
                        gspread.Cell(
                            row=start_row + i,
                            col=5,
                            value=f'=IMAGE("https://drive.google.com/uc?export=view&id={file_id}")'
                        )
                    )
                print("Actualizando fórmulas en E...")
                worksheet.update_cells(formula_cells, value_input_option='USER_ENTERED')

                # LOGO / FIRMA en F
                worksheet.update_cell(start_row, 6, "LOGO")
                if end_row != start_row:
                    worksheet.update_cell(end_row, 6, "FIRMA")
                print("Columna F actualizada con 'LOGO' y/o 'FIRMA'.")

            break

        except HttpError as e:
            if getattr(e, 'resp', None) and e.resp.status == 429:
                retries += 1
                print("Demasiadas solicitudes. Reintentando...")
                time.sleep(5)
            else:
                print(f"Error HTTP: {e}")
                break
        except Exception as e:
            print(f"Error desconocido: {e}")
            break
