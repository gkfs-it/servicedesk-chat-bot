import json
from pathlib import Path

_AUTH_FILE = Path("authenticated_users.json")

_authenticated: set[int] = set()


def _load() -> None:
    if _AUTH_FILE.exists():
        try:
            data = json.loads(_AUTH_FILE.read_text())
            _authenticated.update(data)
        except (json.JSONDecodeError, TypeError):
            pass


def _save() -> None:
    _AUTH_FILE.write_text(json.dumps(list(_authenticated)))


def is_authenticated(user_id: int) -> bool:
    return user_id in _authenticated


def authenticate(user_id: int) -> None:
    _authenticated.add(user_id)
    _save()


_load()
