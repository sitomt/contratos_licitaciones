import requests
import json

# URL de la API de PLACE — contratos adjudicados recientes
URL = "https://contrataciondelestado.es/wps/PA_1_EVIDEJ53L0O0I40U03AAPC1H82/FichaContrato"

params = {
    "idEvol": "",
    "codProcedimiento": "",
    "codTipo": "",
    "codEstado": "ADJ",  # ADJ = adjudicados
    "objeto": "",
    "importeDesde": "",
    "importeHasta": "",
    "fechaDesde": "",
    "fechaHasta": "",
    "adjudicatario": "",
    "page": 1,
    "pageSize": 10,
    "format": "json"
}

def explorar():
    print("Conectando a PLACE...")
    try:
        respuesta = requests.get(URL, params=params, timeout=15)
        print(f"Status: {respuesta.status_code}")
        print(f"Primeros 3000 caracteres:")
        print(respuesta.text[:3000])
        
        # Guardar respuesta completa para analizarla
        with open("data/processed/respuesta_cruda.json", "w", encoding="utf-8") as f:
            f.write(respuesta.text)
        print("\nGuardado en data/processed/respuesta_cruda.json")
        
    except Exception as e:
        print(f"Error: {e}")

explorar()
