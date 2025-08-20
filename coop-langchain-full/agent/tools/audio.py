import os, requests
from google import genai
from google.genai import types

MODEL = os.getenv("GENAI_MODEL", "gemini-2.0-flash")

def _client():
    api_key=os.getenv("GOOGLE_API_KEY")
    if not api_key: raise RuntimeError("GOOGLE_API_KEY não definido.")
    return genai.Client(api_key=api_key)

def transcribe_audio_url(url: str, mime_type: str="audio/mpeg")->dict:
    r = requests.get(url, timeout=60); r.raise_for_status()
    client=_client()
    parts=[types.Part.from_bytes(data=r.content, mime_type=mime_type), types.Part.from_text("Transcreva em pt-BR.")]
    resp=client.models.generate_content(model=MODEL, contents=[types.Content(role="user", parts=parts)])
    return {"transcript": resp.text or ""}
