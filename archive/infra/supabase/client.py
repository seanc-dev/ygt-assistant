import httpx
from settings import SUPABASE_URL, SUPABASE_SERVICE_KEY


def client() -> httpx.Client:
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise RuntimeError("Supabase not configured")
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
    }
    transport = httpx.HTTPTransport(retries=1)
    return httpx.Client(
        base_url=f"{SUPABASE_URL}/rest/v1",
        headers=headers,
        timeout=httpx.Timeout(4.0, connect=2.0, read=4.0, write=4.0),
        transport=transport,
    )
