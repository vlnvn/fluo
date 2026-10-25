"""Non-destructive pg_dump/restore into a NEW database in the same Neon project."""
import hashlib
import json
import os
import secrets
import subprocess
from pathlib import Path

from psycopg import connect, sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from backend.postgres_store import connection_options
from tools.provision_postgres import read_env

ROOT = Path(__file__).resolve().parents[1]


def main():
    settings = read_env(ROOT / '.local/neon.env')
    dsn = settings['DATABASE_URL_UNPOOLED']
    parsed = conninfo_to_dict(dsn)
    destination = 'fluo_restore_check_' + secrets.token_hex(4)
    child_env = dict(os.environ)
    for key in ('host', 'port', 'user', 'password', 'dbname'):
        if key in parsed:
            child_env['PG' + ('DATABASE' if key == 'dbname' else key.upper())] = parsed[key]
    child_env.update(PGSSLMODE='verify-full', PGSSLROOTCERT=connection_options(dsn)['sslrootcert'])
    binary = ROOT / '.local/postgres-bin/pgsql/bin'
    backup = ROOT / '.local/fluo-neon-demo.dump'
    dump = subprocess.run([str(binary / 'pg_dump.exe'), '--format=custom', '--no-owner', '--no-acl',
                           '--table=public.fluo_*', '--file=' + str(backup)], env=child_env, capture_output=True)
    (ROOT / '.local/pg-dump-private.log').write_bytes(dump.stdout + dump.stderr)
    if dump.returncode:
        raise RuntimeError('Backup failed; inspect the ignored private log')
    with connect(dsn, autocommit=True, **connection_options(dsn)) as connection:
        version = connection.execute('SHOW server_version').fetchone()[0]
        connection.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(destination)))
    child_env['PGDATABASE'] = destination
    restored = subprocess.run([str(binary / 'pg_restore.exe'), '--no-owner', '--no-acl',
                               '--dbname=' + destination, str(backup)], env=child_env, capture_output=True)
    (ROOT / '.local/pg-restore-private.log').write_bytes(restored.stdout + restored.stderr)
    if restored.returncode:
        raise RuntimeError('Isolated restore failed; original database untouched; inspect private log')
    tables = ['fluo_guests', 'fluo_sessions', 'fluo_reviews', 'fluo_preferences', 'fluo_artifacts']
    result = {'status': 'PASS', 'scope': 'Logical snapshot restored into a separate new database in the same Neon Free project; no production rollback or managed PITR claimed.',
              'source_database_untouched': True, 'restore_database': destination,
              'server_version': version, 'backup_bytes': backup.stat().st_size,
              'backup_sha256': hashlib.sha256(backup.read_bytes()).hexdigest(), 'table_hashes_match': {}}
    with connect(dsn, **connection_options(dsn)) as source, connect(make_conninfo(dsn, dbname=destination), **connection_options(dsn)) as target:
        for table in tables:
            # Identifiers are from the fixed allowlist above. No values/notes are logged.
            query = sql.SQL('SELECT * FROM {} ORDER BY 1,2').format(sql.Identifier(table))
            original = source.execute(query).fetchall()
            copy = target.execute(query).fetchall()
            equal = original == copy
            if not equal:
                raise RuntimeError('Restore rows differ; original database remains untouched')
            result['table_hashes_match'][table] = {'exact_rows_equal': equal, 'rows': len(original)}
    (ROOT / 'docs/implementation/qa/vercel/hosted-backup-restore.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'restored_to_new_database': destination, 'source_untouched': True}))


if __name__ == '__main__':
    main()
