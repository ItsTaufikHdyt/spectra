-- 0001: ekstensi PostGIS dan skema (ADR-001, PRD §9).
-- core     : data bangunan resmi (bangunan, registri ID)
-- ref      : data referensi (kelurahan, RT, sungai, kode)         -- kosong dulu
-- elevasi  : DTM/DEM dan elevasi dasar/lantai bangunan             -- kosong dulu (menunggu terrain)
-- sim      : hasil simulasi per skenario, dirujuk dengan ID bangunan (ADR-006) -- kosong dulu
-- staging  : impor mentah sementara dan catatan batch
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS ref;
CREATE SCHEMA IF NOT EXISTS elevasi;
CREATE SCHEMA IF NOT EXISTS sim;
CREATE SCHEMA IF NOT EXISTS staging;

COMMENT ON SCHEMA core IS 'Data bangunan: core.bangunan dan core.registri_id (ADR-003).';
COMMENT ON SCHEMA ref IS 'Data referensi (kelurahan, RT, sungai, kode). Kosong pada migrasi awal.';
COMMENT ON SCHEMA elevasi IS 'DTM/DEM dan elevasi dasar/lantai. DIRENCANAKAN; kosong sampai terrain tersedia.';
COMMENT ON SCHEMA sim IS 'Hasil simulasi dirujuk dengan ID bangunan (ADR-006). DIRENCANAKAN; kosong.';
COMMENT ON SCHEMA staging IS 'Impor mentah sementara dan catatan batch impor.';
