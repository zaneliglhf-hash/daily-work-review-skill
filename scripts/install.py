#!/usr/bin/env python3
"""Install a reviewed local checkout; no network, host discovery, or model calls."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
import uuid

SKILL = "daily-work-review"
RECEIPT = ".install-manifest.json"
CONTENT_DIRS = {"references", "assets", "agents", "scripts"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_file(value):
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError("Invalid package path")
    path = PurePosixPath(value)
    if path.is_absolute() or str(path) != value or any(p.startswith(".") for p in path.parts):
        raise ValueError("Unsafe package path")
    if value != "SKILL.md" and (len(path.parts) < 2 or path.parts[0] not in CONTENT_DIRS):
        raise ValueError("File outside the skill publication directories")
    return path


def validate_manifest(value):
    if not isinstance(value, dict) or set(value) != {"version", "skill", "files"}:
        raise ValueError("Invalid manifest fields")
    if value["skill"] != SKILL or not isinstance(value["version"], str) or not value["version"]:
        raise ValueError("Invalid manifest identity")
    files = value["files"]
    if not isinstance(files, dict) or "SKILL.md" not in files:
        raise ValueError("Manifest must include SKILL.md")
    for name, expected in files.items():
        relative_file(name)
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise ValueError("Invalid SHA-256 in manifest")
    folded = [name.casefold() for name in files]
    if len(folded) != len(set(folded)):
        raise ValueError("Case-insensitive filename collision")
    return value


def regular_file(base, name):
    path = base
    for part in relative_file(name).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("Symbolic links are not supported in skill files")
    if not path.is_file():
        raise ValueError("A required skill file is missing")
    return path


def read_manifest(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("Missing regular manifest file")
    return validate_manifest(json.loads(path.read_text(encoding="utf-8")))


def source_manifest(source):
    source = Path(source).absolute()
    package = source / "skills" / SKILL
    for path in (source, source / "skills", package):
        if path.is_symlink() or not path.is_dir():
            raise ValueError("Source must contain a regular skill directory")
    manifest = read_manifest(source / "manifest.json")
    for name, expected in manifest["files"].items():
        if digest(regular_file(package, name)) != expected:
            raise ValueError("Source SHA-256 mismatch; download a complete, consistent version")
    return package, manifest


def reject_symlinks(root):
    if root.is_symlink():
        raise ValueError("Installation directory must not be a symbolic link")
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            path = Path(directory) / name
            if path.is_symlink():
                raise ValueError("Existing installation contains a symbolic link; no changes made")


def existing_manifest(destination):
    if not destination.exists():
        return None
    if not destination.is_dir():
        raise ValueError("Destination exists and is not a directory")
    reject_symlinks(destination)
    if not (destination / RECEIPT).is_file():
        raise ValueError("Existing skill has no installer receipt; preserve it and select a different skills directory")
    old = read_manifest(destination / RECEIPT)
    for name, expected in old["files"].items():
        if digest(regular_file(destination, name)) != expected:
            raise ValueError("Existing skill has local changes; no files overwritten")
    return old


def install(source, skills_dir, check=False):
    package, manifest = source_manifest(source)
    skills_dir = Path(skills_dir).expanduser().absolute()
    destination = skills_dir / SKILL
    if skills_dir.is_symlink() or destination.is_symlink():
        raise ValueError("Target skills directory must not be a symbolic link")
    old = existing_manifest(destination)
    if check:
        if old != manifest:
            raise ValueError("Installed receipt does not match this package version")
        for name, expected in manifest["files"].items():
            if digest(regular_file(destination, name)) != expected:
                raise ValueError("Installed file checksum mismatch")
        return destination
    if old:
        for name in manifest["files"]:
            target = destination / name
            if name not in old["files"] and target.exists():
                raise ValueError("New package file conflicts with an unmanaged local file; no changes made")
            if target.exists() and not target.is_file():
                raise ValueError("Package file conflicts with a local directory; no changes made")
        for name in manifest["files"]:
            for ancestor in (destination / name).parents:
                if ancestor == destination:
                    break
                if ancestor.exists() and not ancestor.is_dir():
                    raise ValueError("Package directory conflicts with a local file; no changes made")
    skills_dir.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".daily-work-review-stage-", dir=skills_dir))
    backup = skills_dir / (".daily-work-review-backup-" + uuid.uuid4().hex)
    moved_old = False
    try:
        if old:
            shutil.copytree(destination, stage, dirs_exist_ok=True)
            for name in old["files"]:
                if name not in manifest["files"]:
                    (stage / name).unlink()
        for name in manifest["files"]:
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(regular_file(package, name), target)
        (stage / RECEIPT).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if destination.exists():
            os.replace(destination, backup)
            moved_old = True
        try:
            os.replace(stage, destination)
        except BaseException:
            if moved_old:
                os.replace(backup, destination)
                moved_old = False
            raise
        if moved_old:
            shutil.rmtree(backup)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-dir", required=True, help="Explicit native skills directory for the current executor")
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1], help="Reviewed local repository root")
    parser.add_argument("--check", action="store_true", help="Verify installed files without writing")
    args = parser.parse_args()
    try:
        destination = install(args.source, args.skills_dir, args.check)
    except (ValueError, OSError) as exc:
        print("Installation stopped: " + str(exc), file=sys.stderr)
        return 1
    print(("Verified local files: " if args.check else "Installed local files: ") + str(destination))
    print("This verifies files only, not host recognition or browser capability. Invoke the skill in the executor to verify those separately.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
