import os
import re
import json
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from flask import Flask

app = Flask(__name__)

# Variables de entorno
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY")
SERVICE_ACCOUNT_INFO = json.loads(os.environ.get("GOOGLE_SERVICE_ACCOUNT"))
SPREADSHEET_ID = "1a6nuphKrFi8mpGm_y0dCK6AM729h_F8OYD3i91VxOHA"
RANGE = "A2"

# Autenticación con Google Sheets
credentials = service_account.Credentials.from_service_account_info(
    SERVICE_ACCOUNT_INFO,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
sheets_service = build("sheets", "v4", credentials=credentials)

def extract_token_from_html(html):
    match = re.search(r'access_token\s*[:=]\s*[\'"]([A-Za-z0-9\-_\.]+)[\'"]', html)
    if match:
        return match.group(1)
    return None

@app.route("/token")
def get_token():
    try:
        response = requests.get(
            "https://www.tvn.cl/en-vivo",
            headers={"Authorization": f"Bearer {FIRECRAWL_API_KEY}"}
        )
        html = response.text
        token = extract_token_from_html(html)
        if token:
            sheets_service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=RANGE,
                valueInputOption="RAW",
                body={"values": [[token]]}
            ).execute()
            return json.dumps({"status": "ok", "token": token})
        else:
            return json.dumps({"status": "error", "message": "Token no encontrado"}), 500
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
