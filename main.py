from flask import Flask, jsonify
import requests
import re
import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)

# === CONFIGURACIÓN ===
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")  # Usa variables de entorno en Render
SPREADSHEET_ID = "1a6nuphKrFi8mpGm_y0dCK6AM729h_F8OYD3i91VxOHA"
RANGE_NAME = "A2"

# === FUNCIONES AUXILIARES ===

def extract_token_from_html(html):
    match = re.search(r'access_token[\'"=: ]+[\'"]?([A-Za-z0-9\-_\.]+)[\'"]?', html)
    return match.group(1) if match else None

def get_token_from_firecrawl():
    url = "https://api.firecrawl.dev/scrape-url"

    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "url": "https://www.tvn.cl/en-vivo",
        "formats": ["rawHtml"],
        "only_main_content": True,
        "include_tags": ["access_token"],
        "parse_pdf": False,
        "max_age": 14400000
    }
    response = requests.post(url, headers=headers, data=json.dumps(body))
    
    print(">>> Firecrawl status:", response.status_code)
    print(">>> Firecrawl response text:", response.text[:500])  # Solo muestra los primeros 500 caracteres

    data = response.json()  # <-- Aquí está el error si no es JSON
    html = data.get("rawHtml", "")
    return extract_token_from_html(html)

def save_token_to_sheets(token):
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    SERVICE_ACCOUNT_INFO = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT"))
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()
    sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME,
        valueInputOption="RAW",
        body={"values": [[token]]}
    ).execute()

# === RUTAS ===

@app.route("/")
def home():
    return "✅ Servicio funcionando. Usa /token para obtener el token."

@app.route("/token")
def token():
    try:
        token = get_token_from_firecrawl()
        if not token:
            return jsonify({"status": "error", "message": "Token no encontrado"}), 500
        save_token_to_sheets(token)
        return jsonify({"status": "ok", "token": token})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
