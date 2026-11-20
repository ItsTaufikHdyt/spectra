-- 0004: staging.bangunan_impor — hasil parse + pembersihan SEBELUM ID diterbitkan (impor resmi, tahap 'staging').
-- Alur: impor_resmi.py staging -> analisis (jumlah, duplikat dalam batch, EPSG/Z) -> keputusan -> impor_resmi.py terbit
-- (mengisi kolom id lewat core.registri_id, lalu menyalin ke core.bangunan). Tabel ini boleh dikosongkan setelah terbit.

CREATE TABLE staging.bangunan_impor (
    batch_id                bigint NOT NULL REFERENCES staging.import_batch (id),
    urut                    integer NOT NULL,                     -- urutan baca (konfigurasi, lalu urutan di berkas)
    slug                    text NOT NULL,
    sumber_file             text NOT NULL,
    sumber_part             text,
    gml_id                  text,
    nomor_deskripsi         integer,                              -- nomor di gml:description (pelacakan, bukan kunci)
    footprint               geometry(MultiPolygon, 32650),
    pusat_x                 double precision NOT NULL,            -- pusat footprint (atau pusat bbox bila tanpa footprint), untuk urutan ID
    pusat_y                 double precision NOT NULL,
    geometri_lod2           geometry(PolyhedralSurfaceZ, 32650),
    jenis_permukaan         text[] NOT NULL DEFAULT '{}',
    tinggi                  numeric(8, 3),
    jumlah_lantai           integer,
    luas_tapak              numeric(12, 2),
    z_dasar_sumber          numeric(9, 3),
    epsg_sumber             integer,
    epsg_dikoreksi          integer,
    measured_height_sumber  numeric(8, 3),
    qc_flag                 text[] NOT NULL DEFAULT '{}',
    stat                    jsonb NOT NULL DEFAULT '{}',          -- hitungan poligon (sumber, salinan terbalik, duplikat searah, ...)
    id                      text REFERENCES core.registri_id (id),-- diisi saat penerbitan ID; null = belum/tidak diterbitkan
    keputusan               text,                                 -- mis. 'kecualikan' (keputusan duplikat dalam batch); null = diterbitkan
    PRIMARY KEY (batch_id, urut)
);
CREATE INDEX bangunan_impor_footprint_gist ON staging.bangunan_impor USING gist (footprint);
CREATE INDEX bangunan_impor_slug ON staging.bangunan_impor (batch_id, slug);
COMMENT ON TABLE staging.bangunan_impor IS 'Bangunan hasil parse + pembersihan sebelum penerbitan ID (impor resmi). id null sampai tahap terbit.';
