import json
import importlib
import sys
import types
from pathlib import Path

from fastapi.testclient import TestClient


PAYLOAD_DIR = Path(__file__).parent / "payloads"


class DummyResponse:
    def raise_for_status(self) -> None:  # pragma: no cover - simple stub
        pass


def load_payload(filename: str) -> dict:
    return json.loads((PAYLOAD_DIR / filename).read_text())


def make_client(monkeypatch, agent_output: str) -> TestClient:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    # Ensure repository root is in sys.path for `import server`
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    # Provide a stub implementation of agent.runner before importing server
    fake_runner = types.ModuleType("agent.runner")
    fake_runner.run_agent = lambda *_, **__: agent_output
    sys.modules["agent.runner"] = fake_runner
    sys.modules.pop("server", None)
    server = importlib.import_module("server")
    # Mock requests.post to avoid network calls
    monkeypatch.setattr(server.requests, "post", lambda *_, **__: DummyResponse())
    return TestClient(server.app)


def test_webhook_text(monkeypatch):
    client = make_client(monkeypatch, "Agente: texto")
    payload = load_payload("whatsapp_text.json")
    resp = client.post("/webhook", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"ok": True, "preview": "Agente: texto"}


def test_webhook_list_reply(monkeypatch):
    client = make_client(monkeypatch, "Agente: listagem")
    payload = load_payload("whatsapp_list_reply.json")
    resp = client.post("/webhook", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"ok": True, "preview": "Agente: listagem"}
