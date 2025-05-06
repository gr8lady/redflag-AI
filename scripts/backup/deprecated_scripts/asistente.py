#!/usr/bin/env python3
import subprocess
import argparse
import os
import time
from datetime import datetime
import config

# Configuración
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reportes")
TIMEOUT = 120  # 2 minutos máximo

def ensure_dir(path):
    """Crea directorio si no existe"""
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        print(f"⚠ Error creando directorio: {e}")
        return False
    return True

def save_to_file(prompt, response):
    """Guarda prompt y respuesta en archivo"""
    if not ensure_dir(REPORT_DIR):
        return False

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(REPORT_DIR, f"report_{timestamp}.txt")

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"PROMPT:\n{prompt}\n\n")
            f.write(f"RESPUESTA:\n{response}\n")

        print(f"\n✅ Guardado en: {filename}")
        return True
    except Exception as e:
        print(f"⚠ Error guardando archivo: {e}")
        return False

def run_model(prompt):
    """Ejecuta el modelo y captura la salida"""
    command = [
        config.LLAMA_CLI_PATH,
        "-m", config.MODEL_PATH,
        "-p", prompt,
        "--temp", str(config.TEMP),
        "-n", str(config.MAX_TOKENS),
        "--ctx-size", "1024",
        "--repeat_penalty", "1.1"
    ]

    try:
        print("\n⚙ Procesando... (Ctrl+C para cancelar)\n")
        print("-" * 40)

        # Ejecutar y capturar salida en tiempo real
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
            # Verificar timeout
            if time.time() - start_time > TIMEOUT:
                process.kill()
                return "⌛ Tiempo excedido (2 minutos)"

            # Leer línea
            line = process.stdout.readline()
            if not line:
                if process.poll() is not None:
                    break
                continue

            # Mostrar y capturar
            print(line, end='', flush=True)
            full_output.append(line)

            # Detener si parece completo
            if any(s in line.lower() for s in ["</s>", "[end]", "fin"]):
                process.terminate()
                break

        return ''.join(full_output).strip()

    except KeyboardInterrupt:
        process.kill()
        return "\n🛑 Interrumpido por el usuario"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="Asistente de IA para reportes")
    parser.add_argument("prompt", help="Tu pregunta para el modelo")
    args = parser.parse_args()

    # Ejecutar modelo
    response = run_model(args.prompt)

    # Guardar resultado
    print("\n" + "-" * 40)
    save_to_file(args.prompt, response)

if __name__ == "__main__":
    main()
