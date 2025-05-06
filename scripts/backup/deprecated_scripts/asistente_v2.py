#!/usr/bin/env python3
import subprocess
import argparse
import os
import time
from datetime import datetime
import signal
import config

# Configuración
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reportes")
TIMEOUT = 120  # 2 minutos máximo
ABORTED = False  # Bandera para interrupciones

def signal_handler(sig, frame):
    global ABORTED
    ABORTED = True
    print("\n🛑 Interrupción solicitada...")

def ensure_dir(path):
    """Crea directorio si no existe"""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        print(f"⚠ Error creando directorio: {e}")
        return False

def save_to_file(prompt, response, interrupted=False):
    """Guarda el resultado siempre, marcando si fue interrumpido"""
    if not ensure_dir(REPORT_DIR):
        return False

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        status = "INTERRUMPIDO" if interrupted else "COMPLETO"
        filename = os.path.join(REPORT_DIR, f"report_{timestamp}_{status}.txt")

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"PROMPT:\n{prompt}\n\n")
            f.write(f"RESPUESTA ({status}):\n{response}\n")

        print(f"\n✅ Guardado en: {filename}")
        return True
    except Exception as e:
        print(f"⚠ Error guardando archivo: {e}")
        return False

def run_model(prompt):
    """Ejecuta el modelo con captura robusta"""
    global ABORTED
    command = [
        config.LLAMA_CLI_PATH,
        "-m", config.MODEL_PATH,
        "-p", f"{prompt}\n[FIN]",  # Marcador explícito
        "--temp", str(config.TEMP),
        "-n", str(config.MAX_TOKENS),
        "--ctx-size", "1024",
        "--repeat_penalty", "1.1"
    ]

    try:
        print("\n⚙ Procesando (2 mins max)...")
        print("-" * 40)

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        full_output = []
        start_time = time.time()

        while True:
            if time.time() - start_time > TIMEOUT:
                process.kill()
                return ("⌛ Tiempo excedido", False)

            line = process.stdout.readline()
            if not line:
                if process.poll() is not None:
                    break
                continue

            print(line, end='', flush=True)
            full_output.append(line)

            if ABORTED:
                process.kill()
                return ("".join(full_output).strip(), True)

            if "[FIN]" in line:
                process.terminate()
                return ("".join(full_output).split("[FIN]")[0].strip(), False)

        return ("".join(full_output).strip(), False)

    except Exception as e:
        return (f"❌ Error: {str(e)}", False)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    parser = argparse.ArgumentParser(description="Generador de Reportes")
    parser.add_argument("prompt", help="Pregunta para el modelo")
    args = parser.parse_args()

    response, was_interrupted = run_model(args.prompt)

    print("\n" + "-" * 40)
    save_to_file(args.prompt, response, was_interrupted)

if __name__ == "__main__":
    main()
