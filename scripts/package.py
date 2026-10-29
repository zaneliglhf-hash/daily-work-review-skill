#!/usr/bin/env python3
"""Build a deterministic, data-free skill ZIP and SHA-256 manifest."""
import argparse
import json
from pathlib import Path
import zipfile

from install import CONTENT_DIRS, SKILL, digest, relative_file, validate_manifest


def build(root, version="0.1.0"):
    root = Path(root).absolute()
    package = root / "skills" / SKILL
    for directory in (root, root / "skills", package):
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError("Missing regular skill directory")
    files = {}
    for path in sorted(package.rglob("*")):
        name = path.relative_to(package).as_posix()
        if path.is_symlink():
            raise ValueError("Refusing to package symbolic links")
        if any(part.startswith(".") or part == "__pycache__" for part in path.relative_to(package).parts):
            continue
        if path.is_dir():
            if path.parent == package and path.name not in CONTENT_DIRS:
                raise ValueError("Unexpected directory in skill publication surface")
            continue
        relative_file(name)
        if not path.is_file():
            raise ValueError("Only regular files can be published")
        files[name] = digest(path)
    manifest = validate_manifest({"version": version, "skill": SKILL, "files": files})
    dist = root / "dist"
    if dist.is_symlink():
        raise ValueError("Distribution directory must not be a symbolic link")
    dist.mkdir(exist_ok=True)
    manifest_path = root / "manifest.json"
    archive = dist / (SKILL + ".zip")
    sums = dist / "SHA256SUMS"
    if any(path.is_symlink() for path in (manifest_path, archive, sums)):
        raise ValueError("Refusing symbolic-link output files")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as out:
        for name in files:
            info = zipfile.ZipInfo(SKILL + "/" + name, date_time=(2020, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            out.writestr(info, (package / name).read_bytes())
    sums.write_text(digest(archive) + "  " + archive.name + "\n", encoding="ascii")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--version", default="0.1.0")
    args = parser.parse_args()
    manifest = build(args.source, args.version)
    print("Packaged " + str(len(manifest["files"])) + " skill files; version " + manifest["version"])


if __name__ == "__main__":
    main()
