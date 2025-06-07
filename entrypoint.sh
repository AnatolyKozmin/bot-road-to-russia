#!/usr/bin/env bash
set -e

# Проверка доступности базы данных
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

echo "→ Checking if alembic_version table exists ..."

python - <<'PY'
import os, asyncio, asyncpg
async def check_table():
    conn = await asyncpg.connect(os.environ["DB_SYNC"])
    try:
        result = await conn.fetchrow(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')"
        )
        table_exists = result['exists']
        if table_exists:
            print("→ alembic_version table exists, stamping head ...")
            os.system("alembic stamp head")
        else:
            print("→ alembic_version table does not exist, will create during upgrade ...")
    finally:
        await conn.close()
asyncio.run(check_table())
PY

echo "→ Running alembic upgrade head ..."
alembic upgrade head

if [[ "$RUN_MAIN" == "1" ]]; then
  echo "→ Starting bot ..."
  exec python main.py
fi

exec "$@"
