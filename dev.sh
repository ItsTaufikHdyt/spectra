#!/usr/bin/env bash
# dev.sh — Jalankan backend (FastAPI) dan frontend (Vite) spectra bersamaan
# untuk pengembangan lokal. Hentikan keduanya dengan Ctrl+C.
#
# Pemakaian (dari root repo):
#   ./dev.sh
#
# Variabel opsional:
#   SPECTRA_API_PORT  port backend  (bawaan 8100)
#   SPECTRA_WEB_PORT  port frontend (bawaan 3000)

set -euo pipefail
set -m  # setiap proses latar mendapat process group sendiri, agar mudah dihentikan

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_PORT="${SPECTRA_API_PORT:-8100}"
WEB_PORT="${SPECTRA_WEB_PORT:-3000}"
UVICORN="$ROOT/backend/.venv/bin/uvicorn"

info()  { printf '\033[1;34m[dev]\033[0m %s\n' "$*"; }
galat() { printf '\033[1;31m[dev]\033[0m %s\n' "$*" >&2; }

# ---------- Cek prasyarat ----------
if [[ ! -x "$UVICORN" ]]; then
  galat "Backend belum terpasang. Jalankan dulu:"
  galat "  python3 -m venv backend/.venv && backend/.venv/bin/pip install -r backend/requirements.txt"
  exit 1
fi
if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  galat "Dependensi frontend belum terpasang. Jalankan dulu:  cd frontend && npm install"
  exit 1
fi
command -v npm >/dev/null || { galat "npm tidak ditemukan."; exit 1; }

port_terpakai() { (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null; }
for p in "$API_PORT" "$WEB_PORT"; do
  if port_terpakai "$p"; then
    galat "Port $p sudah dipakai proses lain. Hentikan proses itu, atau pakai port lain:"
    galat "  SPECTRA_API_PORT=8101 SPECTRA_WEB_PORT=3001 ./dev.sh"
    exit 1
  fi
done

# ---------- Penghentian ----------
BACKEND_PID=""
FRONTEND_PID=""
hentikan() {
  trap - INT TERM EXIT
  echo
  info "Menghentikan backend dan frontend..."
  for pid in $FRONTEND_PID $BACKEND_PID; do
    kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
  info "Selesai."
}
trap hentikan INT TERM EXIT

# ---------- Backend ----------
info "Menjalankan backend di http://127.0.0.1:$API_PORT/api ..."
"$UVICORN" app.main:app --app-dir "$ROOT/backend" --host 127.0.0.1 --port "$API_PORT" \
  > >(sed -u 's/^/[backend]  /') 2>&1 &
BACKEND_PID=$!

# Tunggu backend siap (maks. 30 detik)
siap=0
for _ in $(seq 1 60); do
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    galat "Backend berhenti saat start. Periksa log [backend] di atas."
    exit 1
  fi
  if command -v curl >/dev/null && curl -fsS "http://127.0.0.1:$API_PORT/api/health" >/dev/null 2>&1; then
    siap=1; break
  fi
  sleep 0.5
done
if [[ $siap -eq 1 ]]; then
  info "Backend siap."
else
  info "Status backend belum terkonfirmasi (curl tidak ada atau health belum merespons). Melanjutkan."
fi

# ---------- Frontend ----------
info "Menjalankan frontend di http://localhost:$WEB_PORT ..."
(
  cd "$ROOT/frontend"
  SPECTRA_API_URL="http://127.0.0.1:$API_PORT" exec npm run dev -- --port "$WEB_PORT" --strictPort
) > >(sed -u 's/^/[frontend] /') 2>&1 &
FRONTEND_PID=$!

info "Keduanya berjalan. Buka http://localhost:$WEB_PORT  —  Ctrl+C untuk menghentikan."

# Jika salah satu berhenti, hentikan yang lain juga
set +e
wait -n "$BACKEND_PID" "$FRONTEND_PID"
kode=$?
set -e
if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
  galat "Backend berhenti (kode $kode)."
elif ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
  galat "Frontend berhenti (kode $kode)."
fi
exit "$kode"
