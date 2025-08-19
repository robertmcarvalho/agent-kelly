# Coop Bot — LangChain + Gemini + FastAPI + WhatsApp + Sheets

Pronto para Cloud Run. Agente em LangChain com ferramentas (Sheets, WhatsApp, Pipefy, avaliação, requisitos) e memória (Upstash) por 5 dias.

## Rodar local
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env   # preencha variáveis
uvicorn server:app --reload --port 8000
curl.exe http://localhost:8000/healthz
```

### Simular webhook WhatsApp
```powershell
curl.exe -X POST http://localhost:8000/webhook -H "Content-Type: application/json" --data-binary "@tests\payloads\whatsapp_text.json"
```

## Deploy (Cloud Run)
```bash
gcloud run deploy coop-langchain-bot --source=. --region=us-central1       --allow-unauthenticated       --set-env-vars=GOOGLE_API_KEY=***,GENAI_MODEL=gemini-2.0-flash,SPREADSHEET_ID=***,UPSTASH_REDIS_REST_URL=***,UPSTASH_REDIS_REST_TOKEN=***,REDIS_TTL_SECONDS=432000,WHATSAPP_VERIFY_TOKEN=***,WHATSAPP_TOKEN=***,WHATSAPP_PHONE_NUMBER_ID=***,PIPEFY_URL=***,LOG_LEVEL=INFO
```

## Estrutura
```
.
├─ server.py
├─ agent/
│  ├─ runner.py
│  ├─ prompts.py
│  └─ tools/
│     ├─ memory.py  (Upstash)
│     ├─ sheets.py   (Google Sheets)
│     ├─ assessment.py
│     ├─ requirements.py
│     ├─ whatsapp.py
│     ├─ pipefy.py
│     ├─ audio.py    (transcrição opcional)
│     ├─ telemetry.py
│     └─ utils.py
├─ config/coop.yaml
├─ tests/payloads/
├─ scripts/
└─ requirements.txt
```
