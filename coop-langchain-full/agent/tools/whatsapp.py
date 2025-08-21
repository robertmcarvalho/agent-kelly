import os, requests
from .telemetry import timeit, log_event

WA_TOKEN=os.getenv("WHATSAPP_TOKEN")
WA_PHONE_ID=os.getenv("WHATSAPP_PHONE_NUMBER_ID")

def _endpoint(path: str)->str: return f"https://graph.facebook.com/v20.0/{path}"

def send_text(to: str, body: str)->dict:
    if not (WA_TOKEN and WA_PHONE_ID): return {"sent": False, "reason": "missing_whatsapp_env"}
    url=_endpoint(f"{WA_PHONE_ID}/messages")
    payload={"messaging_product":"whatsapp","to":to,"type":"text","text":{"body": (body or "")[:4096]}}
    with timeit("wa_send_text"):
        try:
            r=requests.post(url, headers={"Authorization": f"Bearer {WA_TOKEN}","Content-Type":"application/json"}, json=payload, timeout=30)
        except requests.RequestException as e:
            log_event("wa.send_text", ok=False, error=str(e))
            return {"sent": False, "reason": "request_error"}
    ok = r.status_code<300
    log_event("wa.send_text", ok=ok, status=r.status_code)
    return {"sent": ok, "status": r.status_code}

def send_vagas_list(to: str, vagas: list, title: str="Vagas Abertas", prompt: str="Escolha uma vaga")->dict:
    if not (WA_TOKEN and WA_PHONE_ID): return {"sent": False, "reason": "missing_whatsapp_env"}
    rows=[]
    for v in vagas[:10]:
        rid=f"vaga:{v.get('id_vaga')}"
        ttl=f"{v.get('farmacia','?')} — {v.get('turno','?')}"
        desc=f"Taxa {v.get('taxa_entrega','?')}"
        rows.append({"id": rid, "title": ttl[:24] or "Vaga", "description": desc[:72]})
    payload={"messaging_product":"whatsapp","to":to,"type":"interactive",
        "interactive":{"type":"list","body":{"text":prompt[:1024]},"action":{"button":"Ver vagas","sections":[{"title":title[:24] or "Vagas","rows":rows}]}}}
    url=_endpoint(f"{WA_PHONE_ID}/messages")
    with timeit("wa_send_list"):
        try:
            r=requests.post(url, headers={"Authorization": f"Bearer {WA_TOKEN}","Content-Type":"application/json"}, json=payload, timeout=30)
        except requests.RequestException as e:
            log_event("wa.send_list", ok=False, error=str(e), rows=len(rows))
            return {"sent": False, "reason": "request_error"}
    ok = r.status_code<300
    log_event("wa.send_list", ok=ok, status=r.status_code, rows=len(rows))
    return {"sent": ok, "status": r.status_code}

def send_buttons(to: str, body: str, buttons: list)->dict:
    if not (WA_TOKEN and WA_PHONE_ID): return {"sent": False, "reason": "missing_whatsapp_env"}
    acts=[]
    for i, b in enumerate(buttons[:3]):
        acts.append({"type":"reply","reply":{"id":f"btn_{i}","title":b[:20] or "..."}})
    payload={"messaging_product":"whatsapp","to":to,"type":"interactive",
        "interactive":{"type":"button","body":{"text":body[:1024]},"action":{"buttons":acts}}}
    url=_endpoint(f"{WA_PHONE_ID}/messages")
    with timeit("wa_send_buttons"):
        try:
            r=requests.post(url, headers={"Authorization": f"Bearer {WA_TOKEN}","Content-Type":"application/json"}, json=payload, timeout=30)
        except requests.RequestException as e:
            log_event("wa.send_buttons", ok=False, error=str(e), buttons=len(acts))
            return {"sent": False, "reason": "request_error"}
    ok = r.status_code<300
    log_event("wa.send_buttons", ok=ok, status=r.status_code, buttons=len(acts))
    return {"sent": ok, "status": r.status_code}
