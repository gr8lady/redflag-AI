import subprocess
import argparse
import datetime
import signal
import sys
import os
import config
from threading import Thread
from queue import Queue, Empty

def save_report(prompt, response):
    os.makedirs("reportes", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"reportes/reporte_{timestamp}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"PROMPT: {prompt}\n\nRESPUESTA:\n{response}")
    print(f"✅ Reporte guardado en {filename}")

def run_llama(query, timeout=60):
    # Instrucción clara para español + formato de respuesta
    spanish_prompt = f"""Responde en español, sé claro y conciso.
Prompt: {query}
Respuesta (3 líneas máximo):\n[FIN]"""

    command = [
        config.LLAMA_CLI_PATH,
        "-m", config.MODEL_PATH,
        "-p", spanish_prompt,
        "-n", "100",
        "--temp", "0.3",  # Reducir creatividad para mayor precisión
        "--repeat_penalty", "1.2"  # Evita repeticiones
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        # Extrae solo la respuesta hasta "[FIN]"
        return result.stdout.split("[FIN]")[0].strip()
    except subprocess.TimeoutExpired:
        return "🔴 ERROR: Tiempo agotado. Prueba con un prompt más corto."

def main():
    parser = argparse.ArgumentParser(description="Generador de Reportes en Español")
    parser.add_argument("prompt", type=str, help="Pregunta para el modelo")
    args = parser.parse_args()

    print("⚙️ Procesando (espere unos segundos)...")
    output = run_llama(args.prompt)

    print("\n🧠 RESPUESTA EN ESPAÑOL:")
    print(output)
    save_report(args.prompt, output)

if __name__ == "__main__":
    main()
