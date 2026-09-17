"""
Servidor del bot de WhatsApp de CRB Ingeniería (Flask, compatible con hosting
compartido tipo cPanel vía Passenger).

Ejecutar en local (para probar antes de subir):
    python3 server.py
    (o bien: flask --app server run --port 8000)

Ver README.md para cómo conectar esto con WhatsApp Cloud API (Meta),
tanto en local (con ngrok) como ya subido al hosting.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # carga las variables desde .env antes de cualquier otra cosa

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import config
from ai_reply import get_ai_reply
from whatsapp_client import send_text_message, notify_admin

app = Flask(__name__)

# Permite que el widget de chat del sitio web (crb.icrb.cl u otro dominio que definas)
# llame a /chat desde el navegador. Edita la lista con tu(s) dominio(s) real(es).
CORS(
    app,
    resources={r"/chat": {"origins": [
        "https://crb.icrb.cl",
        "https://www.icrb.cl",
        "https://icrb.cl",
    ]}},
)

FUERA_DE_HORARIO_MSG = (
    "Gracias por escribirnos. Nuestro horario comercial es de lunes a viernes de 9:00 a 18:00; "
    "en este momento estamos fuera de horario, pero un asesor te responderá apenas estemos disponibles. "
    "Si es una urgencia técnica con contrato vigente, indícalo y lo derivamos de inmediato. "
    "Para poder contactarte, cuéntanos tu nombre y un teléfono o correo de contacto."
)

DERIVADO_MSG = (
    "Gracias por tu mensaje. Un asesor de CRB Ingeniería va a revisar tu consulta y te responde a la brevedad. "
    "Para poder contactarte, cuéntanos tu nombre y un teléfono o correo de contacto."
)


@app.get("/webhook")
def verify_webhook():
    """Meta llama a este endpoint una sola vez, al configurar el webhook, para confirmar
    que el servidor es tuyo. Debe devolver el 'hub.challenge' tal cual si el token coincide."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    expected_token = os.environ.get("WHATSAPP_VERIFY_TOKEN")
    if mode == "subscribe" and token == expected_token:
        return Response(challenge, mimetype="text/plain")
    return Response(status=403)


@app.post("/webhook")
def receive_message():
    """Meta manda aquí cada mensaje entrante."""
    data = request.get_json(force=True, silent=True) or {}

    try:
        entry = data["entry"][0]
        change = entry["changes"][0]["value"]
        messages = change.get("messages")
        if not messages:
            # Puede ser un evento de "status" (entregado/leído), lo ignoramos.
            return jsonify({"status": "ignored"})

        message = messages[0]
        from_number = message["from"]
        text = message.get("text", {}).get("body", "")

        handle_incoming_message(from_number, text)

    except (KeyError, IndexError) as e:
        print("Payload inesperado de WhatsApp:", e, data)

    return jsonify({"status": "ok"})


def decide_reply(text: str, source_label: str) -> tuple[str, bool]:
    """Decide qué responder a un mensaje, sin importar si viene de WhatsApp o del chat
    del sitio web. Devuelve (texto_de_respuesta, se_derivo_a_un_asesor)."""

    # 1) Temas que siempre van a un asesor humano (reclamos, contratos, urgencias, etc.)
    if config.needs_escalation(text):
        notify_admin(f"Conversación derivada ({source_label}). Escribió: {text}")
        return DERIVADO_MSG, True

    # 2) Fuera de horario comercial: avisamos y derivamos, sin usar la IA.
    if not config.is_business_hours():
        notify_admin(f"Mensaje fuera de horario ({source_label}): {text}")
        return FUERA_DE_HORARIO_MSG, True

    # 3) Respuestas fijas (horario, servicios, contacto, ubicación, cotización).
    fixed = config.match_fixed_reply(text)
    if fixed:
        return fixed, False

    # 4) Preguntas abiertas: responde la IA usando el contexto de la empresa.
    try:
        reply = get_ai_reply(text)
    except Exception as e:
        print("Error generando respuesta con IA:", e)
        notify_admin(f"Fallo la IA respondiendo ({source_label}) a '{text}': {e}")
        return DERIVADO_MSG, True
    return reply, False


def handle_incoming_message(from_number: str, text: str) -> None:
    print(f"Mensaje de WhatsApp {from_number}: {text}")
    reply, _ = decide_reply(text, source_label=f"WhatsApp {from_number}")
    send_text_message(from_number, reply)


@app.post("/chat")
def chat_endpoint():
    """Endpoint para el widget de chat del sitio web. Recibe {"message": "..."}
    y devuelve {"reply": "...", "escalated": true/false}."""
    data = request.get_json(force=True, silent=True) or {}
    text = (data.get("message") or "").strip()
    if not text:
        return jsonify({"error": "Falta el campo 'message'"}), 400
    if len(text) > 1000:
        text = text[:1000]

    reply, escalated = decide_reply(text, source_label="chat web")
    return jsonify({"reply": reply, "escalated": escalated})


if __name__ == "__main__":
    # Solo para pruebas locales. En el hosting, Passenger usa passenger_wsgi.py.
    app.run(host="0.0.0.0", port=8000, debug=True)
