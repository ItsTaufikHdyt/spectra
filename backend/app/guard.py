"""
guard.py — Validasi URL geoportal (pencegahan SSRF).

Aturan: hanya https, port 443, tanpa kredensial di URL, host wajib ada di
backend/config/allowed_hosts, dan SEMUA alamat hasil DNS host tersebut harus alamat publik
(bukan privat, loopback, link-local, atau cadangan). Dipanggil untuk URL awal dan untuk setiap
redirect (lihat remote_http.get(url_guard=...)).

shortcut: DNS diperiksa sebelum request, tetapi urllib me-resolve ulang saat koneksi (celah
DNS rebinding). Risiko kecil karena host dibatasi allowlist; tutup dengan mem-pin IP bila
allowlist berisi host yang DNS-nya tidak dikendalikan Pemkot.
"""

from __future__ import annotations

import ipaddress
import os
import socket
from pathlib import Path
from urllib.parse import urlsplit

ALLOWED_HOSTS_FILE = Path(os.environ.get("SPECTRA_ALLOWED_HOSTS", Path(__file__).resolve().parents[1] / "config" / "allowed_hosts"))


class UrlDitolak(ValueError):
    """URL tidak boleh diakses backend; pesan siap ditampilkan ke pengguna."""


def load_allowed_hosts(path: Path = ALLOWED_HOSTS_FILE) -> frozenset[str]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return frozenset(x.strip().lower().rstrip(".") for x in lines if x.strip() and not x.lstrip().startswith("#"))


def check_url(url: str, *, allowed: frozenset[str] | None = None, resolve=socket.getaddrinfo) -> str:
    """Kembalikan host bila URL boleh diakses; selain itu lempar UrlDitolak."""
    try:
        parts = urlsplit(str(url).strip())
        port = parts.port
    except ValueError as err:
        raise UrlDitolak(f"URL tidak valid: {err}") from None
    if parts.scheme != "https":
        raise UrlDitolak("Hanya URL https yang diizinkan.")
    host = (parts.hostname or "").lower().rstrip(".")
    if not host:
        raise UrlDitolak("URL tidak memuat nama host.")
    if parts.username or parts.password:
        raise UrlDitolak("URL tidak boleh memuat nama pengguna atau kata sandi.")
    if port not in (None, 443):
        raise UrlDitolak("Hanya port standar https (443) yang diizinkan.")
    if host == "localhost" or host.endswith(".localhost"):
        raise UrlDitolak("Alamat localhost ditolak.")
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None and not literal.is_global:
        raise UrlDitolak(f"Alamat IP privat atau lokal ({host}) ditolak.")
    allowed = load_allowed_hosts() if allowed is None else allowed
    if host not in allowed:
        raise UrlDitolak(f"Host {host} tidak ada di daftar yang diizinkan (backend/config/allowed_hosts).")
    try:
        addrs = {a[4][0] for a in resolve(host, 443, proto=socket.IPPROTO_TCP)}
    except OSError as err:
        raise UrlDitolak(f"Host {host} tidak dapat di-resolve: {err}") from None
    bad = sorted(a for a in addrs if not ipaddress.ip_address(a).is_global)
    if bad or not addrs:
        raise UrlDitolak(f"Host {host} mengarah ke alamat privat atau lokal ({', '.join(bad) or 'kosong'}); ditolak.")
    return host
