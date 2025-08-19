import json, os
from upstash_redis import Redis

TTL = int(os.getenv("REDIS_TTL_SECONDS", "432000") or "432000")
URL = os.getenv("UPSTASH_REDIS_REST_URL", "")
TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
redis = Redis(url=URL, token=TOKEN) if URL and TOKEN else None

def _k(uid: str) -> str: return f"coop_agent:user:{uid}"

def load(uid: str) -> dict:
    if not redis: return {}
    v = redis.get(_k(uid))
    try:
        return json.loads(v) if v else {}
    except Exception:
        return {}

def save(uid: str, d: dict) -> None:
    if not redis: return
    redis.set(_k(uid), json.dumps(d, ensure_ascii=False), ex=TTL)
