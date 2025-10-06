from utils.crypto import fernet_from, encrypt, decrypt
from infra.repos.connections_interfaces import ConnectionsRepo
from infra.memory.connections_repo import MemoryConnectionsRepo


def test_connections_memory_roundtrip():
    repo: ConnectionsRepo = MemoryConnectionsRepo()
    f, key_used = fernet_from(None)
    enc = encrypt(f, "token123")
    repo.upsert("t1", "notion", enc, None, {"k": "v"})
    row = repo.get("t1", "notion")
    assert row and row["access_token_encrypted"] == enc


