-- 0002: catatan batch impor dan registri ID bangunan (ADR-003).

-- Satu baris per impor. jenis 'uji_coba' = hasilnya BUKAN registri resmi dan boleh di-reset.
CREATE TABLE staging.import_batch (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    waktu       timestamptz NOT NULL DEFAULT now(),
    jenis       text NOT NULL CHECK (jenis IN ('uji_coba', 'resmi')),
    sumber      text NOT NULL,          -- mis. 'raw/citygml/Kelurahan Bontang Lestari'
    catatan     text,
    ringkasan   jsonb                   -- hasil impor: cocok_gml_id, cocok_posisi, id_baru, nonaktif, tinjauan_manual, ...
);

-- Nomor ID berasal dari sekuens: nomor TIDAK PERNAH dipakai ulang (sekuens tidak mundur,
-- tidak berputar; nomor yang terlewat karena rollback tetap hilang).
CREATE SEQUENCE core.seq_nomor_bangunan AS integer MINVALUE 1 START 1 NO CYCLE;

CREATE TABLE core.registri_id (
    nomor             integer PRIMARY KEY DEFAULT nextval('core.seq_nomor_bangunan'),
    id                text GENERATED ALWAYS AS ('BTG-BLD-' || lpad(nomor::text, 6, '0')) STORED NOT NULL UNIQUE,
    gml_id            text,                                   -- rujukan, BOLEH tidak unik
    slug              text NOT NULL,                          -- kelurahan (api_api, bontang_lestari, ...)
    pusat_footprint   geometry(Point, 32650) NOT NULL,        -- pusat footprint sumber saat ID diterbitkan
    diterbitkan_pada  timestamptz NOT NULL DEFAULT now(),
    batch_id          bigint NOT NULL REFERENCES staging.import_batch (id),
    status            text NOT NULL CHECK (status IN ('aktif', 'nonaktif', 'uji_coba')),
    berlaku_sampai    date,                                   -- terisi bila nonaktif (bangunan hilang dari impor baru)
    CONSTRAINT nonaktif_punya_tanggal CHECK ((status = 'nonaktif') = (berlaku_sampai IS NOT NULL))
);

CREATE INDEX registri_id_pusat_gist ON core.registri_id USING gist (pusat_footprint);
CREATE INDEX registri_id_slug_gml ON core.registri_id (slug, gml_id);
CREATE INDEX registri_id_batch ON core.registri_id (batch_id);

-- Pengaman: ID resmi tidak boleh dihapus, dan nomor/ID tidak boleh diubah.
-- Baris berstatus 'uji_coba' boleh dihapus (registri uji coba bisa di-reset).
CREATE FUNCTION core.registri_id_jaga() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        IF OLD.status <> 'uji_coba' THEN
            RAISE EXCEPTION 'ID % berstatus % tidak boleh dihapus (tandai nonaktif)', OLD.id, OLD.status;
        END IF;
        RETURN OLD;
    END IF;
    IF NEW.nomor <> OLD.nomor THEN
        RAISE EXCEPTION 'nomor ID tidak boleh diubah (%)', OLD.id;
    END IF;
    IF OLD.status <> 'uji_coba' AND NEW.status = 'uji_coba' THEN
        RAISE EXCEPTION 'ID resmi % tidak boleh kembali ke uji_coba', OLD.id;
    END IF;
    RETURN NEW;
END $$;

CREATE TRIGGER registri_id_jaga_trg BEFORE UPDATE OR DELETE ON core.registri_id
    FOR EACH ROW EXECUTE FUNCTION core.registri_id_jaga();

COMMENT ON TABLE core.registri_id IS 'Registri ID BTG-BLD-xxxxxx (ADR-003). status=uji_coba: BUKAN registri resmi, boleh di-reset.';
