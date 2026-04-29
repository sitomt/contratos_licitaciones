import pdfplumber
import json

PDFS = [
    "data/raw/presupuestos_generales_2026.pdf",
    "data/raw/resumen_ingresos_y_gastos.pdf"
]

def extraer_texto(ruta_pdf):
    texto_completo = []

    with pdfplumber.open(ruta_pdf) as pdf:
        print(f"Procesando: {ruta_pdf}")
        print(f"Total de paginas: {len(pdf.pages)}")

        for numero, pagina in enumerate(pdf.pages):
            texto = pagina.extract_text()
            tablas = pagina.extract_tables()

            contenido = {
                "pagina": numero + 1,
                "fuente": ruta_pdf,
                "texto": texto if texto else "",
                "tablas": tablas if tablas else [],
                "tipo": "texto" if texto else "imagen_sin_texto"
            }

            texto_completo.append(contenido)

            if texto:
                print(f"Pagina {numero + 1}: {len(texto)} caracteres | tablas: {len(tablas)}")
            else:
                print(f"Pagina {numero + 1}: sin texto (posible imagen escaneada)")

    return texto_completo

todos_los_textos = []

for pdf in PDFS:
    resultado = extraer_texto(pdf)
    todos_los_textos.extend(resultado)

with open("data/processed/datos_extraidos.json", "w", encoding="utf-8") as f:
    json.dump(todos_los_textos, f, ensure_ascii=False, indent=2)

print(f"\nExtraccion completada")
print(f"Total de paginas procesadas: {len(todos_los_textos)}")
print(f"Archivo guardado: data/processed/datos_extraidos.json")