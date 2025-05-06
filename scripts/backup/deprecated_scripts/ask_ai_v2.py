import subprocess
import argparse
import datetime
import logging
import shlex
import config


# Configuración de logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding='utf-8'
)

def log_interaction(prompt, response):
    logging.info("🔍 Prompt:\n%s\n", prompt)
    logging.info("🧠 Respuesta:\n%s\n%s\n", response, "=" * 80)

def run_llama(query):
    command = [
        config.LLAMA_CLI_PATH,
        "-m", config.MODEL_PATH,
        "-p", query,
        "--temp", str(config.TEMP),
        "--top-k", str(config.TOP_K),
        "--top-p", str(config.TOP_P),
        "-n", str(config.MAX_TOKENS)
    ]

    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            input=""  # simula presionar Enter para salir del modo interactivo
        )
        return result.stdout

    except subprocess.CalledProcessError as e:
        error_message = f"❌ Error en llama-cli (código {e.returncode}): {e.stderr}"
        logging.error(error_message)
        return error_message

    except FileNotFoundError:
        error_message = "❌ Error: No se encontró el ejecutable o el modelo."
        logging.error(error_message)
        return error_message

def main():
    parser = argparse.ArgumentParser(description="Interfaz local para DeepSeek LLM")
    parser.add_argument("prompt", type=str, nargs="+", help="Prompt para el modelo")
    args = parser.parse_args()
    args.prompt = " ".join(args.prompt).strip()

    if not args.prompt:
        print("❌ Error: El prompt no puede estar vacío.")
        return

    print("⚙️  Ejecutando DeepSeek LLM...\n")
    output = run_llama(args.prompt)
    print("🧠 Respuesta del modelo:\n", output)
    log_interaction(args.prompt, output)

if __name__ == "__main__":
    main()
