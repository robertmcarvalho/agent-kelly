import os, logging, requests
from typing import List

log = logging.getLogger(__name__)
WA_TOKEN = os.getenv("WHATSAPP_TOKEN")
WA_PHONE_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

def _send_request(payload: dict):
    """Função auxiliar para enviar requisições à API do WhatsApp."""
    if not WA_TOKEN or not WA_PHONE_ID:
        log.warning("WhatsApp tokens não configurados. Pulando envio.")
        # Retorna um texto para o agente saber que não foi enviado
        return {"status": "no_credentials", "sent": False, "response_text": "O envio de mensagem não está configurado."}
    try:
        url = f"https://graph.facebook.com/v20.0/{WA_PHONE_ID}/messages"
        headers = {"Authorization": f"Bearer {WA_TOKEN}", "Content-Type": "application/json"}
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        log.info("Mensagem enviada com sucesso para %s", payload.get("to"))
        return {"status": "ok", "sent": True, "response_text": "Mensagem com botões enviada."}
    except Exception as e:
        log.exception("Falha ao enviar WhatsApp: %s", e)
        return {"status": "error", "sent": False, "error": str(e), "response_text": f"Erro ao enviar mensagem: {e}"}

def send_text(to: str, body: str) -> dict:
    """Envia uma mensagem de texto simples."""
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": body[:4096]}}
    return _send_request(payload)

def send_buttons(to: str, body: str, buttons: List[str]) -> dict:
    """Envia uma mensagem com até 3 botões de resposta rápida."""
    actions = [{"type": "reply", "reply": {"id": f"btn_{i}", "title": btn}} for i, btn in enumerate(buttons[:3])]
    payload = {
        "messaging_product": "whatsapp", "to": to, "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body},
            "action": {"buttons": actions}
        }
    }
    return _send_request(payload)

def send_vagas_list(to: str, vagas: list) -> dict:
    """Envia uma lista interativa com as vagas."""
    rows = [{"id": f"vaga:{v.get('id_vaga')}", "title": v.get("farmacia"), "description": f"{v.get('turno')} | {v.get('taxa_entrega')}"} for v in vagas[:10]]
    payload = {
        "messaging_product": "whatsapp", "to": to, "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "Vagas Disponíveis"},
            "body": {"text": "Selecione uma das vagas abaixo para continuar."},
            "action": {"button": "Ver Vagas", "sections": [{"title": "Escolha uma opção", "rows": rows}]}
        }
    }
    return _send_request(payload)