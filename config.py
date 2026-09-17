"""
Configuración del bot de WhatsApp de CRB Ingeniería.
Edita libremente los textos, el horario y las palabras clave según necesites.
"""

from datetime import datetime
import zoneinfo

TIMEZONE = zoneinfo.ZoneInfo("America/Santiago")

# Horario de atención "humana" (fuera de este rango, el bot avisa que
# un asesor responderá en horario hábil, en vez de prometer una respuesta inmediata).
BUSINESS_HOURS = {
    0: (9, 18),  # Lunes
    1: (9, 18),  # Martes
    2: (9, 23),  # Miércoles -- TEMPORAL: extendido para pruebas, revertir a (9, 18)
    3: (9, 18),  # Jueves
    4: (9, 18),  # Viernes
    5: None,     # Sábado (cerrado)
    6: None,     # Domingo (cerrado)
}

COMPANY_INFO = """
Nombre: CRB Ingeniería
Rubro: Automatización industrial, electricidad, montaje de tableros, mantenimiento, redes y fibra óptica.
Desde 2011 desarrollando soluciones integrales de automatización industrial, electricidad y conectividad para la industria chilena.
Servicios:
- Automatización industrial
- Electricidad y tecnología
- Montaje y armado de tableros eléctricos y de control
- Mantenimiento industrial
- Redes y fibra óptica (cableado estructurado, certificación, redes OT/IT)
Contacto comercial: acomercial@icrb.cl
Teléfono/WhatsApp: +56 9 9541 1566
Dirección: Luis Peña Guzmán 477, Pudahuel, Santiago, Chile.
Soporte técnico para clientes con contrato: disponible las 24 horas para urgencias.
Horario comercial (cotizaciones, consultas generales): Lunes a Viernes, 9:00 a 18:00.
"""

# Respuestas fijas por palabra clave (minúsculas, sin tildes se comparan igual gracias a normalize()).
FIXED_REPLIES = {
    ("horario", "hora atienden", "atencion"): (
        "Nuestro horario comercial es de lunes a viernes de 9:00 a 18:00. "
        "Si tienes un contrato de mantenimiento vigente, el soporte técnico de urgencia está disponible las 24 horas."
    ),
    ("servicios", "que hacen", "que ofrecen", "rubro"): (
        "En CRB Ingeniería trabajamos en: automatización industrial, electricidad y tecnología, "
        "montaje y armado de tableros, mantenimiento industrial, y redes y fibra óptica. "
        "¿Sobre cuál de estos te gustaría más información?"
    ),
    ("contacto", "correo", "email", "telefono"): (
        "Puedes escribirnos a acomercial@icrb.cl o llamar al +56 9 9541 1566. "
        "También estamos en Luis Peña Guzmán 477, Pudahuel."
    ),
    ("ubicacion", "direccion", "donde estan", "donde queda"): (
        "Estamos en Luis Peña Guzmán 477, Pudahuel, Santiago."
    ),
    ("cotizacion", "presupuesto", "precio", "cuanto cuesta"): (
        "Para cotizar necesitamos algunos datos de tu proyecto. "
        "Cuéntanos: ¿qué tipo de servicio necesitas (automatización, electricidad, tableros, mantenimiento o redes), "
        "en qué comuna/región, y si es urgente? También déjanos tu nombre y un teléfono o correo de contacto "
        "para que te enviemos la cotización."
    ),
}

# Si el mensaje del cliente contiene alguna de estas palabras, se deriva a un asesor humano
# en vez de dejar que la IA improvise (por ejemplo, temas sensibles, reclamos, contratos).
ESCALATION_KEYWORDS = [
    "hablar con alguien", "hablar con una persona", "asesor", "ejecutivo", "humano",
    "reclamo", "urgente", "emergencia", "contrato", "factura", "boleta", "pago",
]


def normalize(text: str) -> str:
    import unicodedata
    text = text.lower().strip()
    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    return text


def is_business_hours(now: datetime | None = None) -> bool:
    now = now or datetime.now(TIMEZONE)
    hours = BUSINESS_HOURS.get(now.weekday())
    if not hours:
        return False
    start, end = hours
    return start <= now.hour < end


def match_fixed_reply(message: str) -> str | None:
    norm = normalize(message)
    for keywords, reply in FIXED_REPLIES.items():
        if any(normalize(k) in norm for k in keywords):
            return reply
    return None


def needs_escalation(message: str) -> bool:
    norm = normalize(message)
    return any(normalize(k) in norm for k in ESCALATION_KEYWORDS)
