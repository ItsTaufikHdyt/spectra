"""Parser streaming CityGML 2.0 dan 3.0 -> bangunan mentah (READ-ONLY terhadap berkas sumber).

Berkas dibaca per blok (16 MB) dan dipotong per <cityObjectMember>; tiap potongan kecil di-parse dengan
ElementTree. Berkas 3,5 GB TIDAK dimuat utuh ke memori. Yang dikembalikan masih "mentah": label permukaan
dari sumber belum dipercaya (lihat geometri.py untuk pembersihan).
"""

from __future__ import annotations

import codecs
import re
import xml.etree.ElementTree as ET
from collections import namedtuple
from pathlib import Path
from typing import Iterator

BLOK = 1 << 24  # 16 MB
GML_ID = ("{http://www.opengis.net/gml}id", "{http://www.opengis.net/gml/3.2}id")  # GML 3.1 (CityGML 2.0) / GML 3.2 (3.0)
PERMUKAAN = {
    "WallSurface", "RoofSurface", "GroundSurface", "ClosureSurface", "OuterCeilingSurface",
    "OuterFloorSurface", "FloorSurface", "CeilingSurface", "InteriorWallSurface",
}
GENERIK = {"stringAttribute", "intAttribute", "doubleAttribute", "measureAttribute", "dateAttribute", "uriAttribute"}

# Satu poligon sumber: cincin luar/dalam tanpa titik penutup, label permukaan dari sumber (tidak dipercaya), LOD.
Poligon = namedtuple("Poligon", "luar dalam label lod")
BangunanMentah = namedtuple("BangunanMentah", "gml_id atribut poligon n_bagian")
Header = namedtuple("Header", "versi srs_name srs_dimensi envelope")


