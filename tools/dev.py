"""Run the loopback API and web development server; stop only owned children."""
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def responds(url):
    try:
        return urllib.request.urlopen(url, timeout=1).status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def main():
    if responds('http://127.0.0.1:8000/api/v1/health') or responds('http://127.0.0.1:5173'):
        raise SystemExit('A server already uses a Fluo port. Use the running application or stop that server explicitly first.')
    local = ROOT / '.local'
    local.mkdir(exist_ok=True)
    env = {**os.environ, 'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1'}
    commands = [([sys.executable, '-m', 'uvicorn', 'backend.app:app', '--host','127.0.0.1','--port','8000','--no-server-header','--timeout-keep-alive','10'], ROOT, 'api'),
                ([shutil.which('npm.cmd' if os.name == 'nt' else 'npm') or 'npm', 'run','dev'], ROOT/'web', 'web')]
    children, logs = [], []
    try:
        for command, cwd, name in commands:
            log = (local / f'{name}.log').open('w', encoding='utf-8')
            logs.append(log)
            flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            children.append(subprocess.Popen(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=flags))
        for _ in range(90):
            if any(child.poll() is not None for child in children):
                raise RuntimeError('A Fluo process exited. Inspect .local/api.log and .local/web.log.')
            if responds('http://127.0.0.1:8000/api/v1/health') and responds('http://127.0.0.1:5173'):
                print('Fluo is running: http://127.0.0.1:5173', flush=True)
                print('API / OpenAPI: http://127.0.0.1:8000/docs\nPress Ctrl+C to stop these two processes.', flush=True)
                break
            time.sleep(1)
        else:
            raise RuntimeError('Startup timed out; inspect .local logs.')
        while all(child.poll() is None for child in children):
            time.sleep(.5)
    except KeyboardInterrupt:
        pass
    finally:
        for child in children:
            if child.poll() is None:
                if os.name == 'nt':
                    subprocess.run(['taskkill','/PID',str(child.pid),'/T','/F'],capture_output=True)
                else:
                    child.send_signal(signal.SIGTERM)
        for log in logs:
            log.close()


if __name__ == '__main__':
    main()
