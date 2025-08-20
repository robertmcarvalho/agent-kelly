import os
def get_pipefy_link() -> dict:
    return {"pipefy_url": os.getenv("PIPEFY_URL", "https://app.pipefy.com")}
