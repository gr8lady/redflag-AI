#!/usr/bin/env python3
import subprocess
import argparse
import datetime
import os
import signal
import sys
import config

# Configuración - Rutas absolutas
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "deepseek_chat_log.txt")  # Ahora con ruta completa
REPORT_DIR = os.path.join(SCRIPT_DIR, "reportes")
TIMEOUT = 300

def ensure_spanish(prompt):
    """Añade instrucción para respuesta en español si no está presente"""
    if "español" not in prompt.lower() and "spanish" not in prompt.lower():
        return f"Responde únicamente en español: {prompt}\n[FIN]"
    return prompt + "\n[FIN]" if "[FIN]" not in prompt else prompt

def log_interaction(prompt, response):
    """Registra en el log histórico"""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"[{timestamp}] PROMPT:\n{prompt}\n\nRESPUESTA:\n{response}\n")
        log.write("=" * 80 + "\n")

def save_report(prompt, response):
    """Guarda en reporte individual"""
    os.makedirs(REPORT_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{REPORT_DIR}/reporte_{timestamp}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"PROMPT:\n{prompt}\n\nRESPUESTA:\n{response}")
    print(f"\n📄 Reporte guardado en: {os.path.abspath(filename)}")

def run_llama(query, timeout=TIMEOUT):
    """Ejecuta el modelo con control mejorado"""
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
        "--repeat_penalty", "1.2",
        "--color"  # Mejor visualización
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

        # Procesamiento en tiempo real
        full_output = []
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                print(line.strip(), end='', flush=True)
                full_output.append(line)
                if "[FIN]" in line:
                    process.terminate()
                    break

        output = ''.join(full_output).split("[FIN]")[0].strip()
        return output if output else "🟡 Respuesta incompleta"

    except subprocess.TimeoutExpired:
        process.kill()
        return "⌛ Tiempo agotado"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="Interfaz para DeepSeek LLM")
    parser.add_argument("--interactive", "-i", action="store_true", help="Modo conversación")
    parser.add_argument("prompt", nargs="?", type=str, help="Tu pregunta")
    args = parser.parse_args()

    if args.interactive:
        print("\n💬 Modo Interactivo (escribe 'salir' para terminar)\n")
        while True:
            try:
                prompt = input("[Tu pregunta]: ")
                if prompt.lower() in ("salir", "exit"):
                    break

                print("\n[Asistente]: ", end='', flush=True)
                response = run_llama(prompt)
                log_interaction(prompt, response)
                save_report(prompt, response)

            except KeyboardInterrupt:
                print("\n🔴 Sesión terminada")
                break

    elif args.prompt:
        print("\n⚙️ Procesando... (Ctrl+C para cancelar)\n")
        response = run_llama(args.prompt)
        log_interaction(args.prompt, response)
        save_report(args.prompt, response)
    else:
        print("Modos de uso:")
        print("  ./script.py \"Tu pregunta\"")
        print("  ./script.py --interactive")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    main()
