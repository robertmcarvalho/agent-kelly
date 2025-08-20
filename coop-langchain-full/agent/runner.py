import os
from typing import Dict
# Corrigido: import de langchain_core, que é o local correto para StructuredTool
from langchain_core.tools import StructuredTool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from agent.prompts import SYSTEM_PROMPT
from agent.tools import sheets, assessment, requirements, whatsapp, pipefy, memory

# ==== Schemas ====
class CityIn(BaseModel):
    cidade: str = Field(..., description="Cidade do entregador")

class GetByIdIn(BaseModel):
    id_vaga: str

class SaveLeadIn(BaseModel):
    lead_nome: str
    whatsapp: str
    cidade: str
    aprovado: bool
    vaga_escolhida: str | None = None
    farmacia: str | None = None
    turno: str | None = None
    taxa_entrega: str | None = None
    observacoes: str | None = None

class RequirementsIn(BaseModel):
    moto_ok: bool
    cnh_categoria_a: bool
    android_ok: bool

class ScoreIn(BaseModel):
    respostas: Dict[str, str]

class SendTextIn(BaseModel):
    to: str
    body: str

class SendListIn(BaseModel):
    to: str
    vagas: list

class SendButtonsIn(BaseModel):
    to: str
    body: str
    buttons: list[str] = Field(..., description="Lista de textos para os botões (máximo 3).")

# ==== Tools ====
tools = [
    StructuredTool.from_function(sheets.get_coop_info, name="get_coop_info", description="Info da cooperativa"),
    StructuredTool.from_function(sheets.get_open_positions, name="get_open_positions", description="Vagas por cidade", args_schema=CityIn),
    StructuredTool.from_function(sheets.get_position_by_id, name="get_position_by_id", description="Buscar vaga por id", args_schema=GetByIdIn),
    StructuredTool.from_function(sheets.save_lead, name="save_lead", description="Salvar lead na planilha", args_schema=SaveLeadIn),
    StructuredTool.from_function(requirements.check_requirements, name="check_requirements", description="Verificar requisitos", args_schema=RequirementsIn),
    StructuredTool.from_function(assessment.start_assessment, name="start_assessment", description="Inicia avaliação"),
    StructuredTool.from_function(assessment.score_assessment, name="score_assessment", description="Pontua avaliação", args_schema=ScoreIn),
    StructuredTool.from_function(whatsapp.send_text, name="send_text", description="Enviar WhatsApp texto", args_schema=SendTextIn),
    StructuredTool.from_function(whatsapp.send_vagas_list, name="send_vagas_list", description="Enviar lista interativa de vagas", args_schema=SendListIn),
    StructuredTool.from_function(whatsapp.send_buttons, name="send_buttons", description="Enviar mensagem com botões de resposta rápida.", args_schema=SendButtonsIn),
    StructuredTool.from_function(pipefy.get_pipefy_link, name="get_pipefy_link", description="Obter link do Pipefy"),
]

def _prompt():
    return f"""<SYSTEM>
{SYSTEM_PROMPT}
Instruções adicionais:
- Sempre mantenha o texto final ≤ 4096 caracteres.
- Para enviar WhatsApp, use send_text/send_vagas_list com to = state['user:wa_id'].
- Se o usuário enviar 'selecionar_vaga <ID>', busque com get_position_by_id, confirme e salve com save_lead.
</SYSTEM>"""

def build_agent() -> AgentExecutor:
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GENAI_MODEL", "gemini-2.0-flash"),
        api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.2,
    )
    prompt = _prompt()
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=False, handle_parsing_errors=True)

AGENT_EXECUTOR = build_agent()

def run_agent(user_id: str, wa_id: str | None, text: str) -> str:
    state = memory.load(user_id) or {}
    if wa_id: state["user:wa_id"] = wa_id

    inputs = {"input": text, "state": state}
    result = AGENT_EXECUTOR.invoke(inputs)
    memory.save(user_id, state)
    return (result.get("output") or "")[:4096]
