import subprocess
import argparse
import datetime
import signal
import sys
import config
from threading import Thread
from queue import Queue, Empty

LOG_FILE = "deepseek_chat_log.txt"
TIMEOUT = 300  # 5 minutos (ajústalo)

def log_interaction(prompt, response):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"[{timestamp}] 🔍 Prompt:\n{prompt}\n\n")
        log.write(f"[{timestamp}] 🧠 Respuesta:\n{response}\n")
        log.write("=" * 80 + "\n")

def run_llama(query, timeout=300):
    command = [
        config.LLAMA_CLI_PATH,
        "-m", config.MODEL_PATH,
        "-p", query,
        "--temp", str(config.TEMP),
        "--top-k", str(config.TOP_K),
        "--top-p", str(config.TOP_P),
        "-n", str(config.MAX_TOKENS),
        "--ctx-size", "2048"  # Añade esto si usas contexto largo
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

        # Leer salida en tiempo real
        full_output = []
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())  # Muestra la salida inmediatamente
                full_output.append(output)

        return ''.join(full_output)

    except subprocess.TimeoutExpired:
        process.kill()
        return "⌛ Tiempo de espera agotado"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def interactive_mode():
    print("\n💬 **Modo Interactivo** (escribe 'salir' para terminar)\n")
    while True:
        try:
            prompt = input("\n[Usuario]: ")
            if prompt.lower() in ("salir", "exit"):
                break

            print("\n[Asistente]: ", end="", flush=True)
            response = run_llama(prompt)
            log_interaction(prompt, response)

        except KeyboardInterrupt:
            print("\n🔴 Interrumpido por el usuario.")
            break
        except Exception as e:
            print(f"\n⚠️ Error: {e}")
            continue

def main():
    parser = argparse.ArgumentParser(description="Interfaz para DeepSeek LLM")
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Iniciar modo interactivo"
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        type=str,
        help="Prompt único (opcional)"
    )
    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
    elif args.prompt:
        print("⚙️  Ejecutando...\n")
        output = run_llama(args.prompt + "\n\nRespuesta completa:")
        print("\n🧠 Respuesta:\n", output)
        log_interaction(args.prompt, output)
    else:
        print("❌ Error: Usa '--interactive' o provee un prompt.")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))  # Maneja Ctrl+C
    main()
