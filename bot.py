"""Bot de Telegram por POLLING. Otro ADAPTADOR sobre el mismo motor.

    python bot.py

Polling significa que este script le pregunta a Telegram cada pocos
segundos si hay mensajes nuevos. No necesita URL publica, ni HTTPS, ni
abrir puertos: solo salidas HTTP. Por eso funciona en la red de la
universidad y en tu laptop sin configurar nada.

Es la API REST mas simple que van a ver: dos endpoints, getUpdates y
sendMessage.
"""
import sys, time, html
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import requests
from src import settings, rag_core

cfg = settings.cargar()
TOKEN = settings.api_key("TELEGRAM_BOT_TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}"
MAX = cfg["telegram"]["max_caracteres"]

BIENVENIDA = (
    "Chatbot del reglamento de Beca 18.\n\n"
    "Escribe tu pregunta y respondo solo con lo que dice la norma oficial, "
    "citando la pagina.\n\n"
    "Si no esta en el reglamento, te lo digo en vez de inventarlo."
)


def enviar(chat_id: int, texto: str):
    """Telegram corta en 4096 caracteres, asi que partimos si hace falta."""
    for i in range(0, len(texto), MAX):
        requests.post(f"{API}/sendMessage", data={
            "chat_id": chat_id,
            "text": texto[i:i + MAX],
            "parse_mode": "HTML",
        }, timeout=30)


def escribiendo(chat_id: int):
    """El 'escribiendo...' de Telegram. Una linea, y el bot deja de parecer muerto."""
    requests.post(f"{API}/sendChatAction",
                  data={"chat_id": chat_id, "action": "typing"}, timeout=10)


def formatear(r: dict) -> str:
    cuerpo = html.escape(r["respuesta"])
    if r.get("abstuvo"):
        return cuerpo
    paginas = sorted({f["pagina"] for f in r["fuentes"]})
    pie = (f"\n\n<i>paginas consultadas: {paginas} | "
           f"{r['tokens_in']}+{r['tokens_out']} tokens | "
           f"USD {r['costo_usd']:.8f} | {r['latencia_s']}s</i>")
    return cuerpo + pie


def main():
    print("Cargando el motor RAG...")
    motor = rag_core.MotorRAG()
    print("Motor listo. Bot escuchando. Ctrl+C para detener.\n")

    offset = None
    while True:
        try:
            resp = requests.get(f"{API}/getUpdates",
                                params={"offset": offset, "timeout": 25},
                                timeout=40).json()
        except Exception as e:
            print("error de red:", e)
            time.sleep(cfg["telegram"]["intervalo_polling"])
            continue

        for upd in resp.get("result", []):
            offset = upd["update_id"] + 1
            msg = upd.get("message") or {}
            texto = (msg.get("text") or "").strip()
            chat_id = msg.get("chat", {}).get("id")
            if not texto or chat_id is None:
                continue

            usuario = msg.get("from", {}).get("first_name", "?")
            print(f"[{usuario}] {texto}")

            if texto in ("/start", "/help"):
                enviar(chat_id, BIENVENIDA)
                continue

            escribiendo(chat_id)
            try:
                r = motor.responder(texto)
                enviar(chat_id, formatear(r))
            except Exception as e:
                enviar(chat_id, "Ocurrio un error procesando tu pregunta.")
                print("  error:", e)


if __name__ == "__main__":
    main()
