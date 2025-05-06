import subprocess
import argparse
import datetime
import signal
import sys
import config
import os
import re


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
        with subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        ) as process:

            full_output = []

            # Lee en tiempo real
            for line in process.stdout:
                if line:
                    print(line.strip(), flush=True)
                    full_output.append(line)

            # Asegurarse de capturar lo que falte
            remaining_output, _ = process.communicate(timeout=timeout)
            if remaining_output:
                print(remaining_output.strip(), flush=True)
                full_output.append(remaining_output)

            return ''.join(full_output)

    except subprocess.TimeoutExpired:
        process.kill()
        return "⌛ Tiempo de espera agotado"
    except Exception as e:
        return f"❌ Error: {str(e)}"

def interactive_mode():
    print("\n💬 **Modo Interactivo** (presiona ENTER sin escribir para terminar)\n")
    while True:
        try:
            prompt = input("\n[Usuario]: ")
            if prompt.strip() == "":
                print("👋 Saliendo del modo interactivo.")
                break

            print("\n[Asistente]: ", end="", flush=True)
            output = run_llama(prompt + "\n\nRespuesta completa:")
            output_clean = clean_output(output)

            print(output_clean)
            log_interaction(prompt, output_clean)

        except KeyboardInterrupt:
            print("\n🔴 Interrumpido por el usuario.")
            break
        except Exception as e:
            print(f"\n⚠️ Error: {e}")
            continue

def clean_output(text):
    lines = text.strip().splitlines()
    filtered = []

    stop_keywords = ["title:", "description:", "published:", "tags:", "editor:", "markdown", "http", "##"]
    paragraph = []
    paragraph_end_found = False

    for line in lines:
        stripped = line.strip()

        if any(k in stripped.lower() for k in stop_keywords):
            break  # Cortamos en cuanto vemos algo no deseado

        if not stripped:
            if paragraph and not paragraph_end_found:
                # Primera línea vacía después de texto = posible fin
                paragraph_end_found = True
                continue
            elif paragraph_end_found:
                break  # Segunda línea vacía = claramente ya terminó
            continue

        paragraph.append(stripped)
        paragraph_end_found = False  # Reset si sigue escribiendo

    # Unimos líneas con espacios donde haga falta
    cleaned = " ".join(paragraph)
    # Elimina saltos tipo "superposición. Ademá\n> s,"
    cleaned = re.sub(r"> ?[a-z]*,", "", cleaned)
    return cleaned.strip()

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
