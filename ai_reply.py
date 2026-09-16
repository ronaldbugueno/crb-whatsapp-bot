"""
Genera respuestas con IA (Claude) para preguntas abiertas que no calzan
con ninguna respuesta fija, usando la información de la empresa como contexto.
"""

import os
from anthropic import Anthropic
from config import COMPANY_INFO

_client: Anthropic | None = None


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Falta ANTHROPIC_API_KEY en el archivo .env. "
                "Consigue una clave en console.anthropic.com y agrégala ahí."
            )
        _client = Anthropic(api_key=api_key)
    return _client


SYSTEM_PROMPT = f"""Eres el asistente de WhatsApp de CRB Ingeniería, una empresa chilena de automatización industrial.
Respondes de forma breve (máximo 3-4 líneas), clara y cercana, en español de Chile.
Usa SOLO la información de la empresa que se te entrega a continuación. Si te preguntan algo que
no puedes responder con esa información (precios exactos, plazos específicos, temas legales o de contratos),
dilo con honestidad y ofrece derivar la conversación a un asesor humano.
No inventes datos (teléfonos, precios, nombres de personas) que no estén en el contexto.

Información de la empresa:
{COMPANY_INFO}
"""


def get_ai_reply(user_message: str) -> str:
    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()
