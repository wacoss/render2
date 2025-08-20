import requests
import os

url = "https://api.firecrawl.dev/v2/scrape"  # ✅ sin espacios

payload = {
    "url": "https://live.tvn.cl",  # mejor con https
    "formats": ["rawHtml"],
    "maxAge": 60000,  # 1 minuto → actualiza más seguido
    "pageOptions": {
        "waitFor": 4000  # espera 4 segundos a que cargue JS
    }
}

headers = {
    "Authorization": f"Bearer {os.getenv('FIRECRAWL_API_KEY')}",  # ✅ desde variable
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers)

if response.status_code == 200:
    data = response.json()
    if data.get("success"):
        html = data["data"].get("rawHtml", "")
        print("HTML recibido:", len(html), "caracteres")
        # Aquí puedes aplicar tu regex para buscar el token
    else:
        print("Error en Firecrawl:", data.get("error"))
else:
    print("Error HTTP:", response.status_code, response.text)
    


