#!/usr/bin/env bash
# Deploy presence.pyw to the Windows runtime dir and restart it.
set -euo pipefail
cd "$(dirname "$0")"

PY="/mnt/c/Users/computer/AppData/Local/Programs/Python/Python311/python.exe"
DEST="/mnt/c/Users/computer/AppData/Local/ShodanPresence"
WINPATH='C:\Users\computer\AppData\Local\ShodanPresence\presence.pyw'

"$PY" -c "import ast,sys; ast.parse(open(sys.argv[1], encoding='utf-8').read())" presence.pyw
cp presence.pyw "$DEST/presence.pyw"
taskkill.exe /IM pythonw.exe /F 2>/dev/null || true
powershell.exe -NoProfile -Command "Start-Process -WindowStyle Hidden 'C:\\Users\\computer\\AppData\\Local\\Programs\\Python\\Python311\\pythonw.exe' -ArgumentList '\"$WINPATH\"'"
sleep 3
tasklist.exe | grep -i pythonw && echo "deployed + running"
