#!/usr/bin/env python3
import subprocess
import argparse
import datetime
import os
import signal
import sys
import config
from threading import Thread
from queue import Queue, Empty

# Configuración
LOG_FILE = "deepseek_chat_log.txt"
REPORT_DIR = "reportes"
TIMEOUT = 300  # 5 minutos

def ensure_spanish(prompt):
    """Añade instrucción para respuesta en español si no está presente"""
    if "español" not in prompt.lower():
        return f"Responde en español: {prompt}\n\n[FIN]"
    return prompt

def save_report(prompt, response):
    """Guarda en reporte con marca de tiempo"""
    os.makedirs(REPORT_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{REPORT_DIR}/reporte_{timestamp}.txt"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"PROMPT:\n{prompt}\n\nRESPUESTA:\n{response}")
    print(f"\n📄 Reporte guardado en: {filename}")

def run_llama(query, timeout=TIMEOUT):
    """Ejecuta el modelo con control de finalización"""
    formatted_prompt = ensure_spanish(query)

    command = [
        config.LLAMA_CLI_PATH,
        "-m", config.MODEL_PATH,
        "-p", formatted_prompt,
        "--temp", str(config.TEMP),
        "--top-k", str(config.TOP_K),
        "--top-p", str(config.TOP_P),
        "-n", str(config.MAX_TOKENS),
        "--ctx-size", "2048",
        "--repeat_penalty", "1.1"  # Evita repeticiones infinitas
    ]

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # Procesamiento en tiempo real con detección de [FIN]
        full_output = []
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                print(line.strip(), end='', flush=True)  # Stream output
                full_output.append(line)
                if "[FIN]" in line:  # Detección de marcador de final
                    process.terminate()
                    break

        output = ''.join(full_output).split("[FIN]")[0].strip()
        return output if output else "🟡 El modelo no generó respuesta completa."

    except subprocess.TimeoutExpired:
        process.kill()
        return "⌛ Tiempo de espera agotado"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="Interfaz para DeepSeek LLM")
    parser.add_argument("--interactive", "-i", action="store_true", help="Modo interactivo")
    parser.add_argument("prompt", nargs="?", type=str, help="Prompt único")
    args = parser.parse_args()

    if args.interactive:
        print("\n💬 Modo Interactivo (escribe 'salir' para terminar)")
        while True:
            try:
                prompt = input("\n[Tu pregunta]: ")
                if prompt.lower() in ("salir", "exit"):
                    break

                print("\n[Asistente]: ", end='', flush=True)
                response = run_llama(prompt)
                log_interaction(prompt, response)
                save_report(prompt, response)

            except KeyboardInterrupt:
                print("\n🔴 Sesión terminada por el usuario")
                break

    elif args.prompt:
        print("\n⚙️ Procesando...")
        response = run_llama(args.prompt)
        print("\n\n🧠 Respuesta completa!")
        log_interaction(args.prompt, response)
        save_report(args.prompt, response)
    else:
        print("❌ Usa: ./script.py [prompt] ó ./script.py --interactive")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    main()
