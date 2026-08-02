#!/usr/bin/env python3
"""Generate signed Telegram Mini App `initData` strings for local dev.

Signs against TELEGRAM_BOT_TOKEN from the repo-root `.env` (see
`docker-compose.yml`), matching the HMAC scheme backend verifies in
`backend/src/unitkeeper_backend/infrastructure/auth/telegram.py`.

Usage:
    uv run --project backend python scripts/dev/gen_init_data.py
    # or just: python3 scripts/dev/gen_init_data.py  (stdlib only)

Prints two ready-to-use `VITE_DEV_INIT_DATA` values, one per dev user.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from pathlib import Path
from urllib.parse import quote, urlencode

ROOT = Path(__file__).resolve().parents[2]

# Fixed dev user ids so re-running this script is idempotent (same account
# each time -- convenient for repeated manual testing).
DEV_USERS = [
    {"id": 900000001, "first_name": "Alex", "username": "alex_dev", "language_code": "ru"},
    {"id": 900000002, "first_name": "Mia", "username": "mia_dev", "language_code": "ru"},
]


def load_bot_token() -> str:
    env_path = ROOT / ".env"
    for line in env_path.read_text().splitlines():
        if line.startswith("TELEGRAM_BOT_TOKEN="):
            return line.split("=", 1)[1].strip()
    raise SystemExit(f"TELEGRAM_BOT_TOKEN not found in {env_path}")


def sign(bot_token: str, pairs: dict[str, str]) -> str:
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    return hmac.new(secret, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()


def build_init_data(bot_token: str, user: dict[str, object]) -> str:
    pairs = {
        "user": json.dumps(user, separators=(",", ":")),
        "auth_date": str(int(time.time())),
        "query_id": "AAHdF6IQAAAAAN0XohDhrOrc",
    }
    pairs["hash"] = sign(bot_token, pairs)
    return urlencode(pairs, quote_via=quote)


def main() -> None:
    bot_token = load_bot_token()
    out_path = ROOT / "scripts" / "dev" / "init-data.local.txt"
    lines = []
    for index, user in enumerate(DEV_USERS, start=1):
        init_data = build_init_data(bot_token, user)
        lines.append(f"# user{index}: {user['first_name']} (@{user['username']}, id={user['id']})")
        lines.append(f"VITE_DEV_INIT_DATA={init_data}")
        lines.append("")
    out_path.write_text("\n".join(lines))
    print(f"Wrote {out_path}")
    print()
    print(out_path.read_text())


if __name__ == "__main__":
    main()
