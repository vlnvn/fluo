"""Explicit private demo setup. Credentials stay in ignored local files/stdin."""
import argparse
import hashlib
import json
import secrets
from pathlib import Path

from psycopg import connect, sql
from psycopg.conninfo import make_conninfo

from backend.postgres_store import connection_options, migrate
from backend.serverless_inputs import FILES

ROOT = Path(__file__).resolve().parents[1]


def read_env(path):
    values = {}
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        values[key] = json.loads(value) if value.startswith('"') else value
    return values


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--env-file', required=True)
    parser.add_argument('--upload-audited-runtime', action='store_true', required=True)
    args = parser.parse_args()
    env = read_env(args.env_file)
    dsn = env.get('DATABASE_URL_UNPOOLED') or env['DATABASE_URL']
    migrate(dsn)
    credential_file = ROOT / '.local/fluo-app-private.json'
    password = json.loads(credential_file.read_text())['password'] if credential_file.exists() else secrets.token_urlsafe(40)
    with connect(dsn, **connection_options(dsn)) as connection:
        connection.execute((ROOT / 'backend/migrations/002_private_artifacts.sql').read_text())
        for name, digest in FILES.items():
            body = (ROOT / 'data/original' / name).read_bytes()
            if hashlib.sha256(body).hexdigest() != digest:
                raise RuntimeError('Refusing unaudited private runtime input')
            connection.execute('INSERT INTO fluo_artifacts VALUES(%s,%s,%s) ON CONFLICT DO NOTHING', (name, digest, body))
            saved = connection.execute('SELECT body FROM fluo_artifacts WHERE name=%s AND sha256=%s', (name, digest)).fetchone()
            if not saved or hashlib.sha256(saved[0]).hexdigest() != digest:
                raise RuntimeError('Immutable remote artifact does not match audited digest')
        if not connection.execute('SELECT 1 FROM pg_roles WHERE rolname=%s', ('fluo_app',)).fetchone():
            connection.execute(sql.SQL('CREATE ROLE fluo_app LOGIN PASSWORD {}').format(sql.Literal(password)))
        connection.execute('GRANT USAGE ON SCHEMA public TO fluo_app')
        connection.execute('GRANT SELECT ON fluo_schema,fluo_artifacts TO fluo_app')
        connection.execute('GRANT SELECT,INSERT,UPDATE,DELETE ON fluo_guests,fluo_sessions,fluo_reviews,fluo_preferences,fluo_budgets TO fluo_app')
        database = connection.execute('SELECT current_database()').fetchone()[0]
        connection.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO fluo_app').format(sql.Identifier(database)))
    app_dsn = make_conninfo(env['DATABASE_URL'], user='fluo_app', password=password)
    credential_file.write_text(json.dumps({'password': password, 'dsn': app_dsn}), encoding='utf-8')
    with connect(app_dsn, **connection_options(app_dsn)) as connection:
        assert not connection.execute("SELECT has_table_privilege(current_user,'fluo_artifacts','UPDATE')").fetchone()[0]
        count = connection.execute('SELECT count(*) FROM fluo_artifacts').fetchone()[0]
        assert count == 2
    print(json.dumps({'private_runtime_files_verified': count, 'app_role': 'fluo_app',
                      'artifact_writes_allowed_to_app': False, 'legacy_records_imported': False}))


if __name__ == '__main__':
    main()
