#!/usr/bin/env python3
import requests
import argparse
import os
import json
from datetime import datetime

# Configuración
API_URL = "http://localhost:8080/completion"
REPORTS_DIR = "api_reports"

def call_llama_api(prompt):
    """Hace la petición al servidor llama.cpp"""
    headers = {"Content-Type": "application/json"}
    data = {
        "prompt": prompt,
        "temperature": 0.7,
        "top_k": 40,
        "top_p": 0.9,
        "n_predict": 512
    }

    try:
        response = requests.post(API_URL, headers=headers, json=data, timeout=120)
        response.raise_for_status()
        return response.json()["content"]
    except Exception as e:
        return f"❌ Error en API: {str(e)}"

def save_report(prompt, response):
    """Guarda el resultado en un archivo organizado"""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{REPORTS_DIR}/report_{timestamp}.json"

    report = {
        "prompt": prompt,
        "response": response,
        "timestamp": timestamp
    }

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Reporte guardado en: {filename}")
    return filename

def main():
    parser = argparse.ArgumentParser(description="Cliente para llama-server API")
    parser.add_argument("prompt", help="Pregunta para el modelo")
    args = parser.parse_args()

    print(f"\n📡 Enviando prompt: '{args.prompt}'")
    response = call_llama_api(args.prompt)

    save_report(args.prompt, response)
    print("\n🧠 Respuesta recibida:\n" + "-" * 40)
    print(response)

if __name__ == "__main__":
    main()
