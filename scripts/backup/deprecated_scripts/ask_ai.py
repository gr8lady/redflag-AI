import subprocess
import argparse
import datetime
import config  # tu archivo con las rutas y parámetros

LOG_FILE = "deepseek_chat_log.txt"

def log_interaction(prompt, response):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"[{timestamp}] 🔍 Prompt:\n{prompt}\n\n")
        log.write(f"[{timestamp}] 🧠 Respuesta:\n{response}\n")
        log.write("=" * 80 + "\n")

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
        result = subprocess.run(command, capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        error_message = f"❌ Error al ejecutar llama-cli: {e}"
        # Guardar el error en el log
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as log:
            log.write(f"[{timestamp}] ❌ ERROR:\n{error_message}\n")
            log.write("=" * 80 + "\n")
        return error_message

def main():
    parser = argparse.ArgumentParser(description="Interfaz local para DeepSeek LLM")
    parser.add_argument("prompt", type=str, help="Prompt o pregunta para el modelo")
    args = parser.parse_args()

    print("⚙️  Ejecutando DeepSeek LLM...\n")
    output = run_llama(args.prompt)
    print("🧠 Respuesta del modelo:\n")
    print(output)

    # Guardar interacción en log
    log_interaction(args.prompt, output)

if __name__ == "__main__":
    main()

