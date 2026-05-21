"""
Validation helpers to ensure exported rows follow Siskopatuh template dropdown options.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable
import re

from openpyxl import load_workbook


@dataclass(frozen=True)
class SiskopatuhDropdownRules:
    titles: frozenset[str]
    jenis_identitas: frozenset[str]
    kewarganegaraan: frozenset[str]
    status_pernikahan: frozenset[str]
    pendidikan: frozenset[str]
    pekerjaan: frozenset[str]
    provider_visa: frozenset[str]
    asuransi: frozenset[str]
    provinsi: frozenset[str]
    kabupaten_by_named_range: dict[str, frozenset[str]]


def _normalize(value: str | None) -> str:
    return (value or "").strip()


def _lookup_key(value: str | None) -> str:
    normalized = _normalize(value).upper()
    normalized = re.sub(r"[^A-Z0-9]+", "", normalized)
    return normalized


def _iter_named_range_values(workbook, range_name: str) -> list[str]:
    defined_name = workbook.defined_names.get(range_name)
    if not defined_name:
        return []

    values: list[str] = []
    seen: set[str] = set()
    destinations = list(defined_name.destinations)
    for sheet_name, cell_range in destinations:
        worksheet = workbook[sheet_name]
        for row in worksheet[cell_range]:
            cells = row if isinstance(row, tuple) else (row,)
            for cell in cells:
                value = _normalize(str(cell.value) if cell.value is not None else "")
                if value and value not in seen:
                    seen.add(value)
                    values.append(value)
    return values


def _resolve_template_path() -> Path:
    repo_root = Path(__file__).resolve().parents[3]
    backend_root = Path(__file__).resolve().parents[2]
    candidates = (
        backend_root / "templates" / "jamaah.xlsm",
        repo_root / "template jamaah.xlsm",
    )
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        "Siskopatuh template not found. Expected one of: "
        f"{candidates[0]} or {candidates[1]}"
    )


@lru_cache(maxsize=1)
def get_siskopatuh_dropdown_rules() -> SiskopatuhDropdownRules:
    workbook = load_workbook(_resolve_template_path(), data_only=False, keep_vba=True)

    provinsi_values = _iter_named_range_values(workbook, "Propinsi")
    kabupaten_by_named_range: dict[str, frozenset[str]] = {}
    for provinsi in provinsi_values:
        named_range = provinsi.replace(" ", "_")
        kabupaten_values = _iter_named_range_values(workbook, named_range)
        if kabupaten_values:
            kabupaten_by_named_range[named_range] = frozenset(kabupaten_values)

    return SiskopatuhDropdownRules(
        titles=frozenset(_iter_named_range_values(workbook, "Gelar")),
        jenis_identitas=frozenset(_iter_named_range_values(workbook, "JenisIdentitas")),
        kewarganegaraan=frozenset(_iter_named_range_values(workbook, "StatusKewarganegaraan")),
        status_pernikahan=frozenset(_iter_named_range_values(workbook, "StatusPernikahan")),
        pendidikan=frozenset(_iter_named_range_values(workbook, "JenisPendidikan")),
        pekerjaan=frozenset(_iter_named_range_values(workbook, "JenisPekerjaan")),
        provider_visa=frozenset(_iter_named_range_values(workbook, "ProviderVisa")),
        asuransi=frozenset(_iter_named_range_values(workbook, "ASURANSI")),
        provinsi=frozenset(provinsi_values),
        kabupaten_by_named_range=kabupaten_by_named_range,
    )


def _validate_allowed(
    *,
    row_number: int,
    field_label: str,
    value: str | None,
    allowed_values: Iterable[str],
    errors: list[str],
) -> None:
    normalized = _normalize(value)
    if not normalized:
        return
    allowed = set(allowed_values)
    if normalized not in allowed:
        errors.append(f"Row {row_number}: '{field_label}' tidak valid ('{normalized}').")


def _build_lookup(values: Iterable[str]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for value in values:
        key = _lookup_key(value)
        if key and key not in lookup:
            lookup[key] = value
    return lookup


def _map_value(value: str | None, lookup: dict[str, str], aliases: dict[str, str] | None = None) -> str:
    normalized = _normalize(value)
    if not normalized:
        return ""

    key = _lookup_key(normalized)
    alias_target = (aliases or {}).get(key)
    if alias_target:
        normalized = alias_target
        key = _lookup_key(normalized)

    return lookup.get(key, normalized)


def normalize_items_to_siskopatuh_dropdowns(items: list) -> None:
    rules = get_siskopatuh_dropdown_rules()

    title_lookup = _build_lookup(rules.titles)
    jenis_lookup = _build_lookup(rules.jenis_identitas)
    kewarg_lookup = _build_lookup(rules.kewarganegaraan)
    pernikahan_lookup = _build_lookup(rules.status_pernikahan)
    pendidikan_lookup = _build_lookup(rules.pendidikan)
    pekerjaan_lookup = _build_lookup(rules.pekerjaan)
    provider_lookup = _build_lookup(rules.provider_visa)
    asuransi_lookup = _build_lookup(rules.asuransi)
    provinsi_lookup = _build_lookup(rules.provinsi)
    kabupaten_lookup_by_named_range = {
        named: _build_lookup(values)
        for named, values in rules.kabupaten_by_named_range.items()
    }

    title_aliases = {
        "BAPAK": "TUAN",
        "PAK": "TUAN",
        "MR": "TUAN",
        "MISTER": "TUAN",
        "SDR": "TUAN",
        "SAUDARA": "TUAN",
        "H": "TUAN",
        "HAJI": "TUAN",
        "DR": "TUAN",
        "DOKTER": "TUAN",
        "IBU": "NYONYA",
        "MRS": "NYONYA",
        "MRS.": "NYONYA",
        "HJ": "NYONYA",
        "HAJJAH": "NYONYA",
        "MS": "NONA",
        "MISS": "NONA",
    }
    jenis_aliases = {
        "KTP": "NIK",
        "KITP": "KITAP",
        "PASSPORT": "PASPOR",
    }
    kewarg_aliases = {
        "INDONESIA": "WNI",
        "WARGANEGARAINDONESIA": "WNI",
        "WNINDONESIA": "WNI",
    }
    pernikahan_aliases = {
        "BELUMKAWIN": "BELUM MENIKAH",
        "TIDAKKAWIN": "BELUM MENIKAH",
        "KAWIN": "MENIKAH",
        "SUDAHKAWIN": "MENIKAH",
        "MENIKAH": "MENIKAH",
        "CERAI": "JANDA / DUDA",
        "CERAIHIDUP": "JANDA / DUDA",
        "CERAIMATI": "JANDA / DUDA",
        "DUDA": "JANDA / DUDA",
        "JANDA": "JANDA / DUDA",
    }
    pendidikan_aliases = {
        "S1": "D4/S1",
        "D4": "D4/S1",
        "SARJANA": "D4/S1",
        "STRATA1": "D4/S1",
        "STRATAI": "D4/S1",
        "DIV": "D4/S1",
        "SMA": "SMA/MA",
        "SMU": "SMA/MA",
        "SLTA": "SMA/MA",
        "SMK": "SMA/MA",
        "SMP": "SMP/MTS",
        "SLTP": "SMP/MTS",
        "SD": "SD/MI",
        "TIDAKADA": "TIDAK SEKOLAH",
        "TIDAKBERSYARAT": "TIDAK SEKOLAH",
        "BELUMSEKOLAH": "TIDAK SEKOLAH",
        "S2": "S2",
        "STRATA2": "S2",
        "MAGISTER": "S2",
        "PASCASARJANA": "S2",
        "S3": "S3",
        "STRATA3": "S3",
        "DOKTOR": "S3",
        "D3": "D3",
        "DIII": "D3",
        "DIPLOMA3": "D3",
        "AKADEMI": "D3",
    }
    pekerjaan_aliases = {
        "SWASTA": "PEG. SWASTA",
        "PEGAWAISWASTA": "PEG. SWASTA",
        "KARYAWANSWASTA": "PEG. SWASTA",
        "KARYAWAN": "PEG. SWASTA",
        "BURUH": "PEG. SWASTA",
        "KONTRAKTOR": "PEG. SWASTA",
        "WIRASWASTA": "WIRAUSAHA",
        "USAHASENDIRI": "WIRAUSAHA",
        "PEDAGANG": "WIRAUSAHA",
        "PENGUSAHA": "WIRAUSAHA",
        "BELUMBEKERJA": "TIDAK BEKERJA",
        "TIDAKBEKERJA": "TIDAK BEKERJA",
        "IBURUMAHTANGGA": "TIDAK BEKERJA",
        "IRT": "TIDAK BEKERJA",
        "RUMAHTANGGA": "TIDAK BEKERJA",
        "PELAJAR": "TIDAK BEKERJA",
        "MAHASISWA": "TIDAK BEKERJA",
        "PELAJARMAHASISWA": "TIDAK BEKERJA",
        "MAHASISWI": "TIDAK BEKERJA",
        "KARYAWANSWSTA": "PEG. SWASTA",
        "PNS": "PNS",
        "ASN": "PNS",
        "APARATURSIPILNEGARA": "PNS",
        "TNI": "TNI / POLRI",
        "POLRI": "TNI / POLRI",
        "POLISI": "TNI / POLRI",
        "LAINNYA": "LAINNYA",
        "GURU": "LAINNYA",
        "DOSEN": "LAINNYA",
        "DOKTER": "LAINNYA",
        "BIDAN": "LAINNYA",
        "PERAWAT": "LAINNYA",
        "PENSIUNAN": "LAINNYA",
        "PENDETA": "LAINNYA",
        "USTADZ": "LAINNYA",
        "SUPIR": "LAINNYA",
        "OJEK": "LAINNYA",
        "SATPAM": "LAINNYA",
    }

    for item in items:
        item.title = _map_value(getattr(item, "title", ""), title_lookup, title_aliases)
        if item.title and item.title not in title_lookup.values():
            item.title = "TUAN"
        item.jenis_identitas = _map_value(
            getattr(item, "jenis_identitas", ""),
            jenis_lookup,
            jenis_aliases,
        )
        if item.jenis_identitas and item.jenis_identitas not in jenis_lookup.values():
            item.jenis_identitas = "NIK"
        item.kewarganegaraan = _map_value(
            getattr(item, "kewarganegaraan", ""),
            kewarg_lookup,
            kewarg_aliases,
        )
        if item.kewarganegaraan and item.kewarganegaraan not in kewarg_lookup.values():
            item.kewarganegaraan = "WNI"
        item.status_pernikahan = _map_value(
            getattr(item, "status_pernikahan", ""),
            pernikahan_lookup,
            pernikahan_aliases,
        )
        if item.status_pernikahan and item.status_pernikahan not in pernikahan_lookup.values():
            item.status_pernikahan = "BELUM MENIKAH"
        item.pendidikan = _map_value(
            getattr(item, "pendidikan", ""),
            pendidikan_lookup,
            pendidikan_aliases,
        )
        if item.pendidikan and item.pendidikan not in pendidikan_lookup.values():
            item.pendidikan = "SMA/MA"
        item.pekerjaan = _map_value(
            getattr(item, "pekerjaan", ""),
            pekerjaan_lookup,
            pekerjaan_aliases,
        )
        if item.pekerjaan and item.pekerjaan not in pekerjaan_lookup.values():
            item.pekerjaan = "LAINNYA"
        item.provider_visa = _map_value(getattr(item, "provider_visa", ""), provider_lookup)
        if item.provider_visa and item.provider_visa not in provider_lookup.values():
            item.provider_visa = "B2C"
        item.asuransi = _map_value(getattr(item, "asuransi", ""), asuransi_lookup)
        if item.asuransi and item.asuransi not in asuransi_lookup.values():
            for prefix in ("PT. ASURANSI ", "PT ASURANSI ", "PT. ", "PT ", "ASURANSI "):
                if item.asuransi.upper().startswith(prefix.upper()):
                    stripped = item.asuransi[len(prefix):].strip()
                    if not stripped:
                        continue
                    stripped_mapped = _map_value(stripped, asuransi_lookup)
                    if stripped_mapped != stripped:
                        item.asuransi = stripped_mapped
                        break
                    asuransi_key = _lookup_key(stripped)
                    for allowed_val in asuransi_lookup.values():
                        allowed_key = _lookup_key(allowed_val)
                        if asuransi_key in allowed_key or allowed_key in asuransi_key:
                            item.asuransi = allowed_val
                            break
                    if item.asuransi not in asuransi_lookup.values():
                        continue
                    break
            if item.asuransi and item.asuransi not in asuransi_lookup.values():
                asuransi_key = _lookup_key(item.asuransi)
                for allowed_val in asuransi_lookup.values():
                    allowed_key = _lookup_key(allowed_val)
                    if asuransi_key in allowed_key or allowed_key in asuransi_key:
                        item.asuransi = allowed_val
                        break
            if item.asuransi and item.asuransi not in asuransi_lookup.values():
                item.asuransi = ""
        item.provinsi = _map_value(getattr(item, "provinsi", ""), provinsi_lookup)
        if item.provinsi and item.provinsi not in provinsi_lookup.values():
            for prefix in ("PROVINSI ", "PROPINSI ", "PROV. ", "PROP. "):
                if item.provinsi.upper().startswith(prefix.upper()):
                    stripped = item.provinsi[len(prefix):].strip()
                    item.provinsi = _map_value(stripped, provinsi_lookup)
                    break
            if item.provinsi and item.provinsi not in provinsi_lookup.values():
                item.provinsi = ""

        provinsi = _normalize(getattr(item, "provinsi", ""))
        kabupaten = _normalize(getattr(item, "kabupaten", ""))
        if kabupaten and provinsi:
            named_range = provinsi.replace(" ", "_")
            kabupaten_lookup = kabupaten_lookup_by_named_range.get(named_range, {})
            mapped = _map_value(kabupaten, kabupaten_lookup)

            if mapped == kabupaten and kabupaten_lookup:
                for prefix in ("KABUPATEN ", "KOTA ", "KAB. ", "KAB "):
                    if kabupaten.upper().startswith(prefix.upper()):
                        stripped = kabupaten[len(prefix):].strip()
                        stripped_mapped = _map_value(stripped, kabupaten_lookup)
                        if stripped_mapped != stripped:
                            mapped = stripped_mapped
                            break
                        for add_prefix in ("KOTA ", "KAB. ", "KAB "):
                            prefixed = add_prefix + stripped
                            prefixed_mapped = _map_value(prefixed, kabupaten_lookup)
                            if prefixed_mapped != prefixed:
                                mapped = prefixed_mapped
                                break
                        if mapped != kabupaten:
                            break

            if mapped == kabupaten and kabupaten_lookup:
                for prefix in ("KOTA ", "KAB. ", "KAB ", "KABUPATEN "):
                    prefixed = prefix + kabupaten
                    prefixed_mapped = _map_value(prefixed, kabupaten_lookup)
                    if prefixed_mapped != prefixed:
                        mapped = prefixed_mapped
                        break

            if mapped == kabupaten and kabupaten_lookup:
                kab_key = _lookup_key(kabupaten)
                for allowed_val in kabupaten_lookup.values():
                    allowed_key = _lookup_key(allowed_val)
                    if kab_key in allowed_key or allowed_key in kab_key:
                        mapped = allowed_val
                        break

            item.kabupaten = mapped


def validate_items_against_siskopatuh_dropdowns(items: list) -> list[str]:
    rules = get_siskopatuh_dropdown_rules()
    errors: list[str] = []

    for index, item in enumerate(items, start=2):
        _validate_allowed(
            row_number=index,
            field_label="Title",
            value=getattr(item, "title", ""),
            allowed_values=rules.titles,
            errors=errors,
        )
        _validate_allowed(
            row_number=index,
            field_label="Jenis Identitas",
            value=getattr(item, "jenis_identitas", ""),
            allowed_values=rules.jenis_identitas,
            errors=errors,
        )
        _validate_allowed(
            row_number=index,
            field_label="KewargaNegaraan",
            value=getattr(item, "kewarganegaraan", ""),
            allowed_values=rules.kewarganegaraan,
            errors=errors,
        )
        _validate_allowed(
            row_number=index,
            field_label="Status Pernikahan",
            value=getattr(item, "status_pernikahan", ""),
            allowed_values=rules.status_pernikahan,
            errors=errors,
        )
        _validate_allowed(
            row_number=index,
            field_label="Pendidikan",
            value=getattr(item, "pendidikan", ""),
            allowed_values=rules.pendidikan,
            errors=errors,
        )
        _validate_allowed(
            row_number=index,
            field_label="Pekerjaan",
            value=getattr(item, "pekerjaan", ""),
            allowed_values=rules.pekerjaan,
            errors=errors,
        )
        _validate_allowed(
            row_number=index,
            field_label="Provider Visa",
            value=getattr(item, "provider_visa", ""),
            allowed_values=rules.provider_visa,
            errors=errors,
        )
        _validate_allowed(
            row_number=index,
            field_label="Asuransi",
            value=getattr(item, "asuransi", ""),
            allowed_values=rules.asuransi,
            errors=errors,
        )
        _validate_allowed(
            row_number=index,
            field_label="Provinsi",
            value=getattr(item, "provinsi", ""),
            allowed_values=rules.provinsi,
            errors=errors,
        )

        provinsi = _normalize(getattr(item, "provinsi", ""))
        kabupaten = _normalize(getattr(item, "kabupaten", ""))
        if kabupaten and provinsi:
            named_range = provinsi.replace(" ", "_")
            allowed_kabupaten = rules.kabupaten_by_named_range.get(named_range)
            if not allowed_kabupaten:
                errors.append(
                    f"Row {index}: Provinsi '{provinsi}' tidak memiliki referensi kabupaten di template."
                )
            elif kabupaten not in allowed_kabupaten:
                errors.append(
                    f"Row {index}: Kabupaten '{kabupaten}' tidak valid untuk provinsi '{provinsi}'."
                )

    return errors
