-- 0005: keputusan duplikat dalam batch (ADR-007) dan kelurahan administratif.
--  * staging.bangunan_impor: salinan yang dikecualikan TETAP disimpan, dengan rujukan ke bangunan yang dipertahankan dan alasannya.
--  * core.bangunan.kelurahan_administratif: kelurahan menurut batas-kelurahan.norm.geojson (pencocokan spasial pusat footprint;
--    NULL bila di luar semua batas). Kolom `slug` tetap kelurahan SUMBER (pengelompokan tile dan urutan penomoran ID).

ALTER TABLE staging.bangunan_impor
    ADD COLUMN kelurahan_administratif text,
    ADD COLUMN rujukan_urut            integer,                          -- urut bangunan yang dipertahankan (untuk salinan yang dikecualikan)
    ADD COLUMN rujukan_id              text REFERENCES core.registri_id (id), -- ID bangunan yang dipertahankan (diisi saat penerbitan)
    ADD COLUMN alasan_keputusan        text;

ALTER TABLE core.bangunan ADD COLUMN kelurahan_administratif text;
COMMENT ON COLUMN core.bangunan.kelurahan_administratif IS
    'Slug kelurahan menurut batas administratif (pusat footprint, atau pusat bounding box bila tanpa footprint); NULL bila di luar semua batas. slug = kelurahan sumber.';
CREATE INDEX bangunan_kelurahan_administratif ON core.bangunan (kelurahan_administratif);
