import os, logging, requests
from typing import Optional
from fastapi import FastAPI, Request, Response
from agent.runner import run_agent
from fastapi import Query

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
def verify(
    mode: str = Query(..., alias="hub.mode"),
    challenge: str = Query(..., alias="hub.challenge"),
    token: str = Query(..., alias="hub.verify_token")
):
    if mode == "subscribe" and token == VERIFY_TOKEN:
        log.info("Webhook verificado com sucesso!")
        return Response(content=challenge, media_type="text/plain")
    log.warning("Falha na verificação do Webhook. Token recebido: '%s' | Token esperado (início): '%s...'", token, VERIFY_TOKEN[:4])
    return Response(content="Falha na verificação do token", status_code=403)

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
    contacts = value.get("contacts") or []
    from_id = None
    name = None
    if contacts:
        first_contact = contacts[0]
        from_id = msg.get("from") or first_contact.get("wa_id")
        name = (first_contact.get("profile") or {}).get("name")
    else:
        from_id = msg.get("from") or None
    text_in = None

    if msg.get("type") == "text":
        text_in = msg["text"]["body"]
    elif msg.get("type") == "interactive":
        interactive = msg.get("interactive", {})
        if interactive.get("type") == "list_reply":
            lr = interactive["list_reply"]
            if lr.get("id","").startswith("vaga:"):
                text_in = f"selecionar_vaga {lr['id'].split(':',1)[1]}"
            else:
                text_in = lr.get("title") or "Seleção da lista recebida"
        elif interactive.get("type") == "button_reply":
            text_in = interactive["button_reply"].get("title") or "Botão selecionado"
    elif msg.get("type") == "audio":
        # opcional: aqui você pode baixar e transcrever com agent.tools.audio.transcribe_media_id
        text_in = "Recebi seu áudio. (Transcrição não configurada nesta rota)"
    else:
        text_in = "Olá"

    if name:
        text_in = f"(Nome: {name}) {text_in}"

    output = run_agent(user_id=from_id, wa_id=from_id, text=text_in)

    # A resposta ao usuário é enviada pelas ferramentas do agente (ex: whatsapp.send_text).
    # O 'output' do agente é apenas para logging e debug.
    return {"ok": True, "preview": (output or "")[:200]}
