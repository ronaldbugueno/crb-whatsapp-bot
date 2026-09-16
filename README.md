# Bot de WhatsApp — CRB Ingeniería

Responde automáticamente por WhatsApp: preguntas frecuentes (horario, servicios, contacto),
preguntas abiertas con IA, y deriva a un asesor humano cuando corresponde (fuera de horario,
reclamos, urgencias, contratos, etc.).

Está hecho en **Flask** (no FastAPI) a propósito, para que corra bien en hosting compartido
tipo cPanel con Passenger.

## 1. Requisitos

- Una clave de API de Anthropic (para las respuestas con IA) — se obtiene en console.anthropic.com.
- El número de WhatsApp ya dado de alta en Meta for Developers (Phone Number ID, token de acceso).
- Acceso a tu cPanel con la opción **"Setup Python App"** (a veces llamada "Python Selector") —
  la mayoría de los hostings modernos la traen. Si no la ves, revisa con tu proveedor de hosting
  si está disponible o si hay que activarla.

## 2. Probar en tu computador primero (opcional pero recomendado)

```bash
cd whatsapp-bot
python3 -m venv venv
source venv/bin/activate      # en Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Completa `.env` (ver sección 4) y corre:

```bash
python3 server.py
```

Para que Meta pueda llamar a tu servidor local necesitas exponerlo con
[ngrok](https://ngrok.com/download): `ngrok http 8000`, y usar esa URL temporal en el
webhook de Meta (ver sección 5). Esto es solo para probar antes de subirlo al hosting definitivo.

## 3. Subir el proyecto a tu hosting (cPanel)

1. Sube la carpeta `whatsapp-bot` completa a tu hosting — por File Manager de cPanel, o por FTP/SFTP.
   Puede ir en una subcarpeta o en un subdominio, por ejemplo `bot.icrb.cl` o `icrb.cl/whatsapp-bot`.
2. En cPanel, busca **"Setup Python App"**.
3. Haz clic en **"Create Application"**:
   - **Python version**: la más reciente disponible (3.10 o superior).
   - **Application root**: la carpeta donde subiste el proyecto (ej: `whatsapp-bot`).
   - **Application URL**: el subdominio o subcarpeta que quieras usar para el webhook.
   - **Application startup file**: `passenger_wsgi.py` (ya viene incluido en el proyecto).
   - **Application Entry point**: `application` (así se llama la variable dentro de `passenger_wsgi.py`).
4. Cuando la app quede creada, cPanel te va a mostrar un comando tipo:
   `source /home/tuusuario/virtualenv/whatsapp-bot/3.x/bin/activate && cd /home/tuusuario/whatsapp-bot`
   Ejecútalo en la Terminal de cPanel (o conéctate por SSH) y luego corre:
   ```bash
   pip install -r requirements.txt
   ```
5. En la misma pantalla de "Setup Python App" hay una sección de **"Environment variables"**:
   ahí agregas, una por una, las variables que están en `.env.example`
   (`WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN`, `ANTHROPIC_API_KEY`,
   `ADMIN_WHATSAPP_NUMBER`) con sus valores reales. No hace falta el archivo `.env` en el hosting
   si las cargas ahí (Passenger las deja disponibles igual).
6. Guarda y reinicia la app (botón "Restart") desde el mismo panel.
7. Prueba que responde entrando a `https://tu-dominio-o-subcarpeta/webhook` desde el navegador
   (te debería dar un error 403, lo cual es correcto — significa que el servidor está vivo y
   validando el token, como corresponde).

## 4. Completar las variables de entorno

- `WHATSAPP_TOKEN`: el token de acceso de tu app en Meta for Developers.
  Si estás con el número de prueba, dura 24 horas — genera uno nuevo cuando expire.
  Cuando pases a un número real con un token permanente, este paso deja de ser necesario cada día.
- `WHATSAPP_PHONE_NUMBER_ID`: el ID que aparece junto a tu número en el panel de Meta.
- `WHATSAPP_VERIFY_TOKEN`: invéntate una palabra (ej: `crb-ing-2026`) — la vuelves a usar en el paso 5.
- `ANTHROPIC_API_KEY`: tu clave de Anthropic.
- `ADMIN_WHATSAPP_NUMBER` (opcional): tu número, para que el bot te avise cuando derive una conversación.

