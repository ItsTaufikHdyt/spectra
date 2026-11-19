#!/usr/bin/env bash
# Kendali database PostGIS pengembangan spectra (kontainer spectra-postgis-dev, volume spectra_pgdata_dev).
# Tidak menyentuh kontainer/volume lain (GeoNode dll.): semua perintah memakai proyek compose "spectra-dev".
#
# Pemakaian (dari mana saja):
#   data-pipeline/docker/db.sh naik            # nyalakan (menunggu siap)
#   data-pipeline/docker/db.sh mati            # matikan, DATA TETAP ADA
#   data-pipeline/docker/db.sh reset --ya      # HAPUS kontainer + volume spectra lalu nyalakan lagi (data hilang)
#   data-pipeline/docker/db.sh status
#   data-pipeline/docker/db.sh psql [args]     # shell psql
#   data-pipeline/docker/db.sh dump berkas.dump        # cadangan pg_dump (format custom)
#   data-pipeline/docker/db.sh restore berkas.dump     # pulihkan ke database kosong
set -euo pipefail

AKAR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # data-pipeline/
ENV_FILE="$AKAR/.env"
COMPOSE=(docker compose -f "$AKAR/docker/compose.yml" --env-file "$ENV_FILE")
KONTAINER="spectra-postgis-dev"

[ -f "$ENV_FILE" ] || { echo "ERROR: $ENV_FILE tidak ada. Salin dari .env.example lalu isi sandi." >&2; exit 1; }
# shellcheck disable=SC1090
set -a; . "$ENV_FILE"; set +a

perintah="${1:-}"; [ $# -gt 0 ] && shift || true
case "$perintah" in
  naik)
    "${COMPOSE[@]}" up -d --wait
    echo "PostGIS siap di ${SPECTRA_DB_HOST}:${SPECTRA_DB_PORT} (db ${SPECTRA_DB_NAME})."
    ;;
  mati)
    "${COMPOSE[@]}" stop
    echo "Dimatikan. Data tetap ada di volume spectra_pgdata_dev."
    ;;
  reset)
    if [ "${1:-}" != "--ya" ]; then
      echo "reset MENGHAPUS seluruh data pengembangan spectra (volume spectra_pgdata_dev)." >&2
      echo "Ulangi dengan: db.sh reset --ya" >&2; exit 2
    fi
    "${COMPOSE[@]}" down --volumes
    "${COMPOSE[@]}" up -d --wait
    echo "Database dikosongkan. Jalankan migrasi: data-pipeline/.venv/bin/python data-pipeline/db/migrate.py"
    ;;
  status)
    "${COMPOSE[@]}" ps
    ;;
  psql)
    docker exec -i "$KONTAINER" psql -U "$SPECTRA_DB_USER" -d "$SPECTRA_DB_NAME" "$@"
    ;;
  dump)
    [ -n "${1:-}" ] || { echo "Pakai: db.sh dump berkas.dump" >&2; exit 2; }
    docker exec "$KONTAINER" pg_dump -U "$SPECTRA_DB_USER" -d "$SPECTRA_DB_NAME" -Fc > "$1"
    echo "Cadangan ditulis: $1 ($(du -h "$1" | cut -f1)). Simpan DI LUAR git."
    ;;
  restore)
    [ -f "${1:-}" ] || { echo "Pakai: db.sh restore berkas.dump" >&2; exit 2; }
    docker exec -i "$KONTAINER" pg_restore -U "$SPECTRA_DB_USER" -d "$SPECTRA_DB_NAME" --no-owner < "$1"
    echo "Dipulihkan dari $1."
    ;;
  *)
    sed -n '2,13p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 2
    ;;
esac
