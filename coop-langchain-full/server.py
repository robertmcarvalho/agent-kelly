import os, logging, requests
from typing import Optional
from fastapi import FastAPI, Request, Response
from agent.runner import run_agent

LOG_LEVEL = os.getenv("LOG_LEVEL","INFO").upper()
logging.basicConfig(level=LOG_LEVEL)
log = logging.getLogger("server")

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "verify-me")
WA_TOKEN = os.getenv("WHATSAPP_TOKEN")
WA_PHONE_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

app = FastAPI(title="Coop LangChain Bot")

@app.get("/healthz")
def healthz(): 
    return {"ok": True}

@app.get("/webhook")
def verify(mode: Optional[str] = None, hub_mode: Optional[str] = None, hub_challenge: Optional[str] = None, hub_verify_token: Optional[str] = None, **kw):
    mode = mode or hub_mode
    token = hub_verify_token or kw.get("hub.verify_token")
    challenge = hub_challenge or kw.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge or "", media_type="text/plain")
    return Response(status_code=403)

@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    try:
        value = body["entry"][0]["changes"][0]["value"]
    except Exception:
        return {"status":"ignored"}

    messages = value.get("messages", [])
    if not messages:
        return {"status":"no_messages"}

    msg = messages[0]
    from_id = msg.get("from") or (value.get("contacts", [{}])[0].get("wa_id"))
    name = (value.get("contacts", [{}])[0].get("profile", {}) or {}).get("name")
    text_in = None

    if msg.get("type") == "text":
        text_in = msg["text"]["body"]
    elif msg.get("type") == "interactive" and msg.get("interactive", {}).get("type") == "list_reply":
        lr = msg["interactive"]["list_reply"]
        if lr.get("id","").startswith("vaga:"):
            text_in = f"selecionar_vaga {lr['id'].split(':',1)[1]}"
        else:
            text_in = lr.get("title") or "Seleção recebida"
    elif msg.get("type") == "audio":
        # opcional: aqui você pode baixar e transcrever com agent.tools.audio.transcribe_audio_url
        text_in = "Recebi seu áudio. (Transcrição não configurada nesta rota)"
    else:
        text_in = "Olá"

    if name:
        text_in = f"(Nome: {name}) {text_in}"

    output = run_agent(user_id=from_id, wa_id=from_id, text=text_in)

    # resposta via WhatsApp (opcional)
    if WA_TOKEN and WA_PHONE_ID and from_id:
        try:
            url = f"https://graph.facebook.com/v20.0/{WA_PHONE_ID}/messages"
            payload = {"messaging_product":"whatsapp","to":from_id,"type":"text","text":{"body":output[:4096]}}
            r = requests.post(url, headers={"Authorization": f"Bearer {WA_TOKEN}","Content-Type":"application/json"}, json=payload, timeout=30)
            r.raise_for_status()
        except Exception as e:
            log.exception("Falha ao enviar WhatsApp: %s", e)

    return {"ok": True, "preview": (output or "")[:200]}
