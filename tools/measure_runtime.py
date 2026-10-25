"""Local measurements only; never label them as hosted cold-start evidence."""
import ctypes
import hashlib
import json
import platform
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def peak_rss():
    if platform.system() != 'Windows':
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('faults', wintypes.DWORD)] + [(name, ctypes.c_size_t) for name in ('peak_working_set', 'working_set', 'peak_paged', 'paged', 'peak_nonpaged', 'nonpaged', 'pagefile', 'peak_pagefile')]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.windll.kernel32
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    fn = ctypes.windll.psapi.GetProcessMemoryInfo
    fn.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    if not fn(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise RuntimeError('Process memory measurement failed')
    return counters.peak_working_set


def main():
    started = time.perf_counter()
    from backend.service import ReplayService
    from backend.auth import GuestAccess, GuestSettings
    service = ReplayService(db_path=ROOT / '.local/runtime-measure.sqlite3')
    initialization = time.perf_counter() - started
    _, owner = GuestAccess(service.store, GuestSettings()).create()
    session = service.create('return-diversion', owner['digest'])
    timings = []
    cpu = time.process_time()
    for _ in range(20):
        start = time.perf_counter()
        state = service.snapshot(session['id'])
        timings.append(time.perf_counter() - start)
    wheels = list((ROOT / '.local/linux-wheels').glob('*.whl'))
    result = {'scope': 'Fresh Windows process, local SQLite. Not Vercel cold start or capacity.',
              'platform': platform.platform(), 'python': platform.python_version(),
              'initialization_wall_seconds': initialization, 'peak_rss_bytes': peak_rss(),
              'snapshot_p95_seconds': sorted(timings)[18], 'snapshot_mean_cpu_seconds': (time.process_time() - cpu) / 20,
              'snapshot_json_bytes': len(json.dumps(state).encode()), 'runtime_proof': service.runtime_proof,
              'model_bytes': (ROOT / 'models/fluo_hgb_synthetic_v2.joblib').stat().st_size,
              'model_sha256': hashlib.sha256((ROOT / 'models/fluo_hgb_synthetic_v2.joblib').read_bytes()).hexdigest(),
              'linux_cp312_wheels': len(wheels), 'linux_wheels_compressed_bytes': sum(p.stat().st_size for p in wheels),
              'linux_wheels_uncompressed_bytes': sum(sum(x.file_size for x in zipfile.ZipFile(p).infolist()) for p in wheels),
              'actual_vercel_bundle_size': None}
    service.store.close()
    destination = ROOT / 'docs/implementation/deployment/VERCEL_LOCAL_MEASUREMENTS.json'
    destination.write_text(json.dumps(result, indent=2), encoding='utf-8', newline='\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
