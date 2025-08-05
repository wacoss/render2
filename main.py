import os
import json
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask

app = Flask(__name__)

GOOGLE_CREDS = json.loads(os.environ['GOOGLE_SERVICE_ACCOUNT'])
SHEET_ID = "1a6nuphKrFi8mpGm_y0dCK6AM729h_F8OYD3i91VxOHA"

def obtener_token_desde_firecrawl():
    url = "https://api.firecrawl.dev/api/v1/scrape-url"
    headers = {
        "x-api-key": os.environ['FIRECRAWL_API_KEY'],
        "Content-Type": "application/json"
    }
    payload = {
        "url": "https://www.tvn.cl/en-vivo",
        "formats": ["rawHtml"],
        "only_main_content": True,
        "include_tags": ["access_token"],
        "parse_pdf": False,
        "max_age": 14400000
    }
    r = requests.post(url, headers=headers, json=payload)
    html = r.json()["data"]["rawHtml"]
    import re
    match = re.search(r'access_token["'=: ]+["\']?([A-Za-z0-9\-_\.]+)["\']?', html)
    return match.group(1) if match else None

def guardar_en_hoja(token):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDS, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1
    sheet.update_acell("A2", token)

@app.route("/token", methods=["GET"])
def actualizar_token():
    try:
        token = obtener_token_desde_firecrawl()
        if token:
            guardar_en_hoja(token)
            return {"status": "ok", "token": token}
        return {"status": "error", "message": "Token no encontrado"}, 400
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

if __name__ == "__main__":
    app.run(debug=False)