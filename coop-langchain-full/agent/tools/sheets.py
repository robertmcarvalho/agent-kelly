import os, json
from typing import Dict, Any, Optional
from google.oauth2.service_account import Credentials
import gspread
from .utils import iso_now

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SA_JSON = os.getenv("SA_JSON")

def _gc():
    if SA_JSON:
        info = json.loads(SA_JSON); creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        from google.auth import default
        creds, _ = default(scopes=SCOPES)
    return gspread.authorize(creds)

def get_coop_info() -> Dict[str, Any]:
    import yaml, os
    base = os.path.dirname(os.path.dirname(__file__))
    path = os.path.join(base, "..", "config", "coop.yaml")
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    texto = f"Cooperativa: {cfg.get('nome','(nome)')}\n"
    if cfg.get("cota"): texto += f"- Cota: {cfg['cota']}\n"
    if cfg.get("uniforme_bag"): texto += f"- Uniforme/Bag: {cfg['uniforme_bag']}\n"
    if cfg.get("beneficios"): texto += f"- Benefícios: {cfg['beneficios']}\n"
    return {"text": texto.strip(), "mensagens": cfg.get("mensagens", {}), "raw": cfg}

def get_open_positions(cidade: str) -> Dict[str, Any]:
    gc = _gc(); sh = gc.open_by_key(SPREADSHEET_ID); ws = sh.worksheet("Vagas"); recs = ws.get_all_records()
    c = (cidade or "").strip().lower()
    rows=[{"id_vaga":r.get("id_vaga"),"farmacia":r.get("farmacia"),"cidade":r.get("cidade"),
           "turno":r.get("turno"),"taxa_entrega":r.get("taxa_entrega"),"status":r.get("status")}
           for r in recs if str(r.get("status","")).strip().lower()=="aberto" and c in str(r.get("cidade","")).strip().lower()]
    return {"vagas": rows}

def get_position_by_id(id_vaga: str) -> Dict[str, Any]:
    gc = _gc(); sh = gc.open_by_key(SPREADSHEET_ID); ws = sh.worksheet("Vagas"); recs = ws.get_all_records()
    for r in recs:
        if str(r.get("id_vaga")) == str(id_vaga):
            return {"vaga": {"id_vaga": r.get("id_vaga"),"farmacia": r.get("farmacia"),"cidade": r.get("cidade"),
                             "turno": r.get("turno"),"taxa_entrega": r.get("taxa_entrega"),"status": r.get("status")}}
    return {"vaga": None}

def save_lead(lead_nome: Optional[str], whatsapp: Optional[str], cidade: Optional[str], aprovado: Optional[bool],
              vaga_escolhida: Optional[str], farmacia: Optional[str]=None, turno: Optional[str]=None,
              taxa_entrega: Optional[str]=None, observacoes: Optional[str]=None) -> Dict[str, Any]:
    gc = _gc(); sh = gc.open_by_key(SPREADSHEET_ID)
    try:
        ws = sh.worksheet("Leads")
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title="Leads", rows=2000, cols=20)
        ws.append_row(["timestamp_iso","lead_nome","whatsapp","cidade","aprovado","id_vaga_escolhida",
                       "farmacia_escolhida","turno","taxa_entrega","observacoes"])
    row=[iso_now(), lead_nome or "", whatsapp or "", cidade or "", "TRUE" if aprovado else "FALSE",
         vaga_escolhida or "", farmacia or "", turno or "", taxa_entrega or "", observacoes or ""]
    ws.append_row(row)
    return {"status":"ok","saved": True}
