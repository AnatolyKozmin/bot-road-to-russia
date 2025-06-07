#!/usr/bin/env bash
set -e


python - <<'PY'
import os, time, asyncpg, asyncio
async def wait():
    for _ in range(30):
        try:
            await asyncpg.connect(os.environ["DB_SYNC"])  # sync URL (postgres://...)
            return
        except Exception:
            time.sleep(2)
    raise SystemExit("DB not reachable")
asyncio.run(wait())
PY

echo "→ Running alembic upgrade head ..."
alembic upgrade head


if [[ "$RUN_MAIN" == "1" ]]; then
  echo "→ Starting bot ..."
  exec python main.py
fi


exec "$@"
