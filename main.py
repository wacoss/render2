from flask import Flask, jsonify
import os
import re
import requests

app = Flask(__name__)

def extract_token_from_html(html):
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

def get_token_from_firecrawl():
    url = "https://api.firecrawl.dev/v2/scrape"
    
    payload = {
        "url": "live.tvn.cl",
        "onlyMainContent": True,
        "includeTags": ["access_token"],
        "maxAge": 172800000,
        "formats": ["rawHtml"]
    }
    
    headers = {
        "Authorization": f"Bearer {os.getenv('FIRECRAWL_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Error en Firecrawl API: {response.status_code}")
    
    data = response.json()
    
    if not data.get('success'):
        raise Exception("Firecrawl falló")
    
    html = data.get('data', {}).get('rawHtml', '')
    if not html:
        raise Exception("No se obtuvo HTML")
    
    return extract_token_from_html(html)

@app.route("/")
def home():
    return "Servicio funcionando. Usa /token para obtener el token."

@app.route("/token")
def token():
    try:
        token = get_token_from_firecrawl()
        if not token:
            return jsonify({"status": "error", "message": "Token no encontrado"}), 500
        
        return jsonify({"status": "ok", "token": token})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
