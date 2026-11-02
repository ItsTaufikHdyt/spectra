#!/usr/bin/env python3
"""Uji mandiri adapter (tanpa jaringan): pengaman read-only, deteksi sumbu, paging CSW, ISO 19139.

Jalankan: data-pipeline/.venv/bin/python data-pipeline/scripts/test_sources.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sources.ogc_xml import parse_csw_search, parse_iso_record  # noqa: E402
from sources.remote_http import assert_read_only  # noqa: E402
from sources.wfs import detect_axis_order  # noqa: E402

# 1. Operasi tulis ditolak sebelum request dikirim (termasuk variasi kapital kunci).
for op in ("Transaction", "Harvest", "LockFeature", "GetFeatureWithLock", "CreateStoredQuery", None):
    try:
        assert_read_only({"REQUEST": op} if op else {})
    except PermissionError:
        pass
    else:
        raise AssertionError(f"{op} seharusnya ditolak")
for op in ("GetCapabilities", "DescribeFeatureType", "GetFeature", "GetRecords", "GetRecordById"):
    assert_read_only({"request": op})

# 2. Urutan sumbu: bbox Bontang lon/lat vs tertukar lat/lon.
ref = (117.388, 0.022, 117.566, 0.206)
assert detect_axis_order(ref, ref)[0] == "lonlat"
assert detect_axis_order((0.022, 117.388, 0.206, 117.566), ref)[0] == "latlon"
try:
    detect_axis_order((100, 10, 101, 11), ref)
    raise AssertionError("extent tak cocok seharusnya error")
except ValueError:
    pass

# 2b. Extent satu titik (IoU 0): dipakai uji "di dalam extent referensi".
assert detect_axis_order((117.45, 0.1, 117.45, 0.1), ref) == ("lonlat", 0.0)
assert detect_axis_order((0.1, 117.45, 0.1, 117.45), ref) == ("latlon", 0.0)

# 2c. Mode generik: field nama ditebak tanpa peduli kapital; bisa diganti lewat field_nama.
from sources.base import Source, guess_name_field  # noqa: E402

assert guess_name_field(["fid", "NAMA", "luas"]) == "NAMA"
assert guess_name_field(["fid", "Keterangan", "name"]) == "name"  # urutan prioritas NAME_FIELDS
assert guess_name_field(["fid", "luas"]) is None
assert guess_name_field(["fid", "alamat_edt", "nama_edt"]) == "nama_edt"  # awalan, bila tak ada yang persis
assert guess_name_field(["namobj", "nama"]) == "nama"  # persis menang atas awalan
_feats = [{"type": "Feature", "properties": {"fid": 7, "Name": "Posyandu A", "kode": "X1"},
           "geometry": {"type": "Point", "coordinates": [117.45, 0.1]}}]
_g = Source({"id": "uji", "layer": "posyandu", "generik": True}, kelurahan_map={}).standardize(_feats, "EPSG:4326")
assert _g.iloc[0]["nama"] == "Posyandu A" and _g.iloc[0]["fid_sumber"] == "7" and _g.iloc[0]["kelurahan"] is None
_g = Source({"id": "uji", "layer": "posyandu", "generik": True, "field_nama": "kode"}, kelurahan_map={}).standardize(_feats, "EPSG:4326")
assert _g.iloc[0]["nama"] == "X1"
try:  # tanpa generik, layer asing tetap ditolak (perilaku lama)
    Source({"id": "uji", "layer": "posyandu"}, kelurahan_map={}).standardize(_feats, "EPSG:4326")
    raise AssertionError("layer asing tanpa generik seharusnya ditolak")
except ValueError:
    pass

# 3. CSW: halaman terakhir (nextRecord=0) + ISO 19139 minimal.
XML = b"""<csw:GetRecordsResponse xmlns:csw="http://www.opengis.net/cat/csw/2.0.2"
  xmlns:gmd="http://www.isotc211.org/2005/gmd" xmlns:gco="http://www.isotc211.org/2005/gco">
 <csw:SearchResults numberOfRecordsMatched="25" numberOfRecordsReturned="1" nextRecord="0">
  <gmd:MD_Metadata>
   <gmd:fileIdentifier><gco:CharacterString>abc</gco:CharacterString></gmd:fileIdentifier>
   <gmd:hierarchyLevel><gmd:MD_ScopeCode codeListValue="dataset"/></gmd:hierarchyLevel>
   <gmd:identificationInfo><gmd:MD_DataIdentification>
    <gmd:citation><gmd:CI_Citation><gmd:title><gco:CharacterString>Sungai</gco:CharacterString></gmd:title></gmd:CI_Citation></gmd:citation>
    <gmd:abstract><gco:CharacterString>Abstrak</gco:CharacterString></gmd:abstract>
    <gmd:extent><gmd:EX_Extent><gmd:geographicElement><gmd:EX_GeographicBoundingBox>
     <gmd:westBoundLongitude><gco:Decimal>117.4</gco:Decimal></gmd:westBoundLongitude>
     <gmd:southBoundLatitude><gco:Decimal>0.02</gco:Decimal></gmd:southBoundLatitude>
     <gmd:eastBoundLongitude><gco:Decimal>117.5</gco:Decimal></gmd:eastBoundLongitude>
     <gmd:northBoundLatitude><gco:Decimal>0.2</gco:Decimal></gmd:northBoundLatitude>
    </gmd:EX_GeographicBoundingBox></gmd:geographicElement></gmd:EX_Extent></gmd:extent>
   </gmd:MD_DataIdentification></gmd:identificationInfo>
   <gmd:distributionInfo><gmd:MD_Distribution><gmd:transferOptions><gmd:MD_DigitalTransferOptions><gmd:onLine>
    <gmd:CI_OnlineResource><gmd:linkage><gmd:URL>https://x/ows</gmd:URL></gmd:linkage>
     <gmd:protocol><gco:CharacterString>OGC:WFS</gco:CharacterString></gmd:protocol>
     <gmd:name><gco:CharacterString>geonode:sungai_ln_5k</gco:CharacterString></gmd:name></gmd:CI_OnlineResource>
   </gmd:onLine></gmd:MD_DigitalTransferOptions></gmd:transferOptions></gmd:MD_Distribution></gmd:distributionInfo>
  </gmd:MD_Metadata>
 </csw:SearchResults>
</csw:GetRecordsResponse>"""
page = parse_csw_search(XML)
assert (page["matched"], page["returned"], page["next"]) == (25, 1, 0)
rec = parse_iso_record(page["records"][0])
assert rec["id"] == "abc" and rec["judul"] == "Sungai" and rec["tipe"] == "dataset"
assert rec["bbox_wgs84"] == [117.4, 0.02, 117.5, 0.2]
assert rec["layer"] == ["geonode:sungai_ln_5k"]

print("test_sources: semua uji lulus")
