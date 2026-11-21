"""Uji "Kondisi Terkini" tanpa jaringan: normalisasi, cache/TTL, stale, timeout, kunci FIRMS kosong, null Open-Meteo.

Jalankan: backend/.venv/bin/pytest backend -q
"""

import json
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import terkini  # noqa: E402
from app.main import app  # noqa: E402

FIX = Path(__file__).parent / "fixtures"
baca = lambda n: (FIX / n).read_text(encoding="utf-8")  # noqa: E731
KUNCI_UJI = "KUNCI-RAHASIA-UJI-123"


@pytest.fixture(autouse=True)
def bersih(monkeypatch):
    terkini.CACHE = terkini.Cache()
    monkeypatch.delenv("FIRMS_MAP_KEY", raising=False)


def palsu(peta):
    """http_get palsu: peta substring-URL -> teks; nilai Exception = dilempar."""
    def get(url):
        for k, v in peta.items():
            if k in url:
                if isinstance(v, Exception):
                    raise v
                return v
        raise AssertionError(f"URL tak terduga: {url}")
    return get


GEMPA = {"autogempa.json": baca("bmkg_autogempa.json"), "gempaterkini.json": baca("bmkg_gempaterkini.json"), "gempadirasakan.json": baca("bmkg_gempadirasakan.json")}


# --- gempa -------------------------------------------------------------------------
def test_gempa_normalisasi(monkeypatch):
    monkeypatch.setattr(terkini, "http_get", palsu(GEMPA))
    j = TestClient(app).get("/api/terkini/gempa").json()
    assert j["tersedia"] and not j["stale"] and j["sumber"] == "BMKG" and j["url_sumber"].startswith("https://")
    t = j["terbaru"]
    assert t["magnitudo"] == 4.2 and t["kedalaman_km"] == 55.0 and (t["lat"], t["lon"]) == (-1.27, 100.28)
    assert t["waktu_utc"] == "2026-11-21T19:52:18+00:00" and t["tsunami"] is False
    assert 1800 < t["jarak_km"] < 2000  # Pesisir Selatan (Sumbar) ke Bontang: ±1,4° LS dan ±17,2° BB ≈ 1.915 km
    assert len(j["terkini"]) == 15 and len(j["dirasakan"]) == 15
    assert "Tanggal" not in t and "Jam" not in t  # JSON mentah tidak diteruskan


def test_gempa_tsunami_dan_butir_rusak():
    g = {"DateTime": "2026-01-01T00:00:00+00:00", "Coordinates": "0.1,117.5", "Magnitude": "7.1", "Kedalaman": "10 km", "Wilayah": "x", "Potensi": "Berpotensi tsunami"}
    assert terkini._gempa(g)["tsunami"] is True
    assert terkini._gempa({**g, "Potensi": "Tidak berpotensi tsunami"})["tsunami"] is False
    teks = json.dumps({"Infogempa": {"gempa": [g, {"rusak": 1}]}})
    assert len(terkini._daftar(teks, "x")) == 1  # butir rusak dilewati
    with pytest.raises(terkini.GagalAmbil):
        terkini._daftar("bukan json", "x")


def test_jarak_nol_di_pusat():
    assert terkini.jarak_km(*terkini.PUSAT) == 0


# --- cache / TTL / stale -----------------------------------------------------------
def test_cache_ttl_dan_stale():
    jam = [1000.0]
    c = terkini.Cache(clock=lambda: jam[0])
    n = {"n": 0}

    def ok():
        n["n"] += 1
        return {"v": n["n"]}

    assert c.ambil("gempa", "gempa", 120, ok) == ({"v": 1}, 1000.0, False)
    jam[0] = 1100.0
    assert c.ambil("gempa", "gempa", 120, ok)[0] == {"v": 1} and n["n"] == 1  # masih segar: tanpa request baru
    jam[0] = 1200.0
    assert c.ambil("gempa", "gempa", 120, ok) == ({"v": 2}, 1200.0, False)

    def gagal():
        raise terkini.GagalAmbil("Sumber merespons HTTP 503.")

    jam[0] = 1400.0
    data, t, stale = c.ambil("gempa", "gempa", 120, gagal)
    assert data == {"v": 2} and t == 1200.0 and stale is True and "503" in c.galat["gempa"][1]
    with pytest.raises(terkini.GagalAmbil):
        c.ambil("cuaca", "cuaca:x", 120, gagal)  # tanpa cache sama sekali


def test_endpoint_stale_dan_tidak_tersedia(monkeypatch):
    jam = [1000.0]
    terkini.CACHE = terkini.Cache(clock=lambda: jam[0])
    cl = TestClient(app)
    monkeypatch.setattr(terkini, "http_get", palsu({"autogempa": "bukan json"}))
    j = cl.get("/api/terkini/gempa").json()
    assert j["tersedia"] is False and "galat" in j and "terbaru" not in j  # tidak ada angka karangan
    monkeypatch.setattr(terkini, "http_get", palsu(GEMPA))
    assert cl.get("/api/terkini/gempa").json()["stale"] is False
    jam[0] = 5000.0  # lewat TTL, sumber mati
    monkeypatch.setattr(terkini, "http_get", palsu({"": terkini.GagalAmbil("Sumber merespons HTTP 500.")}))
    j = cl.get("/api/terkini/gempa").json()
    assert j["tersedia"] and j["stale"] is True and j["diambil_pada"] == "1970-01-01T00:16:40+00:00" and j["terbaru"]["magnitudo"] == 4.2
    s = cl.get("/api/terkini/status").json()
    assert s["gempa"]["galat_terakhir"]["pesan"] == "Sumber merespons HTTP 500." and s["hotspot"]["aktif"] is False


