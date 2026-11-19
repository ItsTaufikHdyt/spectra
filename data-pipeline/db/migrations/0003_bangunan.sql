-- 0003: core.bangunan (PRD §6.1, ADR-002/003) dan core.bangunan_riwayat (DIRENCANAKAN).

CREATE TABLE core.bangunan (
    id                      text PRIMARY KEY REFERENCES core.registri_id (id),
    gml_id                  text,                                 -- rujukan sumber, boleh tidak unik
    slug                    text NOT NULL,
    sumber_file             text NOT NULL,                        -- nama berkas .gml asal
    sumber_part             text,                                 -- 'I', 'II', ... (null bila berkas tunggal)
    footprint               geometry(MultiPolygon, 32650),        -- null bila tanpa poligon dasar (qc_flag 'tanpa_footprint')
    -- Pusat footprint (centroid) untuk pencocokan registri (ADR-003); dihitung otomatis.
    pusat_footprint         geometry(Point, 32650) GENERATED ALWAYS AS (ST_Centroid(footprint)) STORED,
    -- Geometri LOD2 bersih, Z dasar = 0 (ADR-002). Dipilih POLYHEDRALSURFACE Z: kumpulan poligon 3D
    -- (dinding, atap, lantai) tanpa mengharuskan solid tertutup; sumber sering tidak tertutup sempurna,
    -- sehingga tipe Solid/TIN tidak sesuai. Jenis tiap permukaan disimpan sejajar di jenis_permukaan.
    geometri_lod2           geometry(PolyhedralSurfaceZ, 32650),
    jenis_permukaan         text[] NOT NULL DEFAULT '{}',         -- 'G' lantai, 'R' atap, 'W' dinding; urutan = urutan poligon di geometri_lod2
    tinggi                  numeric(8, 3),                        -- Zmaks - Zmin setelah normalisasi (m)
    jumlah_lantai           integer,                              -- storeysAboveGround; null bila sumber kosong (tidak ditebak)
    luas_tapak              numeric(12, 2),                       -- luas footprint (m2)
    z_dasar_sumber          numeric(9, 3),                        -- Zmin asli sebelum dinormalkan ke 0
    epsg_sumber             integer,                              -- EPSG yang tertulis di berkas
    epsg_dikoreksi          integer,                              -- EPSG yang dipakai bila label dikoreksi; null bila tidak
    measured_height_sumber  numeric(8, 3),                        -- measuredHeight sumber (pembanding)
    qc_flag                 text[] NOT NULL DEFAULT '{}',
    batch_id                bigint NOT NULL REFERENCES staging.import_batch (id),
    dibuat_pada             timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX bangunan_footprint_gist ON core.bangunan USING gist (footprint);
CREATE INDEX bangunan_pusat_gist ON core.bangunan USING gist (pusat_footprint);
CREATE INDEX bangunan_slug ON core.bangunan (slug);
CREATE INDEX bangunan_gml_id ON core.bangunan (gml_id);
CREATE INDEX bangunan_batch ON core.bangunan (batch_id);
CREATE INDEX bangunan_qc_flag ON core.bangunan USING gin (qc_flag);

-- Riwayat versi (ADR-003: perubahan geometri/tinggi memakai ID yang sama, versi baru di riwayat).
-- DIRENCANAKAN: tabel dibuat KOSONG; pipeline uji coba belum mengisinya. Isi final ditetapkan
-- saat impor resmi. Struktur minimal: satu baris per versi, snapshot kolom bangunan dalam jsonb.
CREATE TABLE core.bangunan_riwayat (
    id              text NOT NULL REFERENCES core.registri_id (id),
    versi           integer NOT NULL,
    batch_id        bigint NOT NULL REFERENCES staging.import_batch (id),
    berlaku_dari    timestamptz NOT NULL DEFAULT now(),
    berlaku_sampai  timestamptz,
    data            jsonb NOT NULL,
    PRIMARY KEY (id, versi)
);
COMMENT ON TABLE core.bangunan_riwayat IS 'DIRENCANAKAN: riwayat versi bangunan (ADR-003). Belum diisi oleh pipeline.';
COMMENT ON TABLE core.bangunan IS 'Bangunan hasil impor CityGML yang dibersihkan (ADR-002/004). Z dasar = 0; z_dasar_sumber menyimpan Z asli.';
