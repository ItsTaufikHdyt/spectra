"""Satu bangunan mentah -> bangunan bersih (ADR-002): buang salinan, klasifikasi ulang permukaan, Z dasar = 0,
footprint, tinggi, atribut, dan flag QC. Tanpa berkas, tanpa basis data."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import geometri as g
from .parser import BangunanMentah

LABEL_SUMBER = {"GroundSurface": "G", "RoofSurface": "R", "WallSurface": "W"}
AMBANG_Z_DASAR = 0.05      # |Z dasar sumber| > 5 cm = tidak nol (dasar normal sumber 0,001 m)
AMBANG_TINGGI_MIN = 0.1    # m: di bawah ini tidak masuk tile
AMBANG_TAPAK_MIN = 2.0     # m2
AMBANG_TINGGI_BEDA = 0.05  # m: selisih tinggi hitung vs measuredHeight sumber
AMBANG_TINGGI_BESAR = 40.0 # m


@dataclass
class BangunanBersih:
    gml_id: str | None
    slug: str
    sumber_file: str
    sumber_part: str | None
    permukaan: list = field(default_factory=list)   # [(jenis, luar, [dalam,...]), ...]; Z dasar = 0, normal menghadap keluar
    footprint: object = None                        # shapely MultiPolygon atau None
    z_dasar_sumber: float | None = None
    tinggi: float | None = None
    jumlah_lantai: int | None = None
    luas_tapak: float | None = None
    measured_height_sumber: float | None = None
    epsg_sumber: int | None = None
    epsg_dikoreksi: int | None = None
    qc_flag: list = field(default_factory=list)
    stat: dict = field(default_factory=dict)

    @property
    def jenis_permukaan(self) -> list[str]:
        return [p[0] for p in self.permukaan]


def _angka(atribut: dict, kunci: str, tipe):
    nilai = (atribut.get(kunci) or (None,))[0]
    try:
        return tipe(nilai) if nilai not in (None, "") else None
    except ValueError:
        return None


def bersihkan(
    mentah: BangunanMentah, *, slug: str, sumber_file: str, sumber_part: str | None, epsg_sumber: int | None, epsg_dipakai: int | None
) -> BangunanBersih:
    hasil = BangunanBersih(
        mentah.gml_id, slug, sumber_file, sumber_part, epsg_sumber=epsg_sumber,
        epsg_dikoreksi=epsg_dipakai if epsg_dipakai != epsg_sumber else None,
        jumlah_lantai=_angka(mentah.atribut, "bldg:storeysAboveGround", int),
        measured_height_sumber=_angka(mentah.atribut, "bldg:measuredHeight", float),
    )
    if hasil.epsg_dikoreksi:
        hasil.qc_flag.append("epsg_dikoreksi")
    if not mentah.poligon:
        hasil.qc_flag.append("tanpa_geometri")
        hasil.stat = {"n_poligon_sumber": 0}
        return hasil

    semua = [t for p in mentah.poligon for t in p.luar]
    zmin, zmax = min(t[2] for t in semua), max(t[2] for t in semua)
    pusat = ((min(t[0] for t in semua) + max(t[0] for t in semua)) / 2, (min(t[1] for t in semua) + max(t[1] for t in semua)) / 2)
    hasil.z_dasar_sumber = round(zmin, 3)
    hasil.tinggi = round(zmax - zmin, 3)
    if abs(zmin) > AMBANG_Z_DASAR:
        hasil.qc_flag.append("z_dasar_tidak_nol_di_sumber")

    unik, terbalik, searah = g.buang_salinan(mentah.poligon)
    jenis_hitung = {"G": 0, "R": 0, "W": 0}
    label_beda = 0
    dasar = []
    for p in unik:
        jenis = g.klasifikasi(p.luar, zmin)
        jenis_hitung[jenis] += 1
        if LABEL_SUMBER.get(p.label) not in (None, jenis):
            label_beda += 1
        luar = g.normalkan_z(g.orientasi_keluar(p.luar, jenis, pusat), zmin)
        dalam = [g.normalkan_z(h, zmin) for h in p.dalam]
        hasil.permukaan.append((jenis, luar, dalam))
        if jenis == "G":
            dasar.append(type(p)(luar, dalam, p.label, p.lod))

    hasil.footprint, tidak_valid = g.footprint(dasar)
    hasil.stat = {
        "n_poligon_sumber": len(mentah.poligon), "n_salinan_terbalik": terbalik, "n_duplikat_searah": searah,
        "n_poligon_bersih": len(unik), "n_label_sumber_beda": label_beda, "jenis": jenis_hitung, "n_dasar_tidak_valid": tidak_valid,
    }
    if hasil.footprint is None:
        hasil.qc_flag.append("tanpa_footprint")
    else:
        hasil.luas_tapak = round(hasil.footprint.area, 2)
        if hasil.luas_tapak < AMBANG_TAPAK_MIN:
            hasil.qc_flag.append("footprint_kurang_2m2")
        if tidak_valid:
            hasil.qc_flag.append("footprint_diperbaiki")
    if hasil.tinggi < AMBANG_TINGGI_MIN:
        hasil.qc_flag.append("tinggi_kurang_0_1m")
    if hasil.tinggi > AMBANG_TINGGI_BESAR:
        hasil.qc_flag.append("tinggi_lebih_40m")
    if jenis_hitung["R"] == 0:
        hasil.qc_flag.append("tanpa_atap")
    if hasil.measured_height_sumber is not None:
        if hasil.measured_height_sumber == 0:
            hasil.qc_flag.append("tinggi_sumber_nol")
        elif abs(hasil.measured_height_sumber - hasil.tinggi) > AMBANG_TINGGI_BEDA:
            hasil.qc_flag.append("tinggi_sumber_beda")
    return hasil


def nomor_deskripsi(mentah: BangunanMentah) -> int | None:
    """Nomor di gml:description ('12, created by ...'); dipakai untuk pelacakan, BUKAN sebagai kunci."""
    m = re.match(r"\s*(\d+)", (mentah.atribut.get("gml:description") or ("",))[0] or "")
    return int(m.group(1)) if m else None
