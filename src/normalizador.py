import re


def normalizar_texto(texto: str) -> str:
    # 1. Reunir palabras partidas por guión de fin de línea
    texto = re.sub(r'(\w+)-\n(\w+)', r'\1\2', texto)

    # 2. Colapsar espacios múltiples en uno solo
    texto = re.sub(r' {2,}', ' ', texto)

    # 3. Eliminar puntos suspensivos de relleno
    texto = re.sub(r'\.{3,}', ' ', texto)

    # 4 y 5. Procesar línea a línea: eliminar líneas que sean solo número
    #         y eliminar cabeceras repetitivas del documento
    lineas = texto.split('\n')
    lineas_limpias = []
    for linea in lineas:
        if re.match(r'^\s*\d+\s*$', linea):
            continue
        if re.search(r'PROYECTO PRESUPUESTOS GENERALES 2026\s*\d*', linea):
            continue
        lineas_limpias.append(linea)

    # 6. Reunir líneas que no terminan en punto, coma, dos puntos o punto y coma
    resultado = []
    i = 0
    while i < len(lineas_limpias):
        linea = lineas_limpias[i]
        while (i + 1 < len(lineas_limpias)
               and linea.strip()
               and not re.search(r'[.,:;]$', linea.rstrip())):
            i += 1
            linea = linea.rstrip() + ' ' + lineas_limpias[i].lstrip()
        resultado.append(linea)
        i += 1

    # 7. Strip final
    return '\n'.join(resultado).strip()
