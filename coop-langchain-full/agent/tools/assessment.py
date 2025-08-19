from typing import Dict, Any
QUESTOES = [
  {"id":"pontualidade","pergunta":"Chega no horário diariamente? (sempre/às vezes/raramente)"},
  {"id":"epi_uniforme","pergunta":"Usa uniforme e bag conforme padrão? (sim/não)"},
  {"id":"rotas_app","pergunta":"Segue rotas no app e usa chat? (sim/não/parcial)"},
  {"id":"finais_semana","pergunta":"Disponível ao menos um turno no fim de semana? (sim/não)"},
  {"id":"boas_praticas","pergunta":"Avisa atrasos com antecedência? (sempre/às vezes/nunca)"}
]
MAPA={"sim":2,"sempre":2,"às vezes":1,"as vezes":1,"parcial":1,"não":0,"nao":0,"raramente":0,"nunca":0}
LIMIAR=7

def start_assessment() -> Dict[str, Any]:
    return {"perguntas": QUESTOES}

def score_assessment(respostas: Dict[str,str]) -> Dict[str,Any]:
    total=0; detalhado=[]
    for q in QUESTOES:
        rid=q["id"]; txt=(respostas.get(rid,"") or "").strip().lower(); pts=MAPA.get(txt,0)
        detalhado.append({"id":rid,"resposta":txt,"pontos":pts}); total+=pts
    return {"total":total,"aprovado": total>=LIMIAR, "limiar":LIMIAR, "detalhado":detalhado}
