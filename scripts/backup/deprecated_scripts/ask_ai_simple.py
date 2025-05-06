import subprocess
import argparse
import datetime
import signal
import sys
import config
import os

LOG_FILE = "deepseek_chat_log.txt"
TIMEOUT = 300  # 5 minutos

def log_interaction(prompt, response):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"[{timestamp}] 🔍 Prompt:\n{prompt}\n\n")
        log.write(f"[{timestamp}] 🧠 Respuesta:\n{response}\n")
        log.write("=" * 80 + "\n")

def run_llama(query, timeout=TIMEOUT):
    command = [
        config.LLAMA_CLI_PATH,
        "-m", config.MODEL_PATH,
        "-p", query,
        "--temp", str(config.TEMP),
        "--top-k", str(config.TOP_K),
        "--top-p", str(config.TOP_P),
        "-n", str(config.MAX_TOKENS),
        "--ctx-size", "2048"
    ]

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        full_output = []

        while True:
            line = process.stdout.readline()
            if line == '' and process.poll() is not None:
                break
            if line:
                print(line.strip())
                full_output.append(line)

        # Captura lo que quedó en el búfer
        remaining_output, _ = process.communicate()
        if remaining_output:
            print(remaining_output.strip())
            full_output.append(remaining_output)

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

def clean_output(text):
    lines = text.splitlines()
    filtered = []
    for line in lines:
        if "## Project Title" in line:
            break  # corta en la parte que claramente no pertenece
        if line.strip().startswith(">") and "http" in line:
            continue  # evita basura con enlaces o markdown
        filtered.append(line)
    return "\n".join(filtered).strip()


def main():
    parser = argparse.ArgumentParser(description="Interfaz para DeepSeek LLM")
    parser.add_argument("--interactive", "-i", action="store_true", help="Iniciar modo interactivo")
    parser.add_argument("--input", "-f", type=str, help="Leer prompt desde archivo")
    parser.add_argument("--save", "-s", type=str, help="Guardar la respuesta en archivo externo")
    parser.add_argument("prompt", nargs="?", type=str, help="Prompt único (opcional)")
    args = parser.parse_args()

    if args.interactive:
        interactive_mode()

    elif args.input:
        if not os.path.isfile(args.input):
            print(f"❌ Error: No se encontró el archivo {args.input}")
            sys.exit(1)
        with open(args.input, "r", encoding="utf-8") as f:
            prompt = f.read()
        print("⚙️  Ejecutando...\n")
        output = run_llama(prompt + "\n\nRespuesta completa:")
        output_clean = clean_output(output)
        #imprime version limpia
        print("\n🧠 Respuesta:\n", output)
        log_interaction(prompt, output)
        if args.save:
            with open(args.save, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"\n💾 Respuesta guardada en {args.save}")

    elif args.prompt:
        print("⚙️  Ejecutando...\n")
        output = run_llama(args.prompt + "\n\nRespuesta completa:")
        print("\n🧠 Respuesta:\n", output)
        log_interaction(args.prompt, output)
        if args.save:
            with open(args.save, "w", encoding="utf-8") as f:
                f.write(output_clean)
            print(f"\n💾 Respuesta guardada en {args.save}")

    else:
        print("❌ Error: Usa '--interactive', '--input archivo.txt' o provee un prompt directo.")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))
    main()
