"""
terkini.py — "Kondisi Terkini": gempa BMKG, cuaca BMKG, hotspot NASA FIRMS, gelombang laut Open-Meteo.

Browser TIDAK memanggil sumber ini langsung; frontend memanggil /api/terkini/* (proxy Vite). Aturan:
- hanya GET, hanya https:443, host wajib ada di config/allowed_hosts_terkini, redirect tidak diikuti, timeout 10 detik;
- satu cache per sumber di memori dengan TTL, jadi banyak pengguna = satu permintaan keluar;
- gagal ambil -> sajikan cache terakhir dengan stale=true; tanpa cache -> tersedia=false. Tidak pernah ada angka karangan;
- keluaran dinormalisasi ke skema ringkas kita (JSON/CSV mentah sumber tidak diteruskan);
- FIRMS_MAP_KEY hanya dari env; tidak pernah masuk log, pesan galat, atau respons (URL tidak ikut di pesan galat).

shortcut: cache di memori proses (satu worker, lihat registry.py) dan satu kunci global saat mengambil; ganti dengan
cache per kunci atau Redis bila backend dijalankan multi-worker.
"""

from __future__ import annotations

import csv
import io
import json
import math
import os
import re
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import yaml
from fastapi import APIRouter, HTTPException

from .guard import UrlDitolak, check_url, load_allowed_hosts

CONFIG = Path(__file__).resolve().parents[1] / "config"
HOSTS_FILE = Path(os.environ.get("SPECTRA_ALLOWED_HOSTS_TERKINI", CONFIG / "allowed_hosts_terkini"))
WILAYAH = yaml.safe_load((CONFIG / "wilayah_bontang.yaml").read_text(encoding="utf-8"))
KELURAHAN = {k["slug"]: k for k in WILAYAH["kelurahan"]}
PUSAT = (WILAYAH["pusat_bontang"]["lat"], WILAYAH["pusat_bontang"]["lon"])

TIMEOUT = 10
MAKS_BYTE = 5_000_000
WITA = timezone(timedelta(hours=8))
TTL = {"gempa": 120, "cuaca": 3600, "hotspot": 1800, "laut": 3600}  # detik
META = {
    "gempa": {"sumber": "BMKG", "atribusi": "Badan Meteorologi, Klimatologi, dan Geofisika (BMKG)", "url_sumber": "https://data.bmkg.go.id/gempabumi/"},
    "cuaca": {"sumber": "BMKG", "atribusi": "Badan Meteorologi, Klimatologi, dan Geofisika (BMKG)", "url_sumber": "https://data.bmkg.go.id/prakiraan-cuaca/"},
    "hotspot": {"sumber": "NASA FIRMS", "atribusi": "NASA FIRMS (VIIRS, data hampir waktu nyata)", "url_sumber": "https://firms.modaps.eosdis.nasa.gov/"},
    "laut": {"sumber": "Open-Meteo (CC BY 4.0)", "atribusi": "Open-Meteo Marine Weather API, CC BY 4.0", "url_sumber": "https://open-meteo.com/en/docs/marine-weather-api"},
}
SATELIT = {"N": "Suomi NPP", "N20": "NOAA-20", "N21": "NOAA-21"}
CONFIDENCE = {"l": "rendah", "n": "nominal", "h": "tinggi"}


class GagalAmbil(Exception):
    """Sumber tidak dapat diambil atau formatnya tidak dikenali; pesan aman ditampilkan (tanpa URL/kunci)."""


# ---------------------------------------------------------------------------
class _TanpaRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):  # redirect = keluar dari allowlist
        return None


def http_get(url: str) -> str:
    """GET satu URL yang lolos allowlist. Pesan galat tidak pernah memuat URL (bisa berisi kunci)."""
    try:
        check_url(url, allowed=load_allowed_hosts(HOSTS_FILE))
    except UrlDitolak as err:
        raise GagalAmbil("Alamat sumber ditolak oleh daftar host yang diizinkan.") from err
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "spectra-backend", "Accept": "application/json, text/csv"})
    try:
        with urllib.request.build_opener(_TanpaRedirect).open(req, timeout=TIMEOUT) as resp:
            return resp.read(MAKS_BYTE).decode("utf-8")
    except urllib.error.HTTPError as err:
        raise GagalAmbil(f"Sumber merespons HTTP {err.code}.") from None
    except Exception as err:  # noqa: BLE001 — timeout, DNS, TLS, dsb.
        raise GagalAmbil(f"Sumber tidak dapat dihubungi ({type(err).__name__}).") from None


def _json(teks: str, apa: str):
    try:
        return json.loads(teks)
    except ValueError:
        raise GagalAmbil(f"Format data {apa} tidak dikenali.") from None


def _iso(t: float) -> str:
    return datetime.fromtimestamp(t, timezone.utc).isoformat(timespec="seconds")


def jarak_km(lat: float, lon: float) -> float:
    """Jarak lingkaran besar (haversine) dari pusat Bontang, km."""
    p1, p2 = math.radians(PUSAT[0]), math.radians(lat)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon - PUSAT[1]) / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
