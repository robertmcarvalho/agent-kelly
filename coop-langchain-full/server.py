import os, logging
from typing import Optional
from fastapi import FastAPI, Request, Response, Query

# ----------------------------
# Logging
# ----------------------------
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL)
log = logging.getLogger("server")

# ----------------------------
# Env vars
# ----------------------------
VERIFY_TOKEN = (
    os.getenv("WHATSAPP_VERIFY_TOKEN")
    or os.getenv("WA_VERIFY_TOKEN")  # alias de compatibilidade
    or "verify-me"
)
WA_TOKEN = os.getenv("WHATSAPP_TOKEN")
WA_PHONE_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

# ----------------------------
# App
# ----------------------------
app = FastAPI(title="Coop LangChain Bot")

@app.get("/healthz")
def healthz():
    return {"ok": True}

# ----------------------------
# Webhook verification (GET)
# Aceita /webhook e /webhook/ (opcionalmente /wa/webhook também)
# ----------------------------
@app.get("/webhook")
@app.get("/webhook/")
# descomente as duas linhas abaixo se quiser também /wa/webhook
# @app.get("/wa/webhook")
# @app.get("/wa/webhook/")
def verify(
    mode: str = Query(..., alias="hub.mode"),
    challenge: str = Query(..., alias="hub.challenge"),
    token: str = Query(..., alias="hub.verify_token"),
):
    if mode == "subscribe" and token == VERIFY_TOKEN:
        log.info("Webhook verificado com sucesso!")
        return Response(content=challenge, media_type="text/plain", status_code=200)
    log.warning(
        "Falha na verificação do Webhook. Token recebido: '%s' | Token esperado (início): '%s...'",
        token, (VERIFY_TOKEN or "")[:4]
    )
    return Response(content="Falha na verificação do token", status_code=403)

# ----------------------------
# Lazy import para evitar crash no startup
# ----------------------------
def _lazy_run_agent(*args, **kwargs):
    try:
        from agent.runner import run_agent  # importa somente quando necessário
    except Exception as e:
        log.exception("Falha ao importar agent.runner.run_agent: %s", e)
        return "AGENT_IMPORT_ERROR"
    try:
        return run_agent(*args, **kwargs)
    except Exception as e:
        log.exception("Erro ao executar run_agent: %s", e)
        return "AGENT_RUNTIME_ERROR"

# ----------------------------
# Webhook receiver (POST)
# Aceita /webhook e /webhook/ (opcionalmente /wa/webhook também)
# ----------------------------
@app.post("/webhook")
@app.post("/webhook/")
# descomente as duas linhas abaixo se quiser também /wa/webhook
# @app.post("/wa/webhook")
# @app.post("/wa/webhook/")
async def webhook(request: Request):
    try:
        body = await request.json()
    except Exception:
        return {"status": "invalid_json"}

    try:
        value = body["entry"][0]["changes"][0]["value"]
    except Exception:
        return {"status": "ignored"}

    messages = value.get("messages", [])
    if not messages:
        return {"status": "no_messages"}

    msg = messages[0]
    from_id = msg.get("from") or (value.get("contacts", [{}])[0].get("wa_id"))
    name = (value.get("contacts", [{}])[0].get("profile", {}) or {}).get("name")
    text_in: Optional[str] = None

    msg_type = msg.get("type")
    if msg_type == "text":
        text_in = msg["text"]["body"]
    elif msg_type == "interactive":
        interactive = msg.get("interactive", {}) or {}
        itype = interactive.get("type")
        if itype == "list_reply":
            lr = interactive.get("list_reply", {}) or {}
            lrid = lr.get("id", "")
            if lrid.startswith("vaga:"):
                text_in = f"selecionar_vaga {lrid.split(':', 1)[1]}"
            else:
                text_in = lr.get("title") or "Seleção da lista recebida"
        elif itype == "button_reply":
            br = interactive.get("button_reply", {}) or {}
            text_in = br.get("title") or "Botão selecionado"
        else:
            text_in = "Interação recebida"
    elif msg_type == "audio":
        # ponto de extensão para transcrição
        text_in = "Recebi seu áudio. (Transcrição não configurada nesta rota)"
    else:
        text_in = "Olá"

    if name:
        text_in = f"(Nome: {name}) {text_in}"

    output = _lazy_run_agent(user_id=from_id, wa_id=from_id, text=text_in)

    # Resposta ao usuário é enviada pelas ferramentas do agente (ex.: whatsapp.send_text)
    return {"ok": True, "preview": (output or "")[:200]}
