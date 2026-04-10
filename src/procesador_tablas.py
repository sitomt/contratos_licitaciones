import pdfplumber
import json

def inspeccionar_tablas(ruta_pdf, solo_pagina=8):
    with pdfplumber.open(ruta_pdf) as pdf:
        pagina = pdf.pages[solo_pagina - 1]
        tablas = pagina.extract_tables()
        
        print(f"Paginas {solo_pagina} — tablas encontradas: {len(tablas)}")
        
        for i, tabla in enumerate(tablas):
            print(f"\n--- TABLA {i+1} ---")
            print(f"Filas: {len(tabla)}")
            print(f"Columnas: {len(tabla[0]) if tabla else 0}")
            print(f"\nContenido fila por fila:")
            for j, fila in enumerate(tabla):
                print(f"  Fila {j}: {fila}")

inspeccionar_tablas("presupuestos_generales_2026.pdf", solo_pagina=8)