class Cache:
    """Cache TTL per kunci; saat gagal, sajikan entri terakhir (stale)."""

    def __init__(self, clock=time.time):
        self.clock = clock
        self.data: dict[str, tuple[object, float]] = {}
        self.galat: dict[str, tuple[float, str]] = {}  # per sumber: (waktu, pesan)
        self._kunci = threading.Lock()

    def ambil(self, sumber: str, kunci: str, ttl: float, fn):
        """-> (data, waktu_ambil, stale). Melempar GagalAmbil bila gagal dan belum ada cache."""
        with self._kunci:
            now = self.clock()
            ada = self.data.get(kunci)
            if ada and now - ada[1] < ttl:
                return ada[0], ada[1], False
            try:
                data = fn()
            except GagalAmbil as err:
                self.galat[sumber] = (now, str(err))
                if ada:
                    return ada[0], ada[1], True
                raise
            self.data[kunci] = (data, now)
            self.galat.pop(sumber, None)
            return data, now, False


CACHE = Cache()


def _jawab(sumber: str, kunci: str, fn, turunan=None) -> dict:
    """Bungkus hasil dengan sumber/atribusi/url_sumber/diambil_pada/stale. Gagal tanpa cache -> tersedia=false."""
    try:
        data, t, stale = CACHE.ambil(sumber, kunci, TTL[sumber], fn)
    except GagalAmbil as err:
        return {**META[sumber], "tersedia": False, "stale": False, "diambil_pada": None, "galat": str(err)}
    isi = turunan(data) if turunan else data
    return {**META[sumber], "tersedia": True, "stale": stale, "diambil_pada": _iso(t), **isi}


# --- gempa -----------------------------------------------------------------------
def _gempa(g: dict) -> dict:
    lat, lon = (float(x) for x in g["Coordinates"].split(","))
    potensi = g.get("Potensi")
    return {
        "waktu_utc": g["DateTime"],  # BMKG menyajikan jam WIB; DateTime sudah UTC, frontend mengubah ke WITA
        "magnitudo": float(g["Magnitude"]),
        "kedalaman_km": float(re.match(r"\s*([\d.]+)", g["Kedalaman"]).group(1)),
        "lat": lat, "lon": lon, "wilayah": g["Wilayah"], "potensi": potensi, "dirasakan": g.get("Dirasakan"),
        "tsunami": bool(potensi) and "tsunami" in potensi.lower() and "tidak" not in potensi.lower(),
        "jarak_km": round(jarak_km(lat, lon)),
    }


def _daftar(teks: str, apa: str) -> list[dict]:
    try:
        mentah = _json(teks, apa)["Infogempa"]["gempa"]
    except (KeyError, TypeError):
        raise GagalAmbil(f"Format data {apa} tidak dikenali.") from None
    hasil = []
    for g in mentah if isinstance(mentah, list) else [mentah]:
        try:
            hasil.append(_gempa(g))
        except (KeyError, ValueError, AttributeError, TypeError):
            continue  # satu butir rusak dilewati, bukan diganti angka
    if not hasil:
        raise GagalAmbil(f"Data {apa} kosong atau formatnya tidak dikenali.")
    return hasil


def ambil_gempa() -> dict:
    base = "https://data.bmkg.go.id/DataMKG/TEWS/"
    return {
        "terbaru": _daftar(http_get(base + "autogempa.json"), "gempa terbaru")[0],
        "terkini": _daftar(http_get(base + "gempaterkini.json"), "gempa M5+"),
        "dirasakan": _daftar(http_get(base + "gempadirasakan.json"), "gempa dirasakan"),
    }