def _lokal(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _gml_id(el) -> str | None:
    return el.get(GML_ID[0]) or el.get(GML_ID[1])


def _jenis_ns(ns: str) -> str:
    if "generics" in ns:
        return "gen"
    if "building" in ns:
        return "bldg"
    if "construction" in ns:
        return "con"
    if ns.startswith("http://www.opengis.net/gml"):
        return "gml"
    if ns.startswith("http://www.opengis.net/citygml/") and ns.rsplit("/", 1)[-1] in ("2.0", "3.0"):
        return "core"
    return ns


def _titik(el) -> list[tuple[float, float, float]]:
    """Titik (x, y, z) dari gml:pos atau gml:posList di dalam LinearRing."""
    hasil = []
    for c in el:
        t = _lokal(c.tag)
        if t == "pos":
            v = c.text.split()
            hasil.append((float(v[0]), float(v[1]), float(v[2]) if len(v) > 2 else 0.0))
        elif t == "posList":
            v = c.text.split()
            for i in range(0, len(v) - 2, 3):
                hasil.append((float(v[i]), float(v[i + 1]), float(v[i + 2])))
    return hasil


def _tanpa_penutup(ring: list) -> list:
    return ring[:-1] if len(ring) > 1 and ring[0] == ring[-1] else ring


def _cincin(poligon_el, nama: str) -> list[list]:
    hasil = []
    for c in poligon_el:
        if _lokal(c.tag) == nama:
            for lr in c:
                if _lokal(lr.tag) == "LinearRing":
                    hasil.append(_tanpa_penutup(_titik(lr)))
    return hasil


def _kumpulkan(el, label, lod, keluar: list) -> None:
    for c in el:
        t = _lokal(c.tag)
        if t in PERMUKAAN:
            _kumpulkan(c, t, lod, keluar)
        elif t == "Polygon":
            luar = _cincin(c, "exterior")
            if luar and len(luar[0]) >= 3:
                keluar.append(Poligon(luar[0], _cincin(c, "interior"), label, lod))
        elif t.startswith("lod"):
            _kumpulkan(c, label, t, keluar)
        else:
            _kumpulkan(c, label, lod, keluar)


def _atribut(b) -> tuple[dict, int]:
    """Atribut sederhana bangunan: {'bldg:measuredHeight': ('3.21', 'm'), 'gen:Nama': (...), ...} dan jumlah BuildingPart."""
    atribut, n_bagian = {}, 0
    for c in b:
        t = _lokal(c.tag)
        ns = c.tag[1:].split("}")[0] if c.tag.startswith("{") else ""
        if t == "boundedBy" or t == "boundary" or t.startswith("lod"):
            continue
        if t == "consistsOfBuildingPart":
            n_bagian += 1
            continue
        jenis = _jenis_ns(ns)
        if jenis == "gen" and t in GENERIK:
            nilai = c.find(f"{{{ns}}}value")
            nama = c.get("name") or (c.find(f"{{{ns}}}name").text if c.find(f"{{{ns}}}name") is not None else "?")
            atribut[f"gen:{nama}"] = (nilai.text if nilai is not None else None, nilai.get("uom") if nilai is not None else None)
        elif jenis in ("bldg", "core", "gml", "con") and len(c) == 0:
            atribut[f"{jenis}:{t}"] = ((c.text or "").strip(), c.get("uom"))
    return atribut, n_bagian


def baca_header(path: Path) -> Header:
    """Versi CityGML (dari namespace), srsName, srsDimension, dan envelope dari 64 KB pertama."""
    with open(path, "rb") as f:
        kepala = f.read(65536).decode("utf-8", "replace")
    m = re.search(r"<core:CityModel[^>]*>", kepala) or re.search(r"<[A-Za-z:]*CityModel[^>]*>", kepala)
    akar = m.group(0) if m else ""
    ns = re.search(r'xmlns:core="([^"]+)"', akar) or re.search(r'xmlns="([^"]+)"', akar)
    versi = ns.group(1).rsplit("/", 1)[-1] if ns else None
    env = re.search(
        r"<gml:Envelope([^>]*)>\s*<gml:lowerCorner>([^<]*)</gml:lowerCorner>\s*<gml:upperCorner>([^<]*)</gml:upperCorner>", kepala
    )
    srs = dim = envelope = None
    if env:
        s = re.search(r'srsName="([^"]*)"', env.group(1))
        d = re.search(r'srsDimension="([^"]*)"', env.group(1))
        srs, dim = (s.group(1) if s else None), (d.group(1) if d else None)
        envelope = (list(map(float, env.group(2).split())), list(map(float, env.group(3).split())))
    return Header(versi, srs, dim, envelope)


def epsg_dari_srs(srs_name: str | None) -> int | None:
    """'http://www.opengis.net/def/crs/EPSG/0/32650' -> 32650."""
    m = re.search(r"(\d{4,6})\s*$", srs_name or "")
    return int(m.group(1)) if m else None


def iter_bangunan(path: Path) -> Iterator[BangunanMentah]:
    """Hasilkan satu BangunanMentah per <cityObjectMember> berisi Building; berkas dibaca streaming."""
    with open(path, "rb") as f0:
        kepala = f0.read(65536).decode("utf-8", "replace")
    m = re.search(r"<core:CityModel[^>]*>", kepala) or re.search(r"<[A-Za-z:]*CityModel[^>]*>", kepala)
    nsdecl = " ".join(re.findall(r'xmlns(?::[A-Za-z0-9]+)?="[^"]+"', m.group(0) if m else ""))
    tiga = re.search(r"<cityObjectMember[ >]", kepala) is not None  # CityGML 3.0: tanpa prefiks 'core:'
    buka = "<cityObjectMember" if tiga else "<core:cityObjectMember"
    tutup = "</cityObjectMember>" if tiga else "</core:cityObjectMember>"
    dec = codecs.getincrementaldecoder("utf-8")()
    buf = ""

    def kuras(akhir: bool) -> Iterator[BangunanMentah]:
        nonlocal buf
        while True:
            i = buf.find(buka)
            if i < 0:
                buf = "" if akhir else buf[-len(buka):]
                return
            j = buf.find(tutup, i)
            if j < 0:
                buf = buf[i:]
                return
            potongan = buf[i:j + len(tutup)].replace(buka, f"{buka} {nsdecl}", 1)
            buf = buf[j + len(tutup):]
            el = ET.fromstring(potongan)
            for anak in el:
                if _lokal(anak.tag) == "Building":
                    atribut, n_bagian = _atribut(anak)
                    poligon: list[Poligon] = []
                    _kumpulkan(anak, None, None, poligon)
                    yield BangunanMentah(_gml_id(anak), atribut, poligon, n_bagian)

    with open(path, "rb") as f:
        while True:
            blok = f.read(BLOK)
            if not blok:
                break
            buf += dec.decode(blok)
            yield from kuras(False)
    buf += dec.decode(b"", True)
    yield from kuras(True)
