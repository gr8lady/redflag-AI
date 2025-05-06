#!/usr/bin/env python3
import requests
import argparse
import os
import json
from datetime import datetime

# Configuración
API_URL = "http://localhost:8080/completion"
REPORTS_DIR = "api_reports"

def clean_output(text):
    lines = text.strip().splitlines()
    filtered = []
    stop_keywords = ["title:", "description:", "published:", "tags:", "editor:", "markdown", "http", "##"]
    paragraph = []
    paragraph_end_found = False

    for line in lines:
        stripped = line.strip()
        if any(k in stripped.lower() for k in stop_keywords):
            break
        if not stripped:
            if paragraph and not paragraph_end_found:
                paragraph_end_found = True
                continue
            elif paragraph_end_found:
                break
            continue
        paragraph.append(stripped)
        paragraph_end_found = False

    return " ".join(paragraph).strip()

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
    """Guarda el resultado en archivos JSON y TXT"""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{REPORTS_DIR}/report_{timestamp}"

    # JSON
    report = {
        "prompt": prompt,
        "response": response,
        "timestamp": timestamp
    }
    json_path = base_name + ".json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # TXT simple
    txt_path = base_name + ".txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f"[Prompt]\n{prompt}\n\n[Respuesta]\n{response}\n")

    print(f"\n✅ Reporte JSON guardado en: {json_path}")
    print(f"📝 Copia TXT guardada en: {txt_path}")
    return json_path, txt_path

def main():
    parser = argparse.ArgumentParser(description="Cliente API local para llama-server")
    parser.add_argument("prompt", nargs="?", help="Pregunta o comando para el modelo")
    parser.add_argument("--input", "-f", type=str, help="Leer prompt desde archivo")
    args = parser.parse_args()

    if args.input:
        if not os.path.isfile(args.input):
            print(f"❌ Error: archivo '{args.input}' no encontrado.")
            return
        with open(args.input, "r", encoding="utf-8") as f:
            prompt = f.read().strip()
    elif args.prompt:
        prompt = args.prompt
    else:
        print("❌ Error: Debes ingresar un prompt o usar --input archivo.txt")
        return

    print(f"\n📡 Enviando prompt:\n{prompt}\n")
    response_raw = call_llama_api(prompt)
    response_clean = clean_output(response_raw)

    save_report(prompt, response_clean)
    print("\n🧠 Respuesta recibida:\n" + "-" * 40)
    print(response_clean)

if __name__ == "__main__":
    main()