# --- cuaca -----------------------------------------------------------------------
def ambil_cuaca(slug: str) -> dict:
    kel = KELURAHAN[slug]
    j = _json(http_get(f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={quote(kel['adm4'])}"), "cuaca")
    try:
        slot = [s for hari in j["data"][0]["cuaca"] for s in hari]
        jam = [
            {
                "waktu_lokal": s["local_datetime"], "waktu_utc": s["utc_datetime"], "suhu_c": s["t"], "kelembapan": s["hu"],
                "cuaca": s["weather_desc"], "tutupan_awan": s.get("tcc"), "hujan_mm": s.get("tp"),
                "angin_kmj": s.get("ws"), "angin_dari": s.get("wd"), "angin_derajat": s.get("wd_deg"),
            }
            for s in slot
        ]
    except (KeyError, IndexError, TypeError):
        raise GagalAmbil("Format data cuaca tidak dikenali.") from None
    if not jam:
        raise GagalAmbil("Data cuaca kosong.")
    jam.sort(key=lambda x: x["waktu_utc"])
    return {"kelurahan": {"slug": slug, "nama": kel["nama"], "adm4": kel["adm4"]}, "zona_waktu": "Asia/Makassar", "jam": jam}


# --- hotspot ---------------------------------------------------------------------
def _kunci_firms() -> str | None:
    return (os.environ.get("FIRMS_MAP_KEY") or "").strip().strip("\"'") or None


def ambil_hotspot() -> dict:
    kunci, cfg = _kunci_firms(), WILAYAH["firms"]
    titik = []
    for sumber in cfg["sumber"]:
        teks = http_get(f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{kunci}/{sumber}/{cfg['bbox']}/{cfg['hari']}")
        if not teks.lstrip().startswith("latitude"):  # galat FIRMS berupa teks biasa (mis. kunci tidak valid)
            raise GagalAmbil("FIRMS tidak mengembalikan data (periksa FIRMS_MAP_KEY atau kuota).")
        for r in csv.DictReader(io.StringIO(teks)):
            try:
                lat, lon = float(r["latitude"]), float(r["longitude"])
                waktu = datetime.strptime(f"{r['acq_date']} {int(r['acq_time']):04d}", "%Y-%m-%d %H%M").replace(tzinfo=timezone.utc)
                titik.append({
                    "lat": lat, "lon": lon, "waktu_utc": waktu.isoformat(), "sensor": SATELIT.get(r.get("satellite"), r.get("satellite")),
                    "confidence": CONFIDENCE.get((r.get("confidence") or "").lower(), r.get("confidence")),
                    "frp_mw": float(r["frp"]) if r.get("frp") not in (None, "") else None, "jarak_km": round(jarak_km(lat, lon)),
                })
            except (KeyError, ValueError):
                continue
    titik.sort(key=lambda t: t["waktu_utc"], reverse=True)
    return {"titik": titik}


def _turunan_hotspot(data: dict, sekarang=None) -> dict:
    now = sekarang or datetime.now(timezone.utc)
    titik, per_hari = data["titik"], {}
    for t in titik:
        hari = datetime.fromisoformat(t["waktu_utc"]).astimezone(WITA).date().isoformat()
        per_hari[hari] = per_hari.get(hari, 0) + 1
    batas = (now - timedelta(hours=24)).isoformat()
    return {
        "dikonfigurasi": True, "hari": WILAYAH["firms"]["hari"], "titik": titik, "jumlah_total": len(titik),
        "jumlah_24jam": sum(1 for t in titik if t["waktu_utc"] >= batas),
        "per_hari": [{"tanggal_wita": h, "jumlah": n} for h, n in sorted(per_hari.items())],
        "catatan": "Titik panas satelit bukan kebakaran terkonfirmasi.",
    }


# --- laut ------------------------------------------------------------------------
_HOURLY = "wave_height,wave_direction,wave_period,sea_surface_temperature"


def ambil_laut(sekarang=None) -> dict:
    now = (sekarang or datetime.now(WITA)).astimezone(WITA).strftime("%Y-%m-%dT%H:00")
    titik = []
    for p in WILAYAH["laut"]:
        j = _json(http_get(
            f"https://marine-api.open-meteo.com/v1/marine?latitude={p['lat']}&longitude={p['lon']}&hourly={_HOURLY}"
            "&timezone=Asia%2FMakassar&forecast_days=2"), "laut")
        try:
            h = j["hourly"]
            jam = [
                {"waktu_lokal": w, "tinggi_m": h["wave_height"][i], "arah_derajat": h["wave_direction"][i],
                 "periode_s": h["wave_period"][i], "suhu_laut_c": h["sea_surface_temperature"][i]}
                for i, w in enumerate(h["time"]) if w >= now
            ][:24]
        except (KeyError, IndexError, TypeError):
            raise GagalAmbil("Format data laut tidak dikenali.") from None
        # sel daratan/di luar cakupan = null; jangan diisi apa pun
        titik.append({"id": p["id"], "nama": p["nama"], "lat": p["lat"], "lon": p["lon"], "tersedia": any(x["tinggi_m"] is not None for x in jam), "jam": jam})
    return {"zona_waktu": "Asia/Makassar", "titik": titik}


# --- router ----------------------------------------------------------------------
router = APIRouter(prefix="/api/terkini")


@router.get("/gempa")
def gempa():
    return _jawab("gempa", "gempa", ambil_gempa)


@router.get("/cuaca")
def cuaca(kelurahan: str = "bontang_kuala"):
    if kelurahan not in KELURAHAN:
        raise HTTPException(404, "Kelurahan tidak dikenal.")
    return _jawab("cuaca", f"cuaca:{kelurahan}", lambda: ambil_cuaca(kelurahan))


@router.get("/hotspot")
def hotspot():
    if not _kunci_firms():
        return {**META["hotspot"], "dikonfigurasi": False, "tersedia": False, "stale": False, "diambil_pada": None}
    return _jawab("hotspot", "hotspot", ambil_hotspot, _turunan_hotspot)


@router.get("/laut")
def laut():
    return _jawab("laut", "laut", ambil_laut)


@router.get("/status")
def status():
    keluar = {}
    for s in META:
        waktu = [t for k, (_, t) in CACHE.data.items() if k.split(":")[0] == s]
        galat = CACHE.galat.get(s)
        keluar[s] = {
            "aktif": _kunci_firms() is not None if s == "hotspot" else True,
            "ttl_detik": TTL[s],
            "diambil_pada": _iso(max(waktu)) if waktu else None,
            "galat_terakhir": {"waktu": _iso(galat[0]), "pesan": galat[1]} if galat else None,
        }
    return keluar
