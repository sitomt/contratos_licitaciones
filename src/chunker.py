import json

TAMANO_CHUNK = 500
SOLAPAMIENTO = 50

def texto_a_chunks(texto, pagina, fuente):
    palabras = texto.split()
    chunks = []
    inicio = 0

    while inicio < len(palabras):
        fin = inicio + TAMANO_CHUNK
        chunk_palabras = palabras[inicio:fin]
        chunk_texto = " ".join(chunk_palabras)

        chunks.append({
            "texto": chunk_texto,
            "pagina": pagina,
            "fuente": fuente,
            "tipo": "texto"
        })

        inicio += TAMANO_CHUNK - SOLAPAMIENTO

    return chunks

def tabla_a_chunk(tabla, pagina, fuente):
    if not tabla or not tabla[0]:
        return None

    cabeceras = tabla[0]
    filas = tabla[1:]
    lineas = []

    for fila in filas:
        if not any(fila):
            continue
        partes = []
        for i, celda in enumerate(fila):
            if celda and i < len(cabeceras) and cabeceras[i]:
                cabecera = str(cabeceras[i]).replace("\n", " ").strip()
                valor = str(celda).replace("\n", " ").strip()
                partes.append(f"{cabecera}: {valor}")
        if partes:
            lineas.append(" | ".join(partes))

    if not lineas:
        return None

    return {
        "texto": "\n".join(lineas),
        "pagina": pagina,
        "fuente": fuente,
        "tipo": "tabla"
    }

def procesar_todo():
    with open("data/processed/datos_extraidos.json", "r", encoding="utf-8") as f:
        paginas = json.load(f)

    todos_los_chunks = []

    for pagina in paginas:
        numero = pagina["pagina"]
        fuente = pagina["fuente"]

        if pagina["texto"]:
            chunks_texto = texto_a_chunks(pagina["texto"], numero, fuente)
            todos_los_chunks.extend(chunks_texto)

        for tabla in pagina["tablas"]:
            chunk_tabla = tabla_a_chunk(tabla, numero, fuente)
            if chunk_tabla:
                todos_los_chunks.append(chunk_tabla)

    with open("data/processed/chunks.json", "w", encoding="utf-8") as f:
        json.dump(todos_los_chunks, f, ensure_ascii=False, indent=2)

    textos = [c for c in todos_los_chunks if c["tipo"] == "texto"]
    tablas = [c for c in todos_los_chunks if c["tipo"] == "tabla"]

    print(f"Chunks de texto: {len(textos)}")
    print(f"Chunks de tabla: {len(tablas)}")
    print(f"Total chunks: {len(todos_los_chunks)}")
    print(f"Guardado en: data/processed/chunks.json")
    print(f"\n--- Ejemplo chunk de texto ---")
    print(todos_los_chunks[0]["texto"][:300])
    print(f"\n--- Ejemplo chunk de tabla ---")
    tabla_ejemplo = next((c for c in todos_los_chunks if c["tipo"] == "tabla"), None)
    if tabla_ejemplo:
        print(tabla_ejemplo["texto"][:300])

procesar_todo()