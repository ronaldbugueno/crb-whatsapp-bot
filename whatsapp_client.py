"""
Envío de mensajes salientes a través de WhatsApp Cloud API.
"""

import os
import httpx

GRAPH_API_VERSION = "v21.0"


def send_text_message(to: str, body: str) -> None:
    phone_number_id = os.environ["WHATSAPP_PHONE_NUMBER_ID"]
    token = os.environ["WHATSAPP_TOKEN"]

    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": body},
    }
    resp = httpx.post(url, headers=headers, json=payload, timeout=15)
    if resp.status_code >= 400:
        print("Error enviando mensaje de WhatsApp:", resp.status_code, resp.text)
    resp.raise_for_status()


def notify_admin(text: str) -> None:
    """Avisa al número administrador (por ejemplo, Ronald) que hay una conversación
    que necesita atención humana. Es opcional: si no se configura ADMIN_WHATSAPP_NUMBER,
    simplemente no hace nada (queda solo el log en consola). Si el envío falla (por ejemplo,
    porque el número no está autorizado mientras se usa el número de prueba de Meta), no debe
    interrumpir la respuesta al cliente: solo se registra el error en el log."""
    admin_number = os.environ.get("ADMIN_WHATSAPP_NUMBER")
    if not admin_number:
        print("[AVISO] Conversación derivada a un asesor (sin ADMIN_WHATSAPP_NUMBER configurado):", text)
        return
    try:
        send_text_message(admin_number, text)
    except Exception as e:
        print("[AVISO] No se pudo notificar al administrador (no interrumpe la respuesta al cliente):", e)
