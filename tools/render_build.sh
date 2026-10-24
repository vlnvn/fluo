#!/usr/bin/env bash
set -euo pipefail
python tools/runtime_packet.py --download
python -m pip install -r requirements-runtime.lock
cd web
npm ci
npm run build
