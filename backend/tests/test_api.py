"""Uji backend tanpa jaringan: guard SSRF, redirect, alur registry/API (geoportal di-mock).

Jalankan: backend/.venv/bin/pytest backend -q
"""

import json
import socket
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import geoportal  # noqa: E402
from app.guard import UrlDitolak, check_url  # noqa: E402

ALLOWED = frozenset({"geoportal.bontangkota.go.id"})
PUBLIC = lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("103.10.10.10", 443))]  # noqa: E731
PRIVATE = lambda *a, **k: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 443))]  # noqa: E731


# --- guard ------------------------------------------------------------------------
@pytest.mark.parametrize(
    "url, pesan",
    [
        ("https://evil.example.com/geoserver/ows", "tidak ada di daftar"),
        ("http://geoportal.bontangkota.go.id/geoserver/ows", "Hanya URL https"),
        ("https://localhost/geoserver/ows", "localhost"),
        ("https://127.0.0.1/ows", "privat atau lokal"),
        ("https://192.168.1.10/ows", "privat atau lokal"),
        ("https://[::1]/ows", "privat atau lokal"),
        ("https://169.254.169.254/latest/meta-data", "privat atau lokal"),
        ("https://geoportal.bontangkota.go.id:8443/ows", "port"),
        ("https://user:pw@geoportal.bontangkota.go.id/ows", "kata sandi"),
        ("file:///etc/passwd", "Hanya URL https"),
    ],
)
def test_url_ditolak(url, pesan):
    with pytest.raises(UrlDitolak, match=pesan):
        check_url(url, allowed=ALLOWED, resolve=PUBLIC)


def test_host_allowlist_yang_resolve_ke_ip_privat_ditolak():
    with pytest.raises(UrlDitolak, match="10.0.0.5"):
        check_url("https://geoportal.bontangkota.go.id/ows", allowed=ALLOWED, resolve=PRIVATE)


def test_url_sah_diterima():
    assert check_url("https://geoportal.bontangkota.go.id/geoserver/ows?x=1", allowed=ALLOWED, resolve=PUBLIC) == "geoportal.bontangkota.go.id"


def test_redirect_ke_host_lain_ditolak():
    """remote_http memanggil url_guard untuk setiap tujuan redirect."""
    from sources import remote_http

    seen = []

    def guard(url):
        seen.append(url)
        if "evil" in url:
            raise UrlDitolak("Host evil tidak ada di daftar")

    redirect = next(h for h in remote_http._opener(guard).handlers if isinstance(h, remote_http.urllib.request.HTTPRedirectHandler))
    req = remote_http.urllib.request.Request("https://geoportal.bontangkota.go.id/ows")
    with pytest.raises(UrlDitolak):
        redirect.redirect_request(req, None, 302, "Found", {}, "https://evil.example.com/x")
    assert seen == ["https://evil.example.com/x"]


def test_operasi_tulis_ditolak_sebelum_request():
    from sources.remote_http import get

    for op in ("Transaction", "Harvest", "LockFeature"):
        with pytest.raises(PermissionError):
            get("https://geoportal.bontangkota.go.id/ows", {"request": op}, url_guard=lambda u: None)


def test_pesan_error_jelas():
    from sources.remote_http import FetchError, ResponseTooLarge

    assert geoportal.explain(FetchError("x", status=None)).pesan.startswith("Server geoportal tidak merespons")
    assert "HTTP 503" in geoportal.explain(FetchError("x", status=503)).pesan
    assert geoportal.explain(ResponseTooLarge("x")).status == 413
    with pytest.raises(geoportal.GeoportalError, match=r"79\.167 fitur, batas 20\.000"):
        geoportal.ensure_small(79167)


# --- API (geoportal di-mock) ------------------------------------------------------
META = {
    "judul": "Banjir 2024", "bbox": [117.44, 0.03, 117.52, 0.2], "srs_sumber": "urn:ogc:def:crs:EPSG::32650",
    "atribut_tersedia": ["fid", "nama", "kelas"], "jumlah_fitur": 2,
    "wms_url": "https://geoportal.bontangkota.go.id/geoserver/ows",
}
BODY = {"wfs_url": "https://geoportal.bontangkota.go.id/geoserver/ows?service=WFS", "typename": "geonode:banjir_ar_25k_2024_final"}


