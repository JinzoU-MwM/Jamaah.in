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
        "IBU": "NYONYA",
        "MRS": "NYONYA",
        "MRS.": "NYONYA",
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
    }
    pekerjaan_aliases = {
        "SWASTA": "PEG. SWASTA",
        "PEGAWAISWASTA": "PEG. SWASTA",
        "KARYAWANSWASTA": "PEG. SWASTA",
        "WIRASWASTA": "WIRAUSAHA",
        "USAHASENDIRI": "WIRAUSAHA",
        "BELUMBEKERJA": "TIDAK BEKERJA",
    }

    for item in items:
        item.title = _map_value(getattr(item, "title", ""), title_lookup, title_aliases)
        item.jenis_identitas = _map_value(
            getattr(item, "jenis_identitas", ""),
            jenis_lookup,
            jenis_aliases,
        )
        item.kewarganegaraan = _map_value(
            getattr(item, "kewarganegaraan", ""),
            kewarg_lookup,
            kewarg_aliases,
        )
        item.status_pernikahan = _map_value(
            getattr(item, "status_pernikahan", ""),
            pernikahan_lookup,
            pernikahan_aliases,
        )
        item.pendidikan = _map_value(
            getattr(item, "pendidikan", ""),
            pendidikan_lookup,
            pendidikan_aliases,
        )
        item.pekerjaan = _map_value(
            getattr(item, "pekerjaan", ""),
            pekerjaan_lookup,
            pekerjaan_aliases,
        )
        item.provider_visa = _map_value(getattr(item, "provider_visa", ""), provider_lookup)
        item.asuransi = _map_value(getattr(item, "asuransi", ""), asuransi_lookup)
        item.provinsi = _map_value(getattr(item, "provinsi", ""), provinsi_lookup)

        provinsi = _normalize(getattr(item, "provinsi", ""))
        kabupaten = _normalize(getattr(item, "kabupaten", ""))
        if kabupaten and provinsi:
            named_range = provinsi.replace(" ", "_")
            kabupaten_lookup = kabupaten_lookup_by_named_range.get(named_range, {})
            item.kabupaten = _map_value(kabupaten, kabupaten_lookup)


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
