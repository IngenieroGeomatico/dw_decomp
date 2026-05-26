# extract_iso.py
import os
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from typing import List

import pycdlib  # pip install pycdlib


def extract_files_from_iso(
    iso_file: str,
    out_dir: str,
    files_to_extract: List[str],
) -> None:
    """
    Extrae los archivos especificados de una imagen ISO.

    Parámetros
    ----------
    iso_file : str
        Ruta al archivo ISO (p.ej. "bin/CodeWarrior for PlayStation Release 4.iso").
    out_dir : str
        Directorio donde se guardarán los archivos extraídos.
    files_to_extract : List[str]
        Lista de nombres de archivo a extraer (p.ej. ["cc_mips.dll"]).

    Notas
    -----
    - La función busca los archivos en el ISO usando Rock Ridge y Joliet.
    - Si se especifica solo el nombre de archivo, busca por coincidencia de nombre
      en cualquier subdirectorio.
    - Si no encuentra un archivo, se muestra un aviso.
    - Si existen varias coincidencias con el mismo nombre, se extraen todas.
    """
    iso_path = Path(iso_file)
    if not iso_path.is_file():
        raise FileNotFoundError(f"ISO no encontrado: {iso_path}")

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    def _is_raw_2352_iso(path: Path) -> bool:
        if path.stat().st_size % 2352 != 0:
            return False
        with path.open("rb") as fp:
            fp.seek(2352 * 16)
            sector = fp.read(22)
        return (
            len(sector) >= 22
            and sector[0:12] == b"\x00" + b"\xff" * 10 + b"\x00"
            and sector[15] in (1, 2)
            and sector[17:22] == b"CD001"
        )

    def _convert_raw_2352_to_iso(raw_path: Path, iso_path: Path) -> None:
        with raw_path.open("rb") as src, iso_path.open("wb") as dst:
            while True:
                sector = src.read(2352)
                if not sector:
                    break
                if len(sector) != 2352:
                    raise ValueError(
                        f"Imagen raw corrupta: sector incompleto en {raw_path}"
                    )
                mode = sector[15]
                if mode not in (1, 2):
                    raise ValueError(
                        f"Sector no es modo 1/2 de datos en imagen raw: modo={mode}"
                    )
                dst.write(sector[16:16 + 2048])

    iso = pycdlib.PyCdlib()
    temp_dir = None
    temp_iso_path = None
    try:
        iso.open(str(iso_path))
    except pycdlib.pycdlibexception.PyCdlibInvalidISO as exc:
        if not _is_raw_2352_iso(iso_path):
            raise ValueError(
                f"El archivo especificado no es un ISO9660 válido: {iso_path}. "
                f"Comprueba que el archivo sea una imagen de CD/DVD compatible."
            ) from exc
        temp_dir = tempfile.mkdtemp(prefix="iso_raw_")
        temp_iso_path = Path(temp_dir) / "converted.iso"
        _convert_raw_2352_to_iso(iso_path, temp_iso_path)
        iso.open(str(temp_iso_path))

    def _collect_file_entries() -> List[dict]:
        entries = []

        def _walk_and_add(path_type: str, kwarg_name: str):
            try:
                for root, _, filenames in iso.walk(**{kwarg_name: '/'}):
                    for filename in filenames:
                        file_path = PurePosixPath(root) / filename
                        entries.append({'type': path_type, 'path': str(file_path)})
            except pycdlib.pycdlibexception.PyCdlibException:
                pass

        if iso.has_rock_ridge():
            _walk_and_add('rr', 'rr_path')
        if iso.has_joliet():
            _walk_and_add('joliet', 'joliet_path')
        if not entries:
            _walk_and_add('iso', 'iso_path')

        # Evita duplicados exactos cuando un mismo archivo aparece en varias tablas.
        unique = {}
        for entry in entries:
            unique[(entry['type'], entry['path'])] = entry
        return list(unique.values())

    def _find_entries(requested: str, entries: List[dict]) -> List[dict]:
        normalized = requested.replace('\\', '/').lstrip('/').lower()
        if '/' in normalized:
            return [entry for entry in entries if entry['path'].lstrip('/').lower() == normalized]
        return [entry for entry in entries if PurePosixPath(entry['path']).name.lower() == normalized]

    def _extract_entry(entry: dict) -> None:
        iso_path = entry['path']
        dest_rel_path = Path(iso_path.lstrip('/'))
        dest_path = out_path / dest_rel_path
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        if entry['type'] == 'rr':
            iso.get_file_from_iso(str(dest_path), rr_path=iso_path)
        elif entry['type'] == 'joliet':
            iso.get_file_from_iso(str(dest_path), joliet_path=iso_path)
        else:
            iso.get_file_from_iso(str(dest_path), iso_path=iso_path)

        print(f"✅ Extraído: {iso_path} → {dest_path}")

    entries = _collect_file_entries()
    for file_name in files_to_extract:
        matched = _find_entries(file_name, entries)
        if not matched:
            print(f"⚠️  Archivo no encontrado en la ISO: {file_name}")
            continue
        for entry in matched:
            _extract_entry(entry)

    try:
        iso.close()
    except Exception:
        pass
    if temp_dir is not None:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ----------------------------------------------------------------------
# Ejemplo de uso
if __name__ == "__main__":
    iso_file = "bin/CodeWarrior for PlayStation Release 4.iso"
    out_dir = "bin/CodeWarrior_R4"
    files_to_extract = ["cc_mips.dll"]

    try:
        extract_files_from_iso(iso_file, out_dir, files_to_extract)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)