@pytest.fixture
def client(tmp_path, monkeypatch):
    import app.main as main

    monkeypatch.setattr(main, "registry", main.Registry(tmp_path))
    meta = dict(META)
    monkeypatch.setattr(geoportal, "describe", lambda url, tn: dict(meta))
    monkeypatch.setattr(geoportal, "count_features", lambda url, tn: meta["jumlah_fitur"])

    def fake_download(entry, layer_dir):
        layer_dir.mkdir(parents=True, exist_ok=True)
        feats = [{"type": "Feature", "geometry": {"type": "Point", "coordinates": [117.45, 0.1]},
                  "properties": {"fid_sumber": str(i), "nama": f"Area {i}", "atribut": {"fid": i, "nama": f"Area {i}", "kelas": f"K{i}"}}}
                 for i in range(meta["jumlah_fitur"])]
        (layer_dir / "data.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
        return {"jumlah_fitur": len(feats), "field_nama": "nama", "urutan_sumbu": "lonlat"}

    monkeypatch.setattr(geoportal, "download", fake_download)
    from fastapi.testclient import TestClient

    c = TestClient(main.app)
    c.meta, c.root = meta, tmp_path
    return c


def test_alur_lengkap(client):
    r = client.post("/api/layers", json=BODY)
    assert r.status_code == 201, r.text
    e = r.json()
    assert e["mode"] == "geojson" and e["aktif"] and e["wfs_url"].endswith("/geoserver/ows")  # query dibuang
    assert (client.root / e["id"] / "data.geojson").exists()
    assert client.post("/api/layers", json=BODY).status_code == 409

    assert client.patch(f"/api/layers/{e['id']}", json={"aktif": False, "warna": "#112233", "opasitas": 0.4}).json()["aktif"] is False
    assert client.patch(f"/api/layers/{e['id']}", json={"warna": "merah"}).status_code == 422
    assert client.patch(f"/api/layers/{e['id']}", json={"field_nama": "kelas"}).status_code == 200
    names = [f["properties"]["nama"] for f in client.get(f"/api/layers/{e['id']}/data").json()["features"]]
    assert names == ["K0", "K1"]
    assert client.patch(f"/api/layers/{e['id']}", json={"field_nama": "tidak_ada"}).status_code == 422

    r = client.post(f"/api/layers/{e['id']}/refresh")
    assert r.status_code == 200 and r.json()["status"] == "ok" and r.json()["aktif"] is False  # status tetap

    assert client.delete(f"/api/layers/{e['id']}").status_code == 204
    assert not (client.root / e["id"]).exists()
    assert client.get("/api/layers").json()["layers"] == []
    assert client.get(f"/api/layers/{e['id']}/data").status_code == 404


def test_layer_besar_ditolak_sebagai_geojson_tapi_boleh_wms(client):
    client.meta["jumlah_fitur"] = geoportal.MAX_FITUR + 1
    r = client.post("/api/layers", json=BODY)
    assert r.status_code == 413 and r.json()["saran"] == "wms" and "Gunakan tampilan WMS" in r.json()["detail"]
    assert [p.name for p in client.root.iterdir()] == []  # tidak ada cache yang dibuat
    r = client.post("/api/layers", json={**BODY, "mode": "wms"})
    assert r.status_code == 201 and r.json()["mode"] == "wms"
    assert client.get(f"/api/layers/{r.json()['id']}/data").status_code == 404


def test_refresh_gagal_menyimpan_pesan_dan_data_lama(client):
    e = client.post("/api/layers", json=BODY).json()
    client.meta["jumlah_fitur"] = geoportal.MAX_FITUR + 1
    assert client.post(f"/api/layers/{e['id']}/refresh").status_code == 413
    after = client.get("/api/layers").json()["layers"][0]
    assert after["status"] == "error" and "terlalu besar" in after["pesan_error"]
    assert client.get(f"/api/layers/{e['id']}/data").status_code == 200


def test_inspect_menolak_url_terlarang(client):
    for url in ("https://evil.example.com/ows", "http://geoportal.bontangkota.go.id/ows", "https://localhost/ows", "https://10.1.2.3/ows"):
        r = client.post("/api/sources/inspect", json={"url": url})
        assert r.status_code == 400, url
        assert r.json()["detail"]


def test_id_tidak_bisa_traversal(client):
    assert client.delete("/api/layers/..").status_code == 404
    assert client.get("/api/layers/x..y%2F..%2F/data").status_code == 404