# --- timeout / allowlist ------------------------------------------------------------
def test_http_get_timeout_dan_pesan_tanpa_url(monkeypatch):
    def lambat(*a, **k):
        raise socket.timeout("timed out")

    monkeypatch.setattr(terkini.urllib.request.OpenerDirector, "open", lambda self, *a, **k: lambat())
    monkeypatch.setattr(terkini, "check_url", lambda url, allowed=None: "host")
    with pytest.raises(terkini.GagalAmbil) as e:
        terkini.http_get(f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/{KUNCI_UJI}/x")
    assert KUNCI_UJI not in str(e.value) and "firms" not in str(e.value) and "TimeoutError" in str(e.value)


def test_host_di_luar_allowlist_ditolak():
    with pytest.raises(terkini.GagalAmbil, match="ditolak"):
        terkini.http_get("https://example.com/x.json")
    with pytest.raises(terkini.GagalAmbil, match="ditolak"):
        terkini.http_get("http://data.bmkg.go.id/DataMKG/TEWS/autogempa.json")  # bukan https


# --- cuaca -------------------------------------------------------------------------
def test_cuaca_normalisasi(monkeypatch):
    monkeypatch.setattr(terkini, "http_get", palsu({"adm4=64.74.01.1001": baca("bmkg_cuaca_6474011001.json")}))
    j = TestClient(app).get("/api/terkini/cuaca?kelurahan=bontang_kuala").json()
    assert j["tersedia"] and j["kelurahan"] == {"slug": "bontang_kuala", "nama": "Bontang Kuala", "adm4": "64.74.01.1001"}
    assert len(j["jam"]) == 17 and j["zona_waktu"] == "Asia/Makassar"
    a = j["jam"][0]
    assert a["waktu_lokal"] == "2026-11-22 07:00:00" and a["suhu_c"] == 25 and a["kelembapan"] == 95 and a["cuaca"] == "Berawan" and a["angin_kmj"] == 4.7
    assert [x["waktu_utc"] for x in j["jam"]] == sorted(x["waktu_utc"] for x in j["jam"])
    assert "image" not in a


def test_cuaca_kelurahan_tidak_dikenal_dan_kode_lengkap():
    assert TestClient(app).get("/api/terkini/cuaca?kelurahan=atlantis").status_code == 404
    assert len(terkini.KELURAHAN) == 15 and all(k["adm4"].startswith("64.74.") for k in terkini.KELURAHAN.values())


# --- hotspot -----------------------------------------------------------------------
def test_hotspot_tanpa_kunci():
    j = TestClient(app).get("/api/terkini/hotspot").json()
    assert j["dikonfigurasi"] is False and j["tersedia"] is False and "titik" not in j


def test_hotspot_normalisasi_dan_kunci_tidak_bocor(monkeypatch):
    monkeypatch.setenv("FIRMS_MAP_KEY", KUNCI_UJI)
    dilihat = []
    csv_ = baca("firms_viirs_noaa20_2hari.csv")

    def get(url):
        dilihat.append(url)
        return csv_ if "NOAA20" in url else "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n"

    monkeypatch.setattr(terkini, "http_get", get)
    data = terkini.ambil_hotspot()
    assert any(KUNCI_UJI in u for u in dilihat) and len(dilihat) == 3  # kunci hanya dalam URL keluar
    t = data["titik"][0]
    assert t["sensor"] == "NOAA-20" and t["confidence"] == "nominal" and t["waktu_utc"].endswith("+00:00") and t["frp_mw"] is not None
    ringkas = terkini._turunan_hotspot(data, sekarang=datetime(2026, 11, 20, 18, 0, tzinfo=timezone.utc))
    assert ringkas["jumlah_total"] == 3 and ringkas["jumlah_24jam"] >= 1
    assert sum(x["jumlah"] for x in ringkas["per_hari"]) == 3
    assert KUNCI_UJI not in json.dumps(ringkas)


def test_hotspot_galat_firms_tidak_membocorkan_kunci(monkeypatch):
    monkeypatch.setenv("FIRMS_MAP_KEY", KUNCI_UJI)
    monkeypatch.setattr(terkini, "http_get", lambda url: "Invalid MAP_KEY.")
    j = TestClient(app).get("/api/terkini/hotspot").json()
    assert j["tersedia"] is False and KUNCI_UJI not in json.dumps(j)


# --- laut --------------------------------------------------------------------------
def test_laut_normalisasi_dan_null(monkeypatch):
    nyata = json.loads(baca("openmeteo_marine_timur.json"))
    kosong = json.loads(json.dumps(nyata))
    for k in ("wave_height", "wave_direction", "wave_period", "sea_surface_temperature"):
        kosong["hourly"][k] = [None] * len(kosong["hourly"][k])  # sel daratan: Open-Meteo mengembalikan null
    urut = iter([nyata, kosong, nyata])
    monkeypatch.setattr(terkini, "http_get", lambda url: json.dumps(next(urut)))
    mulai = datetime.fromisoformat(nyata["hourly"]["time"][0] + ":00+08:00")
    data = terkini.ambil_laut(sekarang=mulai)
    p1, p2, _ = data["titik"]
    assert p1["tersedia"] and len(p1["jam"]) == 24 and p1["jam"][0]["tinggi_m"] == nyata["hourly"]["wave_height"][0]
    assert p2["tersedia"] is False and all(x["tinggi_m"] is None for x in p2["jam"])  # null tetap null
    assert p1["lat"] == terkini.WILAYAH["laut"][0]["lat"]
