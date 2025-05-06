import requests
import argparse
import datetime

def hacer_pregunta(prompt, max_tokens=300):
    url = "http://localhost:8080/completion"
    payload = {
        "prompt": prompt,
        "n_predict": max_tokens,
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "stop": ["</s>"]
    }

    try:
        r = requests.post(url, json=payload)
        r.raise_for_status()
        return r.json()["content"]
    except Exception as e:
        return f"❌ Error al contactar llama-server: {str(e)}"

def guardar_respuesta(prompt, respuesta, archivo):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(archivo, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] 🧠 Prompt:\n{prompt}\n\n")
        f.write(f"[{timestamp}] ✨ Respuesta:\n{respuesta}\n")
        f.write("=" * 80 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Preguntar a llama-server vía API")
    parser.add_argument("prompt", type=str, help="Pregunta o comando para el modelo")
    parser.add_argument("--output", "-o", type=str, default="respuestas_llama.txt", help="Archivo donde guardar la respuesta")
    parser.add_argument("--tokens", "-n", type=int, default=300, help="Tokens máximos a predecir")
    args = parser.parse_args()

    print("⚙️ Preguntando a llama-server...\n")
    respuesta = hacer_pregunta(args.prompt, args.tokens)
    print("🧠 Respuesta:\n")
    print(respuesta)

    guardar_respuesta(args.prompt, respuesta, args.output)
    print(f"\n💾 Respuesta guardada en {args.output}")