## 5. Conectar el webhook en Meta

En el panel de Meta for Developers, dentro de tu app → WhatsApp → Configuración:

1. Busca la sección **Webhook** → "Editar".
2. **Callback URL**: la URL pública de tu app en el hosting + `/webhook`
   (ej: `https://bot.icrb.cl/webhook`).
3. **Verify token**: el mismo valor que pusiste en `WHATSAPP_VERIFY_TOKEN`.
4. Guarda — Meta hace una llamada de verificación automática.
5. Suscríbete al campo **messages** (dentro de "Webhook fields" / "Administrar").

Si estás con el número de prueba, recuerda agregar tu celular como "destinatario de prueba"
en el panel de Meta (sección del número de prueba) para poder recibir sus respuestas.

## 6. Probar

Desde WhatsApp, escribe al número conectado. Prueba con:

- "hola" → responde la IA (saludo).
- "¿cuál es su horario?" → respuesta fija de horario.
- "¿qué servicios ofrecen?" → respuesta fija de servicios.
- "quiero hablar con un asesor" → mensaje de derivación (y aviso a `ADMIN_WHATSAPP_NUMBER` si lo configuraste).
- Un mensaje fuera del horario de `config.py` → mensaje de "fuera de horario".

Si algo no responde, revisa los logs de la app en cPanel (dentro de "Setup Python App" suele haber
un botón o sección de logs) para ver el error exacto.

## 7. Chat widget en el sitio web (crb.icrb.cl)

Además de responder por WhatsApp, este mismo servidor expone un endpoint `/chat` que usa
exactamente las mismas reglas e IA, pero pensado para un cuadro de chat dentro de la página web
(no requiere que el visitante tenga WhatsApp).

1. El archivo `crb-web/js/chat-widget.js` ya está agregado a todas las páginas del sitio.
   Ábrelo y edita esta línea con la URL real donde quede tu bot:
   ```js
   var CHAT_API_URL = "https://bot.icrb.cl/chat"; // <-- cambia esto
   ```
2. En `server.py`, la lista `CORS(...)` debe incluir el dominio exacto desde donde se va a llamar
   al chat (por defecto ya tiene `https://crb.icrb.cl`, `https://icrb.cl` y `https://www.icrb.cl`).
   Si usas otro dominio o subdominio, agrégalo ahí.
3. Sube de nuevo `chat-widget.js` (y el resto del sitio si hiciste otros cambios) a tu hosting,
   y reinicia la app del bot en "Setup Python App" para que tome el cambio del `server.py`.
4. El chat aparece como una burbuja azul flotante (arriba del botón verde de WhatsApp) en todas
   las páginas del sitio.

Nota: como es un endpoint público llamado desde el navegador, cualquiera que abra tu web puede
usarlo — está pensado igual que el bot de WhatsApp (reglas fijas + IA + derivación), no expone
tus credenciales (el token de WhatsApp y la clave de Anthropic quedan solo en el servidor).

## 8. Ajustar textos y reglas

Todo lo editable está en `config.py`:

- `BUSINESS_HOURS`: horario de atención por día de la semana.
- `COMPANY_INFO`: la información que la IA usa como base para responder preguntas abiertas.
- `FIXED_REPLIES`: palabras clave → respuesta fija (agrega o cambia las que quieras).
- `ESCALATION_KEYWORDS`: palabras que siempre derivan a un asesor humano sin pasar por la IA.

Después de editar, vuelve a hacer clic en "Restart" en "Setup Python App" para que tome los cambios.

## 9. Pasar al número real de WhatsApp

Cuando tengas tu número real dado de alta (ver `guia-activar-whatsapp-business-api.md`):

1. Genera un **token de acceso permanente** (creando un "usuario del sistema" en Meta Business Suite).
2. Reemplaza `WHATSAPP_TOKEN` y `WHATSAPP_PHONE_NUMBER_ID` en las variables de entorno del hosting.
3. Ya no habrá restricción de "destinatarios de prueba": el bot podrá responder a cualquier cliente.
