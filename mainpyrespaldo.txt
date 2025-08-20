from flask import Flask, jsonify
import os
import json
import re
import asyncio
from firecrawl import AsyncFirecrawlApp
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)

# === CONFIGURACIÓN ===
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
SPREADSHEET_ID = "1a6nuphKrFi8mpGm_y0dCK6AM729h_F8OYD3i91VxOHA"
RANGE_NAME = "A2"

# === FUNCIONES ===

def extract_token_from_html(html):
    """Extrae el token usando múltiples patrones"""
    patterns = [
        r'access_token["\']?\s*[:=]\s*["\']([A-Za-z0-9\-_\.]{20,})["\']',
        r'"access_token"\s*:\s*"([^"]+)"',
        r'accessToken["\']?\s*[:=]\s*["\']([A-Za-z0-9\-_\.]{20,})["\']',
        r'token["\']?\s*[:=]\s*["\']([A-Za-z0-9\-_\.]{30,})["\']',
        r'Bearer\s+([A-Za-z0-9\-_\.]{20,})',
        r'authorization["\']?\s*[:=]\s*["\']Bearer\s+([^"\']+)["\']',
        r'["\']([A-Za-z0-9\-_\.]{50,})["\']',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        if matches:
            for match in matches:
                if len(match) >= 20 and not match.isdigit():
                    return match
    return None

async def get_token_from_firecrawl():
    app = AsyncFirecrawlApp(api_key=FIRECRAWL_API_KEY)
    response = await app.scrape_url(
        url='https://live.tvn.cl',
        formats=['rawHtml'],
        only_main_content=True,
        include_tags=['access_token'],
        parse_pdf=False,
        max_age=14400000
    )
    html = response.rawHtml
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
        token = asyncio.run(get_token_from_firecrawl())
        if not token:
            return jsonify({"status": "error", "message": "Token no encontrado"}), 500
        save_token_to_sheets(token)
        return jsonify({"status": "ok", "token": token})